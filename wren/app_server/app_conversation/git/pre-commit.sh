#!/bin/bash
# This hook was installed by Wren
# It calls the pre-commit script in the .wren directory

if [ -x ".wren/pre-commit.sh" ]; then
    source ".wren/pre-commit.sh"
    exit $?
else
    echo "Warning: .wren/pre-commit.sh not found or not executable"
    exit 0
fi
