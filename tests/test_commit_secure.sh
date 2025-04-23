#!/bin/bash

echo "test 1: no arguments"
output=$(bash ./sitm_core/secure/commit-secure.sh 2>&1)
exit_code=$?
if [[ $exit_code -ne 0 && "$output" == *"Usage: git commit-secure -cred|-func"* ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi

echo "test 2: missing detection script"
mv ./sitm_core/inference/dance_call.py ./sitm_core/inference/dance_call.py.bak
output=$(bash ./sitm_core/secure/commit-secure.sh -cred -m "test" 2>&1)
exit_code=$?
mv ./sitm_core/inference/dance_call.py.bak ./sitm_core/inference/dance_call.py
if [[ $exit_code -ne 0 && "$output" == *"detection script not found"* ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi

echo "test 3: vulnerable file blocked"
echo 'password = "1234"' > test_commit_vul.txt
git add test_commit_vul.txt
output=$(bash ./sitm_core/secure/commit-secure.sh -cred -m "test commit" 2>&1)
exit_code=$?
git reset HEAD test_commit_vul.txt
rm test_commit_vul.txt
if [[ "$output" == *"commit blocked for"* && $exit_code -eq 1 ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi
