#!/bin/bash

blocked=0
project_root=$(cd "$(dirname "$0")/.." && pwd)

if [[ "$1" == "-cred" ]]; then
    detection_script="$project_root/inference/dance_call.py"
    shift
elif [[ "$1" == "-func" ]]; then
    detection_script="$project_root/inference/vulstyle_call.py"
    shift
else
    echo "Usage: git add-secure -cred|-func [files or patterns]"
    exit 1
fi

if [[ ! -f "$detection_script" ]]; then
    echo "detection script not found at $detection_script"
    exit 1
fi

shopt -s nullglob
input_args=("$@")

if [[ ${#input_args[@]} -eq 0 ]]; then
    echo "no files to scan."
    exit 0
fi

files=()
for arg in "${input_args[@]}"; do
    if [[ "$arg" == "-A" ]]; then
        files+=($(git ls-files --modified --others --exclude-standard))
    elif [[ "$arg" == "-u" ]]; then
        files+=($(git ls-files --modified --deleted))
    elif [[ "$arg" == "." ]]; then
        files+=($(git ls-files --modified --others --exclude-standard .))
    else
        files+=($arg)
    fi
done

if [[ ${#files[@]} -eq 0 ]]; then
    echo "✅ no matching files found."
    exit 0
fi

for file in "${files[@]}"; do
    if [[ -f "$file" ]] && file "$file" | grep -q 'text'; then
        echo "🔍 scanning $file for vulnerabilities..."
        python3 "$detection_script" "$file"
        if [[ $? -ne 0 ]]; then
            echo "skipping staging for $file"
            blocked=1
        else
            echo "✅ $file passed scan."
            git add "$file"
        fi
    else
        git add "$file"
    fi
done

if [[ $blocked -eq 1 ]]; then
    echo "one or more files were blocked due to detected issues."
    exit 1
fi
