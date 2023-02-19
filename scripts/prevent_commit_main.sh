#!/bin/sh

current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" = "main" ]; then
    echo "Committing to main is not allowed."
    exit 1
fi
