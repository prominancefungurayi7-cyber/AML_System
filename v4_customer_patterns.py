"""Signed historical baselines for prospective simulation, never model labels."""
from collections import Counter
from decimal import Decimal
from statistics import median
import random


def profiles(conn, wallets):
    result = {}
    accounts = {w['account_number'] for w in wallets}
    for wallet in wallets:
        rows = conn.execute(
            "SELECT amount,receiver_account,timestamp FROM transactions "
            "WHERE sender_account=? AND transaction_type='transfer' AND amount>0 "
            "AND status='Completed' AND risk_level IN ('normal','low') "
            "ORDER BY id DESC LIMIT 100", (wallet['account_number'],)).fetchall()
        amounts = sorted(int(Decimal(str(r['amount'])) * 100) for r in rows)
        peers = Counter(r['receiver_account'] for r in rows
                        if r['receiver_account'] in accounts and r['receiver_account'] != wallet['account_number'])
        result[wallet['account_number']] = dict(
            sample_count=len(rows), sufficient_history=len(rows) >= 5,
            median_minor=int(median(amounts)) if amounts else 1000,
            lower_minor=amounts[len(amounts)//4] if amounts else 500,
            upper_minor=amounts[min(len(amounts)-1, len(amounts)*3//4)] if amounts else 1500,
            counterparties=[account for account, _ in peers.most_common(5)],
            balance_minor=int(Decimal(str(wallet['balance'])) * 100),
            latest_timestamp=str(rows[0]['timestamp']) if rows else None)
    return result


def plan_from_history(ticket, legacy_plan, schedule):
    # Old signed tickets retain their original payment identities and amounts.
    rows = legacy_plan({**ticket, 'version': 2})
    wallets = ticket['wallets']
    by_account = {w['account_number']: w for w in wallets}
    baseline = ticket['customer_profiles']
    balances = {a: p['balance_minor'] for a, p in baseline.items()}
    rng = random.Random(ticket['batch_id'] + ':history')
    routine_index = 0
    next_wallet = 0
    output = []
    for family, (sender, recipient, form, key) in zip(schedule(ticket), rows):
        form = dict(form)
        if family == 'ordinary':
            if ticket['version'] >= 4:
                # Try every customer in rotation. An unfunded customer remains
                # eligible to receive and can send after an incoming payment.
                # The signed balance snapshot determines this plan; retries
                # never consult changed live balances or invent a deposit.
                for offset in range(len(wallets)):
                    position = (next_wallet + offset) % len(wallets)
                    candidate = wallets[position]
                    candidate_profile = baseline[candidate['account_number']]
                    needed = max(1, candidate_profile['lower_minor'])
                    if balances[candidate['account_number']] >= needed:
                        sender = candidate
                        next_wallet = (position + 1) % len(wallets)
                        break
                else:
                    raise ValueError('Insufficient balance for the historical scenario. Choose a smaller batch.')
            else:
                # Preserve already issued version-3 payment identities.
                sender = wallets[routine_index % len(wallets)]
            profile = baseline[sender['account_number']]
            peers = [by_account[a] for a in profile['counterparties'] if a in by_account]
            fallback_position = (wallets.index(sender) if ticket['version'] >= 4 else
                                 routine_index % len(wallets))
            recipient = (peers[routine_index % len(peers)] if peers else
                         wallets[(fallback_position + 1) % len(wallets)])
            routine_index += 1
            low, high = profile['lower_minor'], profile['upper_minor']
            if ticket['version'] >= 4:
                high = min(high, balances[sender['account_number']])
            amount = rng.randint(max(1, low), max(1, high))
            form['recipient'] = recipient['account_number']
        else:
            amount = int(Decimal(form['amount']) * 100)
        account = sender['account_number']
        if form['type'] != 'cash_in':
            # Never invent funding. Refuse the complete plan before payment writes.
            if balances[account] < amount:
                raise ValueError('Insufficient balance for the historical scenario in wallet ' + account + '. Choose a smaller batch.')
            balances[account] -= amount
            if form['type'] == 'wallet_to_wallet':
                balances[recipient['account_number']] += amount
        else:
            balances[account] += amount
        form['amount'] = f'{Decimal(amount) / 100:.2f}'
        output.append((sender, recipient, form, key))
    return output
