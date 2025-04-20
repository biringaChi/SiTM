#!/bin/bash

project_root=$(cd "$(dirname "$0")/.." && pwd)

# Mode selection
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

# Detect rebase/ff-only options
rebase_flag=""
remote="origin"
branch=$(git rev-parse --abbrev-ref HEAD)

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --rebase)
            rebase_flag="--rebase"
            ;;
        --no-rebase)
            rebase_flag="--no-rebase"
            ;;
        --ff-only)
            rebase_flag="--ff-only"
            ;;
        origin|upstream)
            remote="$1"
            ;;
        main|dev|*)
            branch="$1"
            ;;
    esac
    shift
done

git fetch "$remote"
changed_files=$(git diff --name-only HEAD.."$remote"/"$branch")

if [[ -z "$changed_files" ]]; then
    echo "✅ No incoming changes to pull."
    exit 0
fi

echo "🔍 Checking incoming files for vulnerabilities..."

vulnerable=0
for file in $changed_files; do
    if [[ -f "$file" ]] && file "$file" | grep -q 'text'; then
        echo "📄 Scanning $file..."
        python3 "$detector_script" "$file"
        if [[ $? -ne 0 ]]; then
            echo "⚠️  Detected vulnerability in pulled file $file."
            vulnerable=1
        fi
    fi
done

if [[ $vulnerable -eq 1 ]]; then
    echo -n "⚠️  Vulnerabilities detected. Do you want to continue with the pull? (y/n): "
    read -r confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "❌ Pull aborted due to detected vulnerabilities."
        exit 1
    fi
fi

echo "📥 Pulling from $remote $branch $rebase_flag..."
git pull $rebase_flag "$remote" "$branch"

if [[ $vulnerable -eq 1 ]]; then
    echo -n "⚠️  Do you want to undo the pull? (y/n): "
    read -r undo
    if [[ "$undo" == "y" || "$undo" == "Y" ]]; then
        echo "🔁 Reverting pull..."
        git reset --hard ORIG_HEAD
        echo "✅ Pull reverted."
    fi
fi

exit 0
