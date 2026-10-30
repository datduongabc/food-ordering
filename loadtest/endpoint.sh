#!/bin/bash
# endpoint.sh <path> <vus> [duration]: one endpoint under load, with peak container CPU.
S=$(cd "$(dirname "$0")" && pwd)
STATS=$(mktemp)
trap 'rm -f "$STATS"' EXIT
(while true; do docker stats --no-stream --format '{{.Name}} {{.CPUPerc}}' dateno_backend dateno_web dateno_postgres_db; done) > "$STATS" 2>/dev/null & SP=$!
out=$(docker run --rm --network restaurant_project_default -v $S:/scripts -e TARGET="$1" -e VUS=$2 -e DURATION=${3:-20s} grafana/k6 run --quiet /scripts/endpoint.js 2>&1)
sample=$(echo "$out" | grep -o "sample [^\"]*" | head -1)
kill $SP 2>/dev/null; wait $SP 2>/dev/null
cpu=$(awk '{gsub("%","",$2); if($2+0>m[$1]) m[$1]=$2+0} END {printf "backend %s%% web %s%% db %s%%", m["dateno_backend"], m["dateno_web"], m["dateno_postgres_db"]}' "$STATS")
printf "%-30s vus=%-4s %s | %s %s\n" "$1" "$2" "$(echo "$out" | grep rps= | tail -1)" "$cpu" "$sample"
