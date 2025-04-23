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
    echo "usage: hg pull-sec -cred|-func [pull flags or remote]"
    exit 1
fi

if [[ ! -f "$detection_script" ]]; then
    echo "detection script not found at $detection_script"
    exit 1
fi

pull_args=()
remote="default"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        -*)
            pull_args+=("$1")
            shift
            ;;
        *)
            remote="$1"
            shift
            ;;
    esac
done

echo "fetching changes from $remote..."
hg fetch "$remote" "${pull_args[@]}" > /dev/null 2>&1 || hg pull "$remote" "${pull_args[@]}"

changed=$(hg status -n -m -a)
if [[ -z "$changed" ]]; then
    echo "no incoming changes to scan."
    exit 0
fi

echo "scanning pulled files for vulnerabilities..."

for file in $changed; do
    if [[ -f "$file" ]] && file "$file" | grep -q 'text'; then
        echo "scanning $file..."
        python3 "$detection_script" "$file"
        if [[ $? -ne 0 ]]; then
            echo "vulnerability detected in $file"
            blocked=1
        else
            echo "$file passed scan."
        fi
    fi
done

if [[ $blocked -eq 1 ]]; then
    echo "one or more vulnerabilities detected in pulled content."
    echo -n "do you want to revert the pull? (y/n): "
    read -r confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        hg rollback
        echo "pull reverted."
        exit 1
    else
        echo "proceeding despite detected issues."
    fi
fi

echo "pull completed."
exit 0