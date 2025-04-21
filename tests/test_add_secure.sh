#!/bin/bash

echo "test 1: no arguments"
output=$(bash ./sitm/secure/add-secure.sh -cred 2>&1)
exit_code=$?
if [[ $exit_code -eq 0 && "$output" == *"no files to scan."* ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi

echo "test 2: invalid mode"
output=$(bash ./sitm/secure/add-secure.sh -invalid 2>&1)
exit_code=$?
if [[ $exit_code -ne 0 && "$output" == *"Usage: git add-secure -cred|-func"* ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi

echo "test 3: missing detection script"
mv ./sitm/inference/dance_call.py ./sitm/inference/dance_call.py.bak
output=$(bash ./sitm/secure/add-secure.sh -cred test.txt 2>&1)
exit_code=$?
mv ./sitm/inference/dance_call.py.bak ./sitm/inference/dance_call.py
if [[ $exit_code -ne 0 && "$output" == *"detection script not found"* ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi

echo "test 4: vulnerable file blocked"
echo 'password = "secret"' > vul_test.txt
git add vul_test.txt
output=$(bash ./sitm/secure/add-secure.sh -cred vul_test.txt 2>&1)
exit_code=$?
if [[ "$output" == *"skipping staging for"* && $exit_code -eq 1 ]]; then
    echo "✅ passed"
else
    echo "❌ failed"
fi
git reset HEAD vul_test.txt
rm vul_test.txt
