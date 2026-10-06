"""Fail-closed preproduction custody boundary, with non-secret test primitives."""
import hashlib
import hmac

DATASET = 'mobile_money_v4_independent_challenge_1'
ARMS = ('reference_challenge','shifted_challenge')
STREAMS = ('entities','profiles','catchments','history','routine','episodes',
           'amounts','timestamps','transaction_ids','bootstrap','permutation')


def derived_seed(secret, arm, unit, stream):
    if type(secret) is not bytes or len(secret)!=32:
        raise ValueError('Custodian key must be exactly 256 bits')
    if arm not in ARMS or type(unit) is not int or not 0<=unit<12 or stream not in STREAMS:
        raise ValueError('Invalid stream address')
    message=f'{DATASET}|{arm}|{unit}|{stream}'.encode('utf-8')
    return int.from_bytes(hmac.new(secret,message,hashlib.sha256).digest()[:16],'little')


def require_production_custody(*args, **kwargs):
    # An environment flag or self-asserted JSON certificate is not independent custody.
    raise PermissionError('BLOCKED: no independently administered execution/registry/logging backend is provisioned')


class FixtureDrawLifecycle:
    """In-memory state-machine fixture ONLY, not a durable production lock.

    A real custodian must implement this transition policy atomically in its own
    immutable execution register. This class cannot authorize generation.
    """
    def __init__(self): self.state='NEW'
    def commit(self):
        if self.state!='NEW': raise PermissionError('No second commitment')
        self.state='COMMITTED'
    def begin(self):
        if self.state!='COMMITTED': raise PermissionError('No draw or replacement permitted')
        self.state='CONSUMED'
    def finish(self, success):
        if self.state!='CONSUMED': raise PermissionError('Draw not running')
        self.state='RETAINED' if success else 'FAILED_RETAINED'
