.DEFAULT_GOAL := all

.PHONY: install
install:
	pip install -U setuptools pip
	pip install -U -r test_requirements.txt
	pip install -e .

.PHONY: lint
lint:
	#python setup.py check -rms
	flake8 --ignore=E501,E126,E121,E125,W503 email_validator tests

.PHONY: test
test:
	pytest --cov=email_validator

.PHONY: testcov
testcov: test
	@echo "building coverage html"
	@coverage html

.PHONY: all
all: testcov lint

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	python setup.py clean
