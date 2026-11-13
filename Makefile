PYTHON ?= python3
export PYTHONPATH := src

.PHONY: run test test-unit test-scripts lint clean

run:
	$(PYTHON) -m depgraph $(ARGS)

test: test-unit test-scripts

test-unit:
	$(PYTHON) -m unittest discover -s tests -v

test-scripts:
	@for script in tests/scripts/stage*.sh; do \
		bash "$$script" || exit 1; \
	done

lint:
	$(PYTHON) -m flake8 --max-line-length=80 --max-complexity=10 src tests

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
