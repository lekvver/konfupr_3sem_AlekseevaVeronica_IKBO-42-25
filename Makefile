PYTHON ?= python3
export PYTHONPATH := src

.PHONY: run test test-unit test-scripts clean

run:
	$(PYTHON) -m shell_emulator

test: test-unit test-scripts

test-unit:
	$(PYTHON) -m unittest discover -s tests -v

test-scripts:
	@for script in tests/scripts/stage*.sh; do \
		bash "$$script" || exit 1; \
	done

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
