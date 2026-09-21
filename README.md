# EpoCash AML Decision-Support System

EpoCash-style mobile-money AML decision-support prototype for detecting suspicious transaction patterns.

## Project Overview

This is a research prototype using synthetic data to detect three AML dimensions:
- **Structuring** — Repeated transactions, bursts, fragmented amounts
- **Wallet/Transaction-Network Behaviour** — Many-to-one flows, one-to-many flows, pass-through patterns
- **Agent Behaviour** — Wallet concentration around agents, agent transaction bursts

## AI Pipeline

The system uses a validated two-stage AI architecture:

```
Transaction
    ↓
Stage 13 — 30 Frozen Features
    ↓
Stage 14 — Gradient Boosting Model
    ↓
Suspicious Probability
    ↓
Threshold 0.35
    ↓
Normal / Suspicious Pattern
    ↓
AML Alert
    ↓
Investigation / Dashboard
```

## Technology Stack

- **Backend:** Flask with Flask-SocketIO
- **Database:** MySQL 8.0
- **AI Model:** Stage 14 frozen Gradient Boosting model
- **Dataset:** 100,000 synthetic EpoCash-style transactions
- **Real-time:** Socket.IO with threading async mode

## Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create MySQL database and user:
   ```sql
   CREATE DATABASE aml;
   CREATE USER 'aml'@'localhost' IDENTIFIED BY 'aml123';
   GRANT ALL PRIVILEGES ON aml.* TO 'aml'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. Configure `.env`:
   ```
   DATABASE_URL=mysql://aml:aml123@127.0.0.1:3306/aml
   SECRET_KEY=your-secret-key
   ```

4. Start the application:
   ```bash
   python server.py
   ```

5. Open http://127.0.0.1:5000

The first app start creates the MySQL tables and seeds staff accounts:
- Admin / Admin123
- Compliance / Compliance123

## Transaction Simulation

The system includes a transaction simulator that exercises the real application pipeline:
- EpoCash transaction types (Cash-In, Cash-Out, Wallet-to-Wallet Transfer)
- Agent-mediated transactions
- Structuring, network, and agent scenario generation
- All simulated transactions pass through Stage 13 + Stage 14

## Important Limitation

**This is a research prototype using synthetic data.** It does not establish production AML effectiveness and does not prove that a transaction represents money laundering. The system is for academic research and demonstration purposes only.

## Production Notes

- Set a strong `SECRET_KEY` in production
- Use MySQL 8+ with a dedicated database user
- Run with Gunicorn in a container or cloud host
- Keep `.env` values out of source control

## Docker

```bash
docker build -t aml-system .
docker run -p 5000:5000 aml-system
```

## Documentation

- `reports/README.md` — Report organization guide
- `reports/stage17e_transaction_simulation_alignment_2026-09-15.md` — Final simulation alignment report
- `docs/archive/` — Historical development reports and evidence
