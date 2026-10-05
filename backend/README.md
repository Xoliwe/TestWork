# HealthLink backend

    cp .env.example .env            # set SECRET_KEY
    docker compose up --build       # from repo root (starts Postgres + API)
    docker compose exec backend python -m app.db.seed
    open http://localhost:8000/docs

Run tests (SQLite in-memory, no Docker needed):

    pip install -r requirements.txt && pytest -q

Migrations: `alembic revision --autogenerate -m "initial"` then `alembic upgrade head`
(set AUTO_CREATE_TABLES=false once you use Alembic). All seeded users share the password `Passw0rd!dev`.
