#!/bin/bash
set -ex

poetry check --lock
# poetry run pyright
poetry run python -m pylint ./azenv_deploy
poetry run python -m pylint ./projects/dev/*.py
poetry run python -m coverage run -m pytest
poetry run python -m coverage report -m
poetry run python -m coverage xml
