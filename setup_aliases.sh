#!/bin/bash

echo "setting up aliases for git and mercurial..."

# git aliases (.git/config, local only)
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "configuring git aliases..."
    git config alias.add-sec "!bash ./sitm_core/git_secure/git_add_secure.sh"
    git config alias.commit-sec "!bash ./sitm_core/git_secure/git_commit_secure.sh"
    git config alias.push-sec "!bash ./sitm_core/git_secure/git_push_secure.sh"
    git config alias.pull-sec "!bash ./sitm_core/git_secure/git_pull_secure.sh"
else
    echo "skipped git: not in a git repo"
fi

# mercurial aliases (.hg/hgrc, local only)
if [ -d ".hg" ]; then
    echo "configuring hg aliases..."
    hgrc_file=".hg/hgrc"

    if [ ! -f "$hgrc_file" ]; then
        touch "$hgrc_file"
    fi

    if ! grep -q "^\[alias\]" "$hgrc_file"; then
        sed -i '' -e '${/^$/d;}' "$hgrc_file"
        echo "[alias]" >> "$hgrc_file"
    fi

    set_hg_alias() {
        key="$1"
        val="$2"
        if ! grep -q "^$key" "$hgrc_file"; then
            echo "$key = $val" >> "$hgrc_file"
        fi
    }

    set_hg_alias "add-sec" "!bash ./sitm_core/hg_secure/hg_add_secure.sh \"\$@\""
    set_hg_alias "commit-sec" "!bash ./sitm_core/hg_secure/hg_commit_secure.sh \"\$@\""
    set_hg_alias "push-sec" "!bash ./sitm_core/hg_secure/hg_push_secure.sh \"\$@\""
    set_hg_alias "pull-sec" "!bash ./sitm_core/hg_secure/hg_pull_secure.sh \"\$@\""
else
    echo "skipped hg: not in a mercurial repo"
fi

echo "done setting up aliases."