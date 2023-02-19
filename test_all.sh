#!/bin/bash

PROJECT_DIRECTORY=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$PROJECT_DIRECTORY/src" || exit

echo "changed directory to $PROJECT_DIRECTORY/src"

mypy .
pytest .
