# Real-Time AML System

A Flask-based AML monitoring prototype with authentication, transactions, risk scoring, alerts, compliance dashboards, and live event streaming.

## Run locally

1. Install dependencies:
   `pip install -r requirements.txt`
2. Start the app:
   `python app.py`
3. Open http://127.0.0.1:5000

## Production notes

- Set a strong `SECRET_KEY`.
- Use a real database such as PostgreSQL in production.
- Run the app with Gunicorn in a container or a cloud host.
- Keep the `.env` values out of source control.

## Docker

```bash
docker build -t aml-system .
docker run -p 5000:5000 aml-system
```
