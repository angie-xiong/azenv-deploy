#!/bin/sh

# Test if python comand is available
if type -a python3 >&2; then
  echo "Creating virtual environment for the project..."
  python3 -m venv .venv/
else
  echo "Please make sure python is installed."
fi

echo "Install dependencies...."
if type -a poetry >&2; then
  echo "poetry is ready."
else
  pip install poetry=="2.1.1"
fi
