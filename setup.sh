#!/bin/bash

PROJECT_DIRECTORY=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "Project directory detected as: $PROJECT_DIRECTORY"

cd "$PROJECT_DIRECTORY" || exit

python3.11 -m venv kq_env
source kq_env/bin/activate

pip install -r requirements/requirements.txt

ALIAS_CMD="alias kq_env='cd $PROJECT_DIRECTORY && source kq_env/bin/activate'"

if [[ -z $ZSH_VERSION ]]; then
  echo "Detected zsh, updating .zshrc"
  SRC_FILE="$HOME/.zshrc"
else
  echo "Defaulting to bash, updating .bash_profile"
  SRC_FILE="$HOME/.bash_profile"
fi

echo "$ALIAS_CMD" >> "$SRC_FILE"
echo "export PYTHONPATH=\"$PROJECT_DIRECTORY:\$PYTHONPATH\"" >> "$SRC_FILE"

echo "Setup complete, run 'source $SRC_FILE' use 'kq_env' to enter the dev environment in the future!"
echo "If your shell does not source $SRC_FILE, copy the command to the relevant file."
