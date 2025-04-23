#!/bin/bash

echo "test 1: no mode argument"
output=$(bash ./sitm_core/secure/push-secure.sh 2>&1)
exit_code=$?
if [[ $exit_code -ne 0 && "$output" == *"Usage: git push-secure -cred|-func"* ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi

echo "test 2: missing detection script"
mv ./sitm_core/inference/dance_call.py ./sitm_core/inference/dance_call.py.bak
output=$(bash ./sitm_core/secure/push-secure.sh -cred 2>&1)
exit_code=$?
mv ./sitm_core/inference/dance_call.py.bak ./sitm_core/inference/dance_call.py
if [[ $exit_code -ne 0 && "$output" == *"detection script not found"* ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi

echo "test 3: vulnerable file blocked from push"
echo 'password = "abc"' > test_push_vul.txt
git add test_push_vul.txt
git commit -m "test vulnerable push" > /dev/null
output=$(bash ./sitm_core/secure/push-secure.sh -cred 2>&1)
exit_code=$?
git reset --soft HEAD~1
rm test_push_vul.txt
if [[ "$output" == *"push blocked for"* && $exit_code -eq 1 ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi
