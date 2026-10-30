#!/bin/bash
# A real visitor timing each menu search, for $1 seconds.
end=$((SECONDS + $1)); n=0; bad=0; times=()
while [ $SECONDS -lt $end ]; do
  r=$(curl -s -o /dev/null -m 10 -w '%{http_code} %{time_total}' 'http://localhost:8000/api/products/search?q=ga')
  [ "${r% *}" = 200 ] || bad=$((bad+1)); times+=("${r#* }"); n=$((n+1)); sleep 0.3
done
printf '%s\n' "${times[@]}" | sort -n | awk -v n=$n -v bad=$bad '{a[NR]=$1} END {printf "legit visitor: %d requests, %d failed, median %.0f ms, p95 %.0f ms\n", n, bad, a[int(NR/2)+1]*1000, a[int(NR*0.95)]*1000}'
