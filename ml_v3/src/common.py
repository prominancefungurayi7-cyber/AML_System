"""V3 observable schema and immutable experiment constants; no storage paths."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

DATASET_ID = 'mobile_money_aml_synthetic_100k_v3'
GENERATOR_VERSION = 'stage9.1'
SEED = 2026092209
DAY = 86_400_000_000
HOUR = DAY // 24
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
FIELDS = ['transaction_id','event_timestamp','sender_wallet','receiver_wallet',
          'amount_minor','currency','transaction_type','channel','agent_id',
          'serviced_wallet','agent_flow_direction']
FAMILIES = dict(zip(('S1','S2','S3','S4','N1','N2','N3','N4','A1','A2','A3','A4'),
    ('variable_fragment_burst','similar_amount_repetition','distributed_same_day_fragmentation',
     'variable_near_threshold_history','many_to_one_collection','one_to_many_dispersion',
     'reciprocal_relationship_cycle','wallet_pass_through','agent_wallet_growth',
     'agent_wallet_concentration','agent_temporal_burst','agent_flow_imbalance')))
HARD = {'H1':['S1','S3'],'H2':['S2'],'H3':['S4'],'H4':['N1'],
        'H5':['N2','N4'],'H6':['N3'],'H7':['A1','A3'],'H8':['A2','A4']}


def stamp(t):
    return (START+timedelta(microseconds=int(t))).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


@dataclass(frozen=True, slots=True)
class Event:
    transaction_id: int
    t: int
    sender: str
    receiver: str
    amount: int
    kind: str
    channel: str = 'direct_wallet'
    agent: str = ''
    wallet: str = ''
    direction: str = 'none'

    @property
    def key(self): return (self.t,self.transaction_id)

    @property
    def subject(self): return self.sender if self.kind=='wallet_to_wallet' else self.wallet

    def row(self):
        return dict(zip(FIELDS,(self.transaction_id,stamp(self.t),self.sender,self.receiver,
            self.amount,'USD',self.kind,self.channel,self.agent,self.wallet,self.direction)))

    @classmethod
    def from_row(cls,r):
        if set(r)!=set(FIELDS) or r['currency']!='USD':
            raise ValueError('Observable schema mismatch or leakage')
        delta=datetime.strptime(r['event_timestamp'],'%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)-START
        t=(delta.days*86400+delta.seconds)*1_000_000+delta.microseconds
        return cls(int(r['transaction_id']),t,r['sender_wallet'],r['receiver_wallet'],
                   int(r['amount_minor']),r['transaction_type'],r['channel'],r['agent_id'],
                   r['serviced_wallet'],r['agent_flow_direction'])


def validate_event(e, wallets=None, agents=None):
    if e.amount<=0 or e.kind not in ('cash_in','cash_out','wallet_to_wallet'):
        raise ValueError('Invalid amount/type')
    if not e.sender or not e.receiver: raise ValueError('Missing wallet')
    if wallets is not None and (e.sender not in wallets or e.receiver not in wallets):
        raise ValueError('Wallet outside partition')
    if e.kind=='wallet_to_wallet':
        if e.sender==e.receiver or e.direction!='none': raise ValueError('Invalid W2W')
        if e.channel=='direct_wallet':
            if e.agent or e.wallet: raise ValueError('Direct W2W has agent service')
        elif e.channel=='agent':
            if not e.agent or e.wallet not in (e.sender,e.receiver): raise ValueError('Invalid mediated service')
        else: raise ValueError('Invalid channel')
    else:
        direction='outbound' if e.kind=='cash_in' else 'inbound'
        if e.sender!=e.receiver or e.wallet!=e.sender or not e.agent or e.channel!='agent' or e.direction!=direction:
            raise ValueError('Invalid cash service')
    if agents is not None and e.agent and e.agent not in agents:
        raise ValueError('Agent outside partition')
