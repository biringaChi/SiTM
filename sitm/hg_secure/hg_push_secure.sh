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
    echo "usage: hg push-sec -cred|-func [push flags or remote]"
    exit 1
fi

if [[ ! -f "$detection_script" ]]; then
    echo "detection script not found at $detection_script"
    exit 1
fi

push_args=()
while [[ $# -gt 0 ]]; do
    push_args+=("$1")
    shift
done

files=$(hg status --change . | awk '{print $2}')

if [[ -z "$files" ]]; then
    echo "no committed files to scan."
    hg push "${push_args[@]}"
    exit 0
fi

for file in $files; do
    if [[ -f "$file" ]] && file "$file" | grep -q 'text'; then
        echo "scanning $file for vulnerabilities..."
        python3 "$detection_script" "$file"
        if [[ $? -ne 0 ]]; then
            echo "push blocked for $file"
            blocked=1
        else
            echo "$file passed scan."
        fi
    fi
done

if [[ $blocked -eq 1 ]]; then
    echo "one or more files were blocked due to detected issues."
    exit 1
fi

hg push "${push_args[@]}"
