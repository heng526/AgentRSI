#!/usr/bin/env bash
set -euo pipefail
root=/home/hust/research_recuris
pid_file="$root/frozen/multifamily_k2.pid"
if test -s "$pid_file" && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "ALREADY_RUNNING $(cat "$pid_file")"
    exit 0
fi
nohup "$root/Recuris/.venv/bin/python" "$root/run_multifamily_k2.py" \
    > "$root/frozen/multifamily_master.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$pid_file"
sleep 2
kill -0 "$(cat "$pid_file")"
echo "STARTED $(cat "$pid_file")"
