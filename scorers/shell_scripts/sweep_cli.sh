#!/usr/bin/env bash
# Full CLI-side sweep: the shipped prompt, scored by the CLI's rules, every item,
# every included participant. The companion to sweep_app.sh, which drives the same
# prompts through the app instead.
#
#   ./sweep_cli.sh OUTDIR [RUNS]
#
# Resumable: an item whose <OUTDIR>/<item>.json exists is skipped, so a crash costs
# only the item in flight. Delete an item's .json to re-run just that item.
#
# RUNS is passed to agreement.py EXPLICITLY rather than inherited from its default,
# so the cost is visible at the call site: three runs an item is ~2.5 hours here,
# against ~50 minutes for one. It defaults to 3 anyway, because a single run cannot
# carry a per-item number — Q2 spanned 75-95%% across five runs, Q4b 75-88%% — and
# because the head-to-head was for a long time single-run on this side against
# median-of-three on the web's, which is not a comparison. agreement.py publishes
# the MEDIAN and writes <item>.runs.json holding every run.
#
# A number produced with RUNS=1 should not be quoted.
#
# `-u` is not optional. Without it python block-buffers stdout into the log and a
# dead run looks exactly like a working one — which is how a crashed run and a
# three-day-dead waiter both got reported here as "in progress". With it, each cell
# prints `p12 Q2 gold=5.00 pred=5.00` as it lands, so `tail -f` shows real results.
set -u

OUT=${1:?usage: sweep_cli.sh OUTDIR [RUNS]}
RUNS=${2:-3}
HERE=$(cd "$(dirname "$0")" && pwd)
# THE SCRIPT MOVED, THE TARGETS DID NOT ALL MOVE WITH IT. `$HERE` is this
# file's own directory -- `scorers/shell_scripts/` since 2026-09-27 -- so the
# python it drives is one level up in `scorers/` (the general programs) or in
# the engine package `scoring/` (everything else). Both are resolved from the
# repository root rather than assumed to sit beside this file.
ROOT="$(cd "$HERE/../.." && pwd)"
SCORERS="$ROOT/scorers"
SCORING="$ROOT/scoring"

mkdir -p "$OUT"
echo "cli sweep: $RUNS run(s) per item, publishing the median" | tee -a "$OUT/summary.txt"

# Item -> handout. 1b, T1 and T2 are DerivedChecks sheets with no model call on
# either side, so there is no prompt to measure — but they ARE scored items with
# a gold column, and agreement.py derives them from the reconstructed fields the
# same way the web derives them from the real ones. They used to be left to
# sweep_app.sh, which meant the web column covered twelve handout-2 items and
# all six of handout 3 while the CLI column covered ten and five, and the
# head-to-head silently compared different item sets. They cost no LLM calls and
# run in about a second.
run () {                       # run <handout> <item>...
  local h=$1; shift
  for it in "$@"; do
    if [ -f "$OUT/$it.json" ]; then
      echo "[skip] $it — already have $OUT/$it.json"
      continue
    fi
    echo "[run ] $it  $(date +%H:%M:%S)"
    python3 -u "$SCORERS/agreement.py" --handout "$h" --items "$it" --runs "$RUNS" \
        --out "$OUT/$it.json" > "$OUT/$it.log" 2>&1
    rc=$?
    line=$(grep -E '^ *'"$it"' +[0-9]' "$OUT/$it.log" | tail -1)
    # A cell that FAILS prints no result line, so the failure block is the only
    # place it appears. Surface the count here rather than letting a rate computed
    # over a biased subset read as a clean one.
    bad=$(grep -cE '^      p[0-9]+ ' "$OUT/$it.log")
    # Carry the spread into the summary, as sweep_app.sh does: without it the
    # published median reads as a point estimate, which is the habit this replaced.
    spread=$(grep -oE 'spread [0-9]+ cell' "$OUT/$it.log" | tail -1 | grep -oE '[0-9]+')
    printf '%-5s rc=%s  %s  (+/-%s cells over %s runs, %s failed cell(s))\n' \
        "$it" "$rc" "${line:-NO SUMMARY}" "${spread:-?}" "$RUNS" "$bad" \
        | tee -a "$OUT/summary.txt"
    [ -s "$OUT/$it.json" ] || echo "[warn] $it produced no results file"
  done
}

# Overridable so this script can be exercised on one item without copying it
# elsewhere — a copy breaks $HERE and fails for a reason unrelated to the test.
# Same escape hatch sweep_app.sh has, added after a copy-based test wasted a run.
#
# `${VAR-default}`, NOT `${VAR:-default}`: the colon form substitutes the default
# for an EMPTY value as well as an unset one, so `H1_ITEMS= ./sweep_cli.sh out`
# meaning "skip handout 1" silently ran all eight of its items instead. Without
# the colon an explicitly empty list means none, which is what a caller asking
# for none expects.
run 1 ${H1_ITEMS-Q1 Q2 Q3 Q4a Q4b Q4c Q5 Q6}
run 2 ${H2_ITEMS-PR NR PP NP T1 D1 DAY1 WK1 T2 D2 DAY2 WK2}
run 3 ${H3_ITEMS-1a 1b 1c 2a 2b 3}

echo
echo "=== sweep finished $(date +%H:%M:%S)"
cat "$OUT/summary.txt"
