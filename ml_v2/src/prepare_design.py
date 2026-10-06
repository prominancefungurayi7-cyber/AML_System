"""Materialize the approved integer quotas before any event generation."""
from contracts import ROOT, EVENT_FIELDS, TRUTH_FIELDS, WALLET_FIELDS, AGENT_FIELDS, write_json

FAMILIES = {
 'S1': ('variable_fragment_burst', 'structuring', 4, 18, 600, 10800),
 'S2': ('similar_amount_repetition', 'structuring', 5, 24, 7200, 864000),
 'S3': ('distributed_same_day_fragmentation', 'structuring', 6, 30, 14400, 64800),
 'S4': ('variable_near_threshold_history', 'structuring', 4, 20, 172800, 1209600),
 'N1': ('many_to_one_collection', 'network', 5, 24, 1800, 432000),
 'N2': ('one_to_many_dispersion', 'network', 5, 24, 1200, 259200),
 'N3': ('reciprocal_relationship_cycle', 'network', 4, 24, 3600, 604800),
 'N4': ('wallet_pass_through', 'network', 4, 20, 300, 172800),
 'A1': ('agent_wallet_growth', 'agent', 6, 30, 86400, 604800),
 'A2': ('agent_wallet_concentration', 'agent', 6, 30, 21600, 604800),
 'A3': ('agent_temporal_burst', 'agent', 6, 30, 900, 7200),
 'A4': ('agent_flow_imbalance', 'agent', 6, 30, 21600, 604800),
}
CATEGORIES = ['cash_in', 'cash_out', 'agent_transfer', 'direct_transfer']


def apportion(total, weights):
    denom = sum(weights)
    base = [total * w // denom for w in weights]
    order = sorted(range(len(weights)), key=lambda i: (-(total * weights[i] % denom), i))
    for i in order[:total - sum(base)]:
        base[i] += 1
    return base


def build(write=True):
    allocation = {'dataset': 'epocash_aml_synthetic_100k_v2', 'version': 1, 'categories': CATEGORIES, 'partitions': {}}
    for p, total, nw, na, profiles, bands in [
        ('train',60000,1200,96,[720,300,120,60],[48,29,19]),
        ('validation',15000,300,24,[180,75,30,15],[12,7,5]),
        ('final_test',15000,300,24,[180,75,30,15],[12,7,5]),
        ('independent',10000,200,16,[120,50,20,10],[8,5,3])]:
        n = total // 100
        family = {}
        # Exact domain-category margins; distribute integer remainders across families.
        struct = [apportion(total * 15 // 1000, [1]*4), apportion(total * 15 // 1000,[1]*4), apportion(total * 5 // 1000,[1]*4)]
        # Balance column rounding while preserving n rows per family.
        for i, fid in enumerate(('S1','S2','S3','S4')):
            ci = struct[0][i]
            co = struct[1][3-i]
            at = struct[2][i]
            family[fid] = [ci, co, at, n-ci-co-at]
        ncash = apportion(total * 5 // 1000, [1,1,0,1])
        nt = [n - 2*x for x in ncash]
        naa = apportion(total * 5 // 1000, nt)
        for i, fid in enumerate(('N1','N2','N3','N4')):
            family[fid] = [ncash[i],ncash[i],naa[i],nt[i]-naa[i]]
        aci = apportion(total // 100,[1,1,1,1])
        for i, fid in enumerate(('A1','A2','A3','A4')):
            ci, co = aci[i], aci[3-i]
            family[fid] = [ci,co,n-ci-co,0]
        hard = {}
        hn = total * 55 // 1000
        for i in range(1,9):
            weights = [3,3,3,3] if i <= 3 else ([1,1,3,7] if i <=6 else [1,1,1,0])
            hard[f'H{i}'] = apportion(hn,weights)
        normal_cat = total * 22 // 100
        routine = [normal_cat-sum(v[i] for v in hard.values()) for i in range(4)]
        assert min(routine) >= 0
        positive = total * 12 // 100
        assert [sum(v[i] for v in family.values()) for i in range(4)] == [positive//4]*4
        allocation['partitions'][p] = {
            'transactions':total,'normal':total-positive,'suspicious':positive,
            'wallets':nw,'agents':na,'wallet_profiles':profiles,'agent_bands':bands,
            'family_categories':family,'hard_categories':hard,'routine_categories':routine,
            'family_strength':dict(zip(['weak','moderate','strong'],[n//5,n//2,n*3//10])),
            'positive_blocks':[positive//6]*6,
            'normal_blocks':apportion(total-positive,[1]*6)}
    schema = {'version':1,'encoding':'UTF-8','csv_null':'','timestamp_format':'%Y-%m-%dT%H:%M:%S.%fZ',
              'monetary_unit':'USD cents','amount_minor_min':100,'amount_minor_max':2500000,
              'tables':{'transactions':EVENT_FIELDS,'ground_truth':TRUTH_FIELDS,'wallets':WALLET_FIELDS,'agents':AGENT_FIELDS},
              'constraints':{'transaction_id':'uint64 globally 1..100000','event_sequence':'equals transaction_id',
              'wallet_to_wallet':'different endpoints; agent or direct_wallet; float direction none',
              'cash_in':'same customer endpoints; agent; outbound float', 'cash_out':'same customer endpoints; agent; inbound float',
              'ground_truth':'one-to-one; binary target; no metadata in events'}}
    schema['columns'] = {
        'transactions': {
            name: {'type':('uint64' if name in ('transaction_id','event_sequence') else 'int64' if name=='amount_minor' else 'utc_datetime' if name=='event_timestamp' else 'string'),
                   'nullable': name in ('agent_id','serviced_wallet')}
            for name in EVENT_FIELDS},
        'ground_truth': {
            name: {'type':'uint64' if name=='transaction_id' else 'uint8' if name=='target' else 'string',
                   'nullable':name not in ('transaction_id','target','episode_phase','label_basis')}
            for name in TRUTH_FIELDS},
        'wallets': {name:{'type':'int64' if name=='initial_balance_minor' else 'utc_datetime' if name=='activation_timestamp' else 'string','nullable':False} for name in WALLET_FIELDS},
        'agents': {name:{'type':'int64' if name=='initial_float_minor' else 'utc_datetime' if name=='activation_timestamp' else 'string','nullable':False} for name in AGENT_FIELDS}}
    schema['enums']={'currency':['USD'],'transaction_type':['cash_in','cash_out','wallet_to_wallet'],
                     'channel':['agent','direct_wallet'],'agent_flow_direction':['outbound','inbound','none'],
                     'target':[0,1],'primary_domain':['structuring','network','agent'],
                     'primary_family':[v[0] for v in FAMILIES.values()],
                     'normal_family':['routine']+[f'H{i}' for i in range(1,9)],'signal_strength':['weak','moderate','strong'],
                     'episode_phase':['early','established','late','not_applicable'],
                     'partition':['train','validation','final_test','independent']}
    scenarios = {'version':1,'horizon_start':'2025-01-01T00:00:00.000000Z','horizon_days':180,
        'seed':20260921,'synthetic_threshold_minor':1000000,
        'strength_settings':{'weak':{'coordination':0.25},'moderate':{'coordination':0.55},'strong':{'coordination':0.8}},
        'families':{k:dict(zip(['name','domain','min_events','max_events','min_seconds','max_seconds'],v)) for k,v in FAMILIES.items()},
        'hard_counterparts':{'H1':'S1/S3','H2':'S2','H3':'S4','H4':'N1','H5':'N2/N4','H6':'N3','H7':'A1/A3','H8':'A2/A4'},
        'nuisance_amounts':{'support_minor':[100,2500000],'mixture':'75% truncated lognormal; 25% uniform shared high-value component; 35% rounded', 'log_mu':9.0,'log_sigma':1.6},
        'episode_policy':'Complete episodes; integer budget packing before materialization; no truncation or model-driven selection',
        'independent_variation':{'duration_multiplier_range':[0.85,1.15],'log_amount_location_shift':0.08,'bounded_to_family_support':True},
        'initial_liquidity':{'wallet_minor':250000000,'agent_minor':5000000000,'policy':'fixed ex ante for all entities, independent of target; no replenishment'},
        'holdout_policy':'Software API guards and manifest roles; user-approved replacement of external custody. Not an OS access boundary.',
        'phase_policy':'first ceil(25%) early; last ceil(25%) late; remainder established',
        'normal_signal_strength':None}
    scenarios.update({
        'agent_service_weights':{'lower':0.5,'medium':1.0,'higher':2.0},
        'activation_policy':'90% uniform -365..-1 days; 10% uniform day 0..20; independent of target; all agents established',
        'baseline_policy':'One routine event per wallet after activation, plus ordinary background throughout the horizon; part of 100000 budget',
        'routine_time_policy':'Uniform within six 30-day blocks after wallet activation; no class-specific timestamp precision',
        'normal_episode_length':[6,24],
        'coordination_to_duration':'u ** (0.7 + coordination), scaled to family interval; shared complete support',
        'hard_negative_coordination_support':[0.1,0.8],
        'structuring_settings':{
            'S1':'Gamma(0.8,1) unequal fragment composition; episode total USD300..60000 constrained by event cap; 25% chance of one continuation 1..3 days later',
            'S2':'Shared anchor; 85% anchor-near draws; relative widths 0.015,0.04,0.07,0.20; other values from common support',
            'S3':'Clustered intra-day fragments over 4..18h; 25% chance of repeats, at least six events/day, up to five days',
            'S4':'Exactly ceil(25%)..floor(60%) near-threshold amounts per episode; common support elsewhere'},
        'network_settings':{
            'N1':'3..12 distinct contributors; real transfer edges into one rotating collector; cash entry/exit',
            'N2':'3..12 distinct recipients; real transfer edges from rotating source; cash entry/exit',
            'N3':'Complete cycles of 2..6 distinct wallets; independently varying edge amounts and intervals',
            'N4':'One incoming transfer plus optional cash funding; 50..98% total funding onward in transfers/cash-out'},
        'agent_settings':{
            'A1':'4..16 wallets ranked by lowest preceding 30-day service count plus one previously served customer where available',
            'A2':'2..6 designated wallets receive 35..85% of episode event count; other customers fill remainder',
            'A3':'2..4 irregular time clusters within 15..120 minutes; common amount support',
            'A4':'Opening three cash events contain 2/3 count dominance and independently varying 60..95% value dominance; later service events may rebalance'},
        'phase_roles':'cash phases and real transfer edges; plans may overlap ordinary events; no label changes based on observations',
        'scope_limitations':['Baseline-relative effects are not feature-calibrated; no claim every generated pattern is detectable by the existing 30 features.',
            'Wallet activity_band is metadata; routine wallet selection is uniform among active wallets.',
            'Initial wallet and agent activation policy differs: agents are established, wallets include cold starts.',
            'A4 uses an opening cash portion; it does not promise a whole-episode or whole-week dominant flow.']})
    objects={'allocation_manifest':allocation,'dataset_schema':schema,'scenario_manifest':scenarios}
    if write:
        for name,obj in objects.items():
            write_json(ROOT/'design'/f'{name}.json',obj)
    return objects


if __name__ == '__main__':
    build()
