ENTRYPOINTS=ddd_python tests

test:
	coverage run -m pytest -s --rootdir tests

report:
	coverage report

tox:
	tox

lint:
	flake8 $(ENTRYPOINTS)
	mypy $(ENTRYPOINTS)

check:
	black --check $(ENTRYPOINTS)
	isort --check $(ENTRYPOINTS)

format:
	black $(ENTRYPOINTS)
	isort $(ENTRYPOINTS)

up:
	docker-compose build
	docker-compose up -d --force-recreate

down:
	docker-compose down --remove-orphans

downup: down up

migrate:
	alembic revision --autogenerate

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade

head:
	alembic current

run_flask:
	gunicorn --enable-stdio-inheritance --log-level debug --bind 0.0.0.0:5443 --workers=2 --threads=4 --worker-class=gthread ddd_python.entrypoints.flask_app:app