#!/bin/bash

# Author: Chidera Biringa

project_root=$(cd "$(dirname "$0")/.." && pwd)

# Default mode is credential scan
mode="cred"
if [[ "$1" == "-func" ]]; then
    mode="func"
    shift
elif [[ "$1" == "-cred" ]]; then
    shift
fi

# Select correct detector
if [[ "$mode" == "func" ]]; then
    detection_script="$project_root/inference/vulstyle_call.py"
else
    detection_script="$project_root/inference/dance_call.py"
fi

if [[ ! -f "$detection_script" ]]; then
    echo "❌ detection script not found at $detection_script"
    exit 1
fi

pull_args=()
remote="default"

# Parse pull args
while [[ $# -gt 0 ]]; do
    case "$1" in
        -*)
            pull_args+=("$1")
            ;;
        *)
            remote="$1"
            ;;
    esac
    shift
done

echo "📥 Fetching from $remote..."

# Try fetch, fallback to pull if needed
if ! hg fetch "$remote" "${pull_args[@]}" 2>/dev/null; then
    hg pull "$remote" "${pull_args[@]}"
fi

# Get changed files (added, modified)
changed=$(hg status -n -a -m)

if [[ -z "$changed" ]]; then
    echo "✅ no incoming changes to scan."
    exit 0
fi

echo "🔍 scanning pulled files for vulnerabilities..."

vulnerable=0

for file in $changed; do
    if [[ -f "$file" ]] && file "$file" | grep -q 'text'; then
        echo "scanning $file..."
        python3 "$detection_script" "$file"
        if [[ $? -ne 0 ]]; then
            echo "🚫 vulnerability detected in $file"
            vulnerable=1
        else
            echo "✅ $file passed scan."
        fi
    else
        echo "⏭️ skipped binary or missing file: $file"
    fi
done

if [[ $vulnerable -eq 1 ]]; then
    echo "❗ one or more vulnerabilities detected."
    echo -n "↩️ do you want to rollback this pull? (y/n): "
    read -r confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        hg rollback
        echo "✅ pull reverted."
        exit 1
    else
        echo "⚠️ proceeding despite detected issues."
    fi
fi

echo "✅ pull completed."
exit 0
