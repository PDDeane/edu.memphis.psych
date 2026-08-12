#!/usr/bin/env bash
# Full web sweep: every gradeable item, every included participant, THREE runs
# per item. ~30s a cell and ~480 cells a pass, so most of a day — background it.
#
#   ./sweep_app.sh OUTDIR IDMAP_JSON [RUNS]
#
# Three runs, not one, because one run is not a measurement on this side. Q3
# measured 16/20, 12/20 and 15/20 across three runs — a 4-cell spread — while
# the apparent 5-point gap to the CLI it was being compared against was 0.3
# cells. Several "findings" earlier in this project were single-draw noise, and
# one best-of-three was promoted into a report and read as a 6-point difference
# between the two implementations. agreement_app.py publishes the MEDIAN run and
# prints the spread, so the number in the table carries its own error bar.
#
# RUNS overrides the default for a quick look. A number produced with RUNS=1
# should not be quoted.
#
# Each item also writes <OUTDIR>/<item>.runs.json holding EVERY run, not just the
# published median. That is what makes a per-slot rate on this side countable over
# a real denominator: without it a "3 of 3" on the web hid six discarded runs,
# while the CLI stores one file per run — and a web/CLI difference in how often a
# check fires could not be told apart from sampling.
#
# Resumable: an item whose <OUTDIR>/<item>.json already exists is skipped, so a
# crash or a killed run costs only the item in flight. Delete an item's .json to
# re-run just that item. Per-item stdout lands in <OUTDIR>/<item>.log and the
# summary lines are appended to <OUTDIR>/summary.txt as each item finishes.
set -u

OUT=${1:?usage: sweep_app.sh OUTDIR IDMAP_JSON [RUNS]}
IDMAP=${2:?usage: sweep_app.sh OUTDIR IDMAP_JSON [RUNS]}
RUNS=${3:-3}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
echo "web sweep: $RUNS run(s) per item, publishing the median" | tee -a "$OUT/summary.txt"

# All 26 scored items. T1/T2/1b are the derived ones — no LLM call, so they run
# in seconds and are deterministic; the rest are ~30s a cell.
# Overridable so the script itself can be exercised on one item without copying
# it elsewhere — a copy breaks $HERE and fails for a reason unrelated to the test.
ITEMS=${ITEMS:-"Q1 Q2 Q3 Q4a Q4b Q4c Q5 Q6 PR NR PP NP T1 D1 DAY1 WK1 T2 D2 DAY2 WK2 1a 1b 1c 2a 2b 3"}

for it in $ITEMS; do
  if [ -f "$OUT/$it.json" ]; then
    echo "[skip] $it — already have $OUT/$it.json"
    continue
  fi
  echo "[run ] $it  $(date +%H:%M:%S)"
  python3 "$HERE/agreement_app.py" --item "$it" --idmap "$IDMAP" --runs "$RUNS" \
      --out "$OUT/$it.json" > "$OUT/$it.log" 2>&1
  rc=$?
  line=$(grep -E '^exact ' "$OUT/$it.log" | tail -1)
  fail=$(grep -cE '^\s+p[0-9]+: ' "$OUT/$it.log")
  # Carry the spread into the summary. Without it the summary reads as though the
  # published median were a point estimate, which is the habit this replaced.
  spread=$(grep -oE 'spread [0-9]+ cell' "$OUT/$it.log" | tail -1 | grep -oE '[0-9]+')
  printf '%-5s rc=%s  %s  (+/-%s cells over %s runs, %s unscored cell lines)\n' \
      "$it" "$rc" "${line:-NO SUMMARY}" "${spread:-?}" "$RUNS" "$fail" \
      | tee -a "$OUT/summary.txt"
  # A hard failure leaves no .json, so the next run retries this item.
  [ -s "$OUT/$it.json" ] || echo "[warn] $it produced no results file"
done

echo
echo "=== sweep finished $(date +%H:%M:%S)"
cat "$OUT/summary.txt"
