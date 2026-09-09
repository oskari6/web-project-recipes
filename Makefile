# utility commands
# sqlite3 database.db
LOAD_ENV = set -a; . ./.env; set +a;
.PHONY: db

# start dev env
dev:
	$(LOAD_ENV) .venv/bin/flask run --debug
# start "production" env (dev env without debug)
start:
	$(LOAD_ENV) .venv/bin/flask --app app run
# get tables and columns / relations of database 
get-schema:
	sqlite3 database.db < schema.sql
# setup developemnt enviroment
setup:
	bash  setup.sh
# create seed data (mass)
seed:
	.venv/bin/python -m db.seed
# open db
db:
	sqlite3 database.db
# run lint (install locally pylint first)
lint:
	.venv/bin/pylint app.py routes services utils db > pylint-report.md || true
# delete database tables and data
reset-db:
	python3 -m db.reset_db