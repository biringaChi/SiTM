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
    echo "usage: hg add-sec -cred|-func [files or patterns]"
    exit 1
fi

if [[ ! -f "$detection_script" ]]; then
    echo "detection script not found at $detection_script"
    exit 1
fi

shopt -s nullglob

add_flags=()
files=()
do_addremove=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --include|--exclude|--config)
            add_flags+=("$1" "$2")
            shift 2
            ;;
        --config=*)
            add_flags+=("$1")
            shift
            ;;
        -n|--dry-run)
            add_flags+=("$1")
            shift
            ;;
        -addremove)
            do_addremove=1
            shift
            ;;
        .)
            files+=($(hg status -un .))
            shift
            ;;
        -*)
            add_flags+=("$1")
            shift
            ;;
        *)
            files+=("$1")
            shift
            ;;
    esac
done

if [[ $do_addremove -eq 1 ]]; then
    hg addremove
    files=($(hg status -man | awk '{print $2}'))
fi

if [[ ${#files[@]} -eq 0 ]]; then
    echo "no matching files found."
    exit 0
fi

for file in "${files[@]}"; do
    if [[ -f "$file" ]] && file "$file" | grep -q 'text'; then
        echo "scanning $file for vulnerabilities..."
        python3 "$detection_script" "$file"
        if [[ $? -ne 0 ]]; then
            echo "skipping staging for $file"
            blocked=1
        else
            echo "$file passed scan."
            hg add "${add_flags[@]}" "$file"
        fi
    else
        hg add "${add_flags[@]}" "$file"
    fi
done

if [[ $blocked -eq 1 ]]; then
    echo "one or more files were blocked due to detected issues."
    exit 1
fi
