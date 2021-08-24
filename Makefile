ENTRYPOINTS=ddd_python tests

test:
	coverage run -m pytest --rootdir tests

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
