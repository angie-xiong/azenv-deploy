#!/bin/bash
set -ex

poetry run python -m pylint ./azenv_deploy
