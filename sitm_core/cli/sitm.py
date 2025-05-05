import sys
import subprocess
from pathlib import Path

"""
Author: Chidera Biringa
"""

def detect_vcs():
    if Path(".git").exists():
        return "git"
    elif Path(".hg").exists():
        return "hg"
    else:
        return None

def build_command(vcs, args):
    if len(args) < 2 or args[0] != "add":
        print_usage_and_exit()

    scan_flag = args[1]
    if scan_flag not in {"-cred", "-func"}:
        print("Usage: sitm add -cred|-func [args]")
        sys.exit(1)

    rest = args[2:]
    return [vcs, "add-sec", scan_flag] + rest

def print_usage_and_exit():
    print("Usage:")
    print("  sitm add -cred|-func [args]")
    print("  sitm commit -cred|-func [args]")
    print("  sitm push -cred|-func [args]")
    print("  sitm pull -cred|-func [args]")
    sys.exit(1)

def main():
    vcs = detect_vcs()
    if not vcs:
        print("❌ Error: No supported VCS detected (expected .git or .hg folder).")
        sys.exit(1)

    args = sys.argv[1:]
    if not args:
        print_usage_and_exit()

    cmd_type = args[0]
    if cmd_type == "add":
        cmd = build_command(vcs, args)
    elif cmd_type == "commit":
        cmd = [vcs, "commit-sec"] + args[1:]
    elif cmd_type == "push":
        cmd = [vcs, "push-sec"] + args[1:]
    elif cmd_type == "pull":
        cmd = [vcs, "pull-sec"] + args[1:]
    else:
        print_usage_and_exit()

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        # print(f"❌ Command failed: {' '.join(cmd)}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
