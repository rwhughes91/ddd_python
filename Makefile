ENTRYPOINTS=ddd_python tests

test:
	coverage run -m pytest --rootdir tests

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
	alembic upgrade

downgrade:
	alembic downgrade

head:
	alembic current