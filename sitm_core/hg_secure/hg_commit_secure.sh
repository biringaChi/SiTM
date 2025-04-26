#!/bin/bash

# Author: Chidera Biringa

blocked=0
project_root=$(cd "$(dirname "$0")/.." && pwd)

if [[ "$1" == "-cred" ]]; then
    detection_script="$project_root/inference/dance_call.py"
    shift
elif [[ "$1" == "-func" ]]; then
    detection_script="$project_root/inference/vulstyle_call.py"
    shift
else
    echo "usage: hg commit-sec -cred|-func [files or flags]"
    exit 1
fi

if [[ ! -f "$detection_script" ]]; then
    echo "detection script not found at $detection_script"
    exit 1
fi

commit_args=()
targets=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        -A|--addremove)
            hg addremove
            shift
            ;;
        -*)
            commit_args+=("$1")
            if [[ "$1" =~ ^-m$ || "$1" =~ ^--(message|user|date)$ ]]; then
                shift
                commit_args+=("$1")
            fi
            shift
            ;;
        *)
            targets+=("$1")
            shift
            ;;
    esac
done

if [[ ${#targets[@]} -eq 0 ]]; then
    targets=$(hg status -man | awk '{print $2}')
else
    targets="${targets[@]}"
fi

for file in $targets; do
    if [[ -f "$file" ]] && file "$file" | grep -q 'text'; then
        echo "scanning $file for vulnerabilities..."
        python3 "$detection_script" "$file"
        if [[ $? -ne 0 ]]; then
            echo "commit blocked for $file"
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

hg commit "${commit_args[@]}" $targets
