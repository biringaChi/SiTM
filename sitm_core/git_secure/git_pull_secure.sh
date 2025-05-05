#!/bin/bash

# Author: Chidera Biringa

project_root=$(cd "$(dirname "$0")/.." && pwd)

mode="cred"
if [[ "$1" == "-func" ]]; then
    mode="func"
    shift
elif [[ "$1" == "-cred" ]]; then
    shift
fi

if [[ "$mode" == "func" ]]; then
    detector_script="$project_root/inference/vulstyle_call.py"
else
    detector_script="$project_root/inference/dance_call.py"
fi

rebase_flag=""
remote="origin"
branch=$(git rev-parse --abbrev-ref HEAD)

# Parse additional args
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --rebase|--ff-only|--no-rebase)
            rebase_flag="$1"
            ;;
        origin|upstream)
            remote="$1"
            ;;
        main|master|dev)
            branch="$1"
            ;;
    esac
    shift
done

# Fetch remote changes
git fetch "$remote"

# Get remote commit ref
remote_ref=$(git rev-parse "$remote/$branch")

# Diff between current HEAD and remote branch
changed_files=$(git diff --name-only HEAD "$remote_ref")

if [[ -z "$changed_files" ]]; then
    echo "✅ no incoming changes to pull."
    exit 0
fi

echo "🔍 checking remote changes for vulnerabilities..."

vulnerable=0

for file in $changed_files; do
    echo "incoming change: $file (from $remote/$branch)"
    echo "scanning before merge..."

    temp_path=".sitm_tmp_remote_$(basename "$file")"
    git show "$remote/$branch:$file" > "$temp_path" 2>/dev/null

    if [[ -f "$temp_path" ]]; then
        if file "$temp_path" | grep -q 'text'; then
            python3 "$detector_script" "$temp_path"
            if [[ $? -ne 0 ]]; then
                echo "🚫 detected vulnerability in remote version of $file — pull blocked."
                vulnerable=1
            else
                echo "✅ $file passed scan."
            fi
        else
            echo "⏭️ skipped non-text file $file"
        fi
        rm -f "$temp_path"
    fi
done

if [[ $vulnerable -eq 1 ]]; then
    echo -n "❗ vulnerabilities detected. continue with pull? (y/n): "
    read -r confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "❌ pull aborted."
        exit 1
    fi
fi

echo "📥 pulling from $remote $branch $rebase_flag..."
git pull $rebase_flag "$remote" "$branch"

if [[ $vulnerable -eq 1 ]]; then
    echo -n "↩️ do you want to undo the pull? (y/n): "
    read -r undo
    if [[ "$undo" == "y" || "$undo" == "Y" ]]; then
        git reset --hard ORIG_HEAD
        echo "✅ pull reverted."
    fi
fi

exit 0