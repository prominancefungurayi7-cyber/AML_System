"""Exact target-only replay using the unchanged, hash-verified V4 extractor.

Earlier feature rows do not feed later rows: only observable events update the
extractor's history. Rebuild that state once, then run the frozen step for the
requested event. Never filter the graph, truncate history or change features.
"""


def replay_target(model, events, transaction_id):
    import numpy as np
    from ml_v4.frozen_inference.service import Failure, validate_features

    state = model.extractor.Extractor()
    seen, last, current = set(), None, None
    validated = []
    try:
        # Validate the whole snapshot, including events after the requested one.
        for raw in events:
            if set(raw) != set(model.contract.FIELDS):
                raise Failure('INVALID_EVENT')
            event = model.contract.Event(**raw)
            model.contract.validate_event(event)
            if event.transaction_id in seen or (last is not None and event.key <= last):
                raise Failure('HISTORY_INCOMPLETE')
            seen.add(event.transaction_id)
            last = event.key
            validated.append(event)
            if event.transaction_id == transaction_id:
                current = event
        if current is None:
            raise Failure('EVENT_UNAVAILABLE')
        for event in validated:
            if event.key >= current.key:
                break
            state.activity[event.subject].append(event)
            for wallet in {event.sender_wallet, event.receiver_wallet}:
                state.first_wallet.setdefault(wallet, event.time)
            if event.transaction_type == 'wallet_to_wallet':
                state.incoming[event.receiver_wallet].append(event)
                state.outgoing[event.sender_wallet].append(event)
            if event.agent_id:
                state.services[event.agent_id].append(event)
                state.first_agent.setdefault(event.agent_id, event.time)
            state.ids.add(event.transaction_id)
            state.last = event.key
        # The frozen step applies its own windows and eligibility gates.
        from v4_graph_acceleration import exact_step
        row = exact_step(model, state, current)
        features = np.array([tuple(row)], dtype=[
            (name, 'U16' if name == 'transaction_type' else 'f8') for name in model.names])
        validate_features(features, model.names, model.markers)
        return features, current
    except Failure:
        raise
    except MemoryError:
        raise Failure('HISTORY_RESOURCE_EXHAUSTED') from None
    except Exception:
        raise Failure('FEATURE_INVALID') from None


def infer(connection_factory, transaction_id, source_validator=None):
    """Read-only inference with the original history gate and frozen predictor."""
    from ml_v4.frozen_inference.service import (
        Failure, FrozenModel, probability_decision, result, utc)
    from ml_v4.frozen_inference.history import verified_snapshot

    output = result(transaction_id)
    connection = None
    try:
        if type(transaction_id) is not int or not 0 < transaction_id < 2**63:
            raise Failure('INVALID_EVENT')
        connection = connection_factory()
        events, context = verified_snapshot(connection, transaction_id)
        if source_validator is not None:
            source_validator(connection)
        output.update(context)
        model = FrozenModel()
        features, event = replay_target(model, events, transaction_id)
        output['event_timestamp'] = event.event_timestamp
        probability = model.predict(features)
        prediction, decision = probability_decision(probability)
        output.update(status='success', prediction=prediction,
                      suspicious_probability=probability, decision=decision,
                      human_review_required=bool(prediction))
    except Failure as exc:
        output['error_code'] = exc.code
    except MemoryError:
        output['error_code'] = 'HISTORY_RESOURCE_EXHAUSTED'
    except Exception:
        output['error_code'] = 'INFERENCE_ERROR'
    finally:
        if connection is not None:
            try:
                try:
                    connection.rollback()
                finally:
                    connection.close()
            except Exception:
                output.update(status='inference_error', prediction=None,
                              suspicious_probability=None, decision='inference_error',
                              error_code='HISTORY_UNAVAILABLE', human_review_required=False)
        output['inference_timestamp'] = utc()
    return output
