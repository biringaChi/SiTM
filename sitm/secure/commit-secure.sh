#!/bin/bash

blocked=0
project_root=$(cd "$(dirname "$0")/.." && pwd)

# Select detection script
if [[ "$1" == "-cred" ]]; then
    detection_script="$project_root/inference/dance_call.py"
    shift
elif [[ "$1" == "-func" ]]; then
    detection_script="$project_root/inference/vulstyle_call.py"
    shift
else
    echo "Usage: git commit-secure -cred|-func <git commit args>"
    exit 1
fi

if [[ ! -f "$detection_script" ]]; then
    echo "❌ detection script not found at $detection_script"
    exit 1
fi

files=$(git diff --cached --name-only --diff-filter=ACM)

if [[ -z "$files" ]]; then
    echo "✅ no staged files to scan."
    git commit "$@"
    exit 0
fi

for file in $files; do
    if [[ -f "$file" ]] && file "$file" | grep -q 'text'; then
        echo "🔍 scanning $file for vulnerabilities..."
        python3 "$detection_script" "$file"
        if [[ $? -ne 0 ]]; then
            echo "🚫 commit blocked for $file"
            blocked=1
        else
            echo "✅ $file passed scan."
        fi
    fi
done

if [[ $blocked -eq 1 ]]; then
    echo "❗ commit blocked due to detected issues."
    exit 1
else
    git commit "$@"
fi
