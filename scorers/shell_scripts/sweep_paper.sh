#!/bin/bash
# A full multi-run sweep of the PAPER scorer (score.py), on either model, folded
# into the same per-item `.runs.json` the other two scorers emit.
#
#   ./sweep_paper.sh OUT_DIR [RUNS] [BACKEND]
#
#   BACKEND=lo   score.py through the dev server -> gpt-5-mini   -> side `paper`
#   BACKEND=api  score.py against the Anthropic API -> Opus      -> side `paper_opus`
#   BACKEND=cli  score.py through the claude CLI -> Opus         -> side `paper_opus`
#
# WHY TWO SIDES AND NOT ONE. Only the gpt-5-mini sweep is comparable to the web
# and cli columns: those were both measured on gpt-5-mini, so an Opus paper run
# varies the model AND the path at once and can settle neither. It answers a
# different question -- is the ceiling the rubric or the model -- and the ledger
# keeps it in its own slot so it cannot be read as progress on the first one.
#
# score.py has no --runs of its own: it scores each handout once per invocation.
# The runs are driven here into rN/hM/, the layout the earlier paper corpus used,
# and paper_runs.py folds them per item afterwards. Without that fold the third
# scorer can be RUN and not RECORDED, which is what kept it out of the ledger.
#
# The budget cap is passed through rather than trusted: ~519 calls per run, ~3,100
# at six runs. Cheap on gpt-5-mini and emphatically not on Opus.
set -u
OUT=${1:?usage: sweep_paper.sh OUT_DIR [RUNS] [BACKEND]}
RUNS=${2:-6}
BACKEND=${3:-lo}
BUDGET=${MAX_BUDGET_USD:-25}
HERE="$(cd "$(dirname "$0")" && pwd)"
# THE SCRIPT MOVED, THE TARGETS DID NOT ALL MOVE WITH IT. `$HERE` is this
# file's own directory -- `scorers/shell_scripts/` since 2026-09-27 -- so the
# python it drives is one level up in `scorers/` (the general programs) or in
# the engine package `scoring/` (everything else). Both are resolved from the
# repository root rather than assumed to sit beside this file.
ROOT="$(cd "$HERE/../.." && pwd)"
SCORERS="$ROOT/scorers"
SCORING="$ROOT/scoring"


case "$BACKEND" in
  lo)       SIDE=paper;      MODEL=${AZURE_DEPLOYMENT_ID:-gpt-5-mini} ;;
  api|cli)  SIDE=paper_opus; MODEL=opus ;;
  *) echo "unknown backend '$BACKEND' (expected lo, api or cli)" >&2; exit 2 ;;
esac

mkdir -p "$OUT"
echo "paper sweep: $RUNS run(s) x 3 handouts | backend=$BACKEND model=$MODEL -> side '$SIDE' | budget \$$BUDGET" \
  | tee "$OUT/summary.txt"

for r in $(seq 1 "$RUNS"); do
  for h in 1 2 3; do
    d="$OUT/r$r/h$h"
    if [ -f "$d/.done" ]; then
      echo "[skip] r$r h$h — already complete" | tee -a "$OUT/summary.txt"
      continue
    fi
    mkdir -p "$d"
    echo "[run ] r$r h$h  $(date +%H:%M:%S)"
    python3 "$SCORERS/score.py" --handout "$h" --backend "$BACKEND" --outdir "$d" \
        --max-budget-usd "$BUDGET" > "$OUT/r$r-h$h.log" 2>&1
    rc=$?
    # A hard failure leaves no marker, so re-running retries just that slice --
    # the property sweep_app.sh relies on, and the reason a killed run costs one
    # handout rather than the sweep.
    [ $rc -eq 0 ] && touch "$d/.done"
    n=$(ls "$d"/participant_*.json 2>/dev/null | wc -l)
    printf 'r%s h%s rc=%s  %s participant file(s)\n' "$r" "$h" "$rc" "$n" | tee -a "$OUT/summary.txt"
  done
done

echo "folding into per-item runs..." | tee -a "$OUT/summary.txt"
python3 "$SCORING/paper_runs.py" "$OUT" "$OUT/runs" "$MODEL" "$BACKEND" | tee -a "$OUT/summary.txt"
echo "record with: python3 $SCORING/measured.py --record <ITEM> $OUT/runs/<ITEM>.runs.json $SIDE" \
  | tee -a "$OUT/summary.txt"
