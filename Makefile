# utility commands
LOAD_ENV = set -a; . ./.env; set +a;

dev:
	$(LOAD_ENV) .venv/bin/flask run --debug
start:
	$(LOAD_ENV) .venv/bin/flask --app app run
get-schema:
	sqlite3 database.db < schema.sql
setup:
	bash  setup.sh
seed:
	.venv/bin/python db/seed.py
reset-db:
	python3 -m db.reset_db