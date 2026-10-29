PYTHON ?= python3
export PYTHONPATH := src

.PHONY: run test clean

run:
	$(PYTHON) -m shell_emulator

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
