"""Exact fast path for dense chronological return paths; frozen files untouched.

Path counts use temporal dynamic programming over visited-wallet sets. A second
pass finds the exact minimum amount spread; a final pass selects its shortest,
lexicographically first route. Integer cross-products preserve Fraction ordering.
Equal-amount paths certify the spread lower bound of 1 and need only one pass.
"""
import ast
from collections import defaultdict
from fractions import Fraction

_compiled = {}


def certified_summary(state, current, day):
    if current.transaction_type != 'wallet_to_wallet':
        return (0, None, None)
    root, goal = current.receiver_wallet, current.sender_wallet
    edges = sorted((edge for rows in state.outgoing.values() for edge in rows
                    if current.time - 7 * day < edge.time and edge.key < current.key),
                   key=lambda edge: edge.key)
    wallets = {root, goal} | {e.sender_wallet for e in edges} | {e.receiver_wallet for e in edges}
    bits = {wallet: 1 << index for index, wallet in enumerate(sorted(wallets))}
    root_mask = bits[root]
    counts = defaultdict(dict)
    counts[root][root_mask] = 1
    equal = {}
    total, shortest, best = 0, None, None
    for edge in edges:
        source, destination = edge.sender_wallet, edge.receiver_wallet
        bit = bits[destination]
        # Source != destination; updates cannot modify this source dictionary.
        for mask, count in counts[source].items():
            length = mask.bit_count()
            if mask & bit or length > 5:
                continue
            if source == root and mask == root_mask:
                path = (edge.key,)
            else:
                prefix = equal.get((source, mask, edge.amount_minor))
                path = prefix + (edge.key,) if prefix is not None else None
            if destination == goal:
                total += count
                shortest = min(shortest or length, length)
                if path is not None:
                    candidate = (length, path, edge.amount_minor)
                    if best is None or candidate < best:
                        best = candidate
            elif length < 5:
                next_mask = mask | bit
                counts[destination][next_mask] = counts[destination].get(next_mask, 0) + count
                if path is not None:
                    key = (destination, next_mask, edge.amount_minor)
                    if key not in equal or path < equal[key]:
                        equal[key] = path
    if not total:
        return 0, None, None
    if best is None:
        return total, shortest, _ranked_path(edges, root, goal, bits)
    length, keys, amount = best
    return total, shortest, ((Fraction(1), length, keys), amount)


def _ranked_path(edges, root, goal, bits):
    """Exact minimax spread, then length/key tie-breaks in a separate pass.

    Keeping only the best lexicographic path during minimax would be incorrect:
    a later edge can make two different earlier spreads tie. The second pass
    fixes the winning spread first and therefore preserves the frozen ranking.
    """
    root_mask = bits[root]
    states = defaultdict(dict)
    optimum, length = None, None
    def less(a, b):
        return a[0] * b[1] < b[0] * a[1]
    for edge in edges:
        u, v, amount = edge.sender_wallet, edge.receiver_wallet, edge.amount_minor
        prefixes = [(root_mask, {amount: (1, 1)})] if u == root else states[u].items()
        for mask, amounts in prefixes:
            hops = mask.bit_count()
            if mask & bits[v] or hops > 5:
                continue
            best = None
            for prior_amount, spread in amounts.items():
                ratio = (max(amount, prior_amount), min(amount, prior_amount))
                candidate = ratio if less(spread, ratio) else spread
                if optimum is not None and less(optimum, candidate):
                    continue
                if best is None or less(candidate, best):
                    best = candidate
                    if best[0] == best[1]:
                        break
            if best is None:
                continue
            if v == goal:
                if optimum is None or less(best, optimum):
                    optimum, length = best, hops
                elif not less(optimum, best):
                    length = min(length, hops)
            elif hops < 5:
                target = states[v].setdefault(mask | bits[v], {})
                if amount not in target or less(best, target[amount]):
                    target[amount] = best
    if optimum is None:
        raise ValueError('Counted return paths have no valid ranking')
    states = defaultdict(dict)
    chosen = None
    for edge in edges:
        u, v, amount = edge.sender_wallet, edge.receiver_wallet, edge.amount_minor
        prefixes = [(root_mask, {amount: ()})] if u == root else states[u].items()
        for mask, amounts in prefixes:
            hops = mask.bit_count()
            if mask & bits[v] or hops > length:
                continue
            best = None
            for prior_amount, path in amounts.items():
                ratio = (max(amount, prior_amount), min(amount, prior_amount))
                if not less(optimum, ratio) and (best is None or path < best):
                    best = path
            if best is None:
                continue
            path = best + (edge.key,)
            if v == goal:
                if hops == length and (chosen is None or path < chosen):
                    chosen = path
            elif hops < length:
                target = states[v].setdefault(mask | bits[v], {})
                if amount not in target or path < target[amount]:
                    target[amount] = path
    if chosen is None:
        raise ValueError('Minimum-spread return route unavailable')
    first_amount = next(edge.amount_minor for edge in edges if edge.key == chosen[0])
    return ((Fraction(*optimum), length, chosen), first_amount)


def _step_with_summary(model):
    from ml_v4.frozen_inference.service import authority, verified_bytes, Failure
    record = authority()['artifacts']['extractor_source']
    # Read hash-verified bytes, including on cache hits. No frozen file is edited.
    source = verified_bytes(record)
    key = record['sha256']
    if key in _compiled:
        return _compiled[key]
    tree = ast.parse(source)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Extractor')
    step = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'step')
    matches = [index for index, node in enumerate(step.body)
               if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == 'is_w2w'
               and node.body and isinstance(node.body[0], ast.FunctionDef) and node.body[0].name == 'visit']
    if len(matches) != 1:
        raise Failure('MODEL_INTEGRITY')
    step.args.args.append(ast.arg(arg='summary'))
    step.body[matches[0]] = ast.parse('count, minlen, selected = summary').body[0]
    namespace = dict(vars(model.extractor))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[step], type_ignores=[])),
                 '<verified-v4-exact-network-summary>', 'exec'), namespace)
    _compiled.clear()
    _compiled[key] = namespace['step']
    return _compiled[key]


def exact_step(model, state, current):
    summary = certified_summary(state, current, model.contract.DAY)
    if summary is None:
        return state.step(current)
    return _step_with_summary(model)(state, current, summary)
