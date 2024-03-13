#!/bin/bash

PROJECT_DIRECTORY=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "Project directory detected as: $PROJECT_DIRECTORY"

cd "$PROJECT_DIRECTORY" || exit

python3.11 -m venv kq_env
source kq_env/bin/activate

pip install -r requirements/requirements.txt

ALIAS_CMD="alias kq_env='cd $PROJECT_DIRECTORY && source kq_env/bin/activate'"
echo "$ALIAS_CMD" >> ~/.bash_profile
echo "export PYTHONPATH=\"$PROJECT_DIRECTORY:\$PYTHONPATH\"" >> ~/.bash_profile

echo 'Setup complete, run `source ~/.bash_profile` use `kq_env` to enter the dev environment in the future!'
echo 'If your shell does not source .bash_profile, copy the command to the relevant file.'
