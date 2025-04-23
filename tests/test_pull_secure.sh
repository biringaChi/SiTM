#!/bin/bash

echo "test 1: no changes to pull"
output=$(bash ./sitm_core/secure/pull-secure.sh -cred origin master 2>&1)
exit_code=$?
if [[ $exit_code -eq 0 && "$output" == *"no incoming changes to pull."* ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi
