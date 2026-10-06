"""Hand-checkable Stage 6 causal semantics."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from stage6_candidate_features import extract_rows


def event(i, minute, kind='wallet_to_wallet', sender='a', receiver='b', agent='', wallet='', amount=100):
    return {'transaction_id': str(i), 'event_timestamp': f'2025-01-01T00:{minute:02d}:00.000000Z',
            'transaction_type': kind, 'sender_wallet': sender, 'receiver_wallet': receiver,
            'agent_id': agent, 'serviced_wallet': wallet, 'amount_minor': str(amount*100)}


class Stage6Semantics(unittest.TestCase):
    def test_reciprocal_and_receiver_prior_only(self):
        rows, ids = extract_rows([event(1, 0, sender='a', receiver='b'),
                                  event(2, 1, sender='b', receiver='a'),
                                  event(3, 2, sender='a', receiver='b'),
                                  event(4, 3, sender='c', receiver='b')])
        self.assertEqual(ids, [1,2,3,4])
        self.assertEqual(rows[0][:4], [0,0,0,0])
        self.assertEqual(rows[1][2:4], [0,0])
        self.assertEqual(rows[2][:4], [1,.5,1,1])
        self.assertEqual(rows[3][2:4], [1,2])

    def test_agent_growth_concentration_and_cash_orientation(self):
        rows,_ = extract_rows([event(1,0,'cash_in',agent='g',wallet='w1',amount=100),
                               event(2,1,'cash_out',agent='g',wallet='w1',amount=50),
                               event(3,2,'cash_in',agent='g',wallet='w2',amount=50),
                               event(4,3,'wallet_to_wallet',agent='g',wallet='w3',amount=200),
                               event(5,4,'cash_out',agent='g',wallet='w3',amount=100)])
        self.assertEqual(rows[0][4:], [0,0,0,0])
        self.assertEqual(rows[2][4:], [1,1,-1/3,0])
        self.assertEqual(rows[3][4:6], [1,2/3])
        self.assertEqual(rows[4][4:6], [1,.5])
        self.assertEqual(rows[4][6], -.5)
        self.assertEqual(rows[4][7], -1/3)

    def test_same_timestamp_id_order_and_direct_transfer(self):
        a=event(2,0,sender='x',receiver='y')
        b=event(1,0,sender='z',receiver='y')
        c=event(3,1,sender='y',receiver='z')
        rows,ids=extract_rows([c,a,b])
        self.assertEqual(ids,[1,2,3])
        self.assertEqual(rows[1][2:4],[1,1])
        self.assertEqual(rows[2][0],0)

if __name__ == '__main__': unittest.main()
