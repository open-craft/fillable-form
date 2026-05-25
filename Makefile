.PHONY: build install test clean

build:
	cd fillable_form/frontend && npm run build

install:
	pip install -e .

test:
	python -m pytest fillable_form/tests/ -v

test-frontend:
	cd fillable_form/frontend && npm test

clean:
	rm -rf fillable_form/static/css/*.css fillable_form/static/js/*.js
	rm -rf fillable_form/frontend/dist fillable_form/frontend/node_modules
	rm -rf *.egg-info build dist
