.PHONY: build install requirements test test-python test-frontend clean

build:
	cd fillable_form/frontend && npm run build

install:
	pip install -e .

requirements: ## install Python and frontend test dependencies
	pip install -e '.[test]'
	cd fillable_form/frontend && npm ci

test: test-python test-frontend ## run all tests

test-python: ## run the Python tests
	python -m pytest -v

test-frontend: ## run the frontend (Jest) tests
	cd fillable_form/frontend && npm test

clean:
	rm -rf fillable_form/static/css/*.css fillable_form/static/js/*.js
	rm -rf fillable_form/frontend/dist fillable_form/frontend/node_modules
	rm -rf *.egg-info build dist
