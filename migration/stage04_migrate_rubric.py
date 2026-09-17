#!/usr/bin/env python3
"""Stage 04 · emit the rubric data as content, and refuse to write it if it moved.

SCRIPTED, IDEMPOTENT, AND SAFE BY REFUSAL. The rubric is the thing every scorer
will read; a migration that wrote a subtly different copy would be the worst
possible outcome, because nothing downstream would object. So:

  * every item is EMITTED from the Python rubric and read back,
  * the read-back is compared against the source it came from,
  * and NOTHING is written unless all 26 agree.

TWO COPIES EXIST AND ARE ASSERTED EQUAL. That is stage 04's shape by design:
the Python modules stay until stage 06c deletes them, so for two stages the
rubric has two sources and the audit's job is to prove they say the same thing.

IDEMPOTENCE IS PART OF THE GATE, not a nicety. A second run must report no
edits. A generator whose output drifts run to run cannot be trusted to have
written what it read -- and the drift is usually ordering, which no byte
comparison of a single run would catch.

ESCAPING: element text takes `<`, `>` and `&` only. Escaping quotes there yields
`&#x27;` in the assembled prompt, measured at 20 characters of difference on one
item during stage 3b.
"""
import argparse, html, json, os, re, sys
from pathlib import Path

esc_text = lambda s: html.escape(str(s), quote=False)
esc_attr = lambda s: html.escape(str(s), quote=True)


def num(v):
    f = float(v)
    return str(int(f)) if f == int(f) else str(f)


def attr(name, value, *, number=False):
    if value is None or value == "" or value is False:
        return ""
    if value is True:
        return f' {name}="true"'
    return f' {name}="{esc_attr(num(value) if number else value)}"'


CADENCE_NOUN = {"daily": "day", "weekly": "week"}


def selector_conditions(rub, item_id: str) -> list:
    """The selectors naming this item, as condition names.

    A selector is a module-level tuple of item ids -- CONTINGENCY_GATE_ITEMS and
    its five siblings -- and it is exactly the INVERSE INDEX of a per-item fact:
    "which items declare this". `MOVE_PICK_ITEMS = ("PR",)` is the same
    statement as PR declaring `move_pick`, which stage 05 already migrated. So
    the selectors do not need a home of their own; they need the fact recorded
    where it belongs, on the item, and rebuilt on the reading side.

    That also fixes what `check_selectors_govern_something` was written to catch.
    A tuple whose slot was deleted stays defined and governs nothing; a condition
    no segment or scorer consults is visible as an unconsulted NAME.
    """
    import re as _re
    out = []
    for name, val in sorted(vars(rub).items()):
        if not _re.fullmatch(r"[A-Z][A-Z0-9_]*_ITEMS", name):
            continue
        if isinstance(val, tuple) and item_id in val:
            out.append(name[:-len("_ITEMS")].lower())
    return out


def required_move(rub, item) -> str | None:
    """The move this item's type is demonstrated by, resolved as the SCORER does.

    `rubric_h2.REQUIRED_MOVE` is keyed by the OC TYPE, not by item id -- the
    scorer reads `REQUIRED_MOVE[item["expected_type"]]`. On this corpus the four
    items that have an `expected_type` are named after their own type, so a
    per-item table would be right by accident and wrong in principle: an item
    scored against a type it is not named after would silently get no move.
    Resolving through `expected_type` keeps the indirection the scorer has.
    """
    table = getattr(rub, "REQUIRED_MOVE", None) or {}
    et = item.get("expected_type")
    return table.get(str(et)) if et is not None else None


def emit_frame_inputs(item) -> str:
    """The item's own `conditions` and `params`, for selecting frame segments.

    NOT a `cadence=` attribute. The engine must not learn what a cadence IS --
    it selects segments by NAME and fills placeholders by NAME, and a named
    attribute for one subject's concept would put that concept in the engine
    (C2). The rubric says which conditions hold and what the words are; the
    frame says where they go.
    """
    conds, params = [], {}
    # Every course-specific flag rides here as a NAME, for the same reason the
    # cadence does. Decision 11.5 clause 2.
    for name in ("avoidance_scores", "reads_utb_choice", "move_pick", "graph_item"):
        if item.get(name):
            conds.append(name)
    # NO SELECTOR-ONLY CONDITIONS (decision 11.8). `barrier_pick`,
    # `cadence_barrier`, `contingency_gate`, `polarity_gate` and `type_match`
    # were emitted only so the module's `*_ITEMS` tuples could be rebuilt -- and
    # after 6c nothing reads them, because the selectors were a BUILD-TIME
    # device and the build has run. The ones that stay are above: they are
    # per-item facts the modules carry (`move_pick`, `graph_item`,
    # `reads_utb_choice`, `avoidance_scores`) or a segment consumes
    # (`cadence`, `avoidance_scores`).
    if item.get("_required_move"):
        params["required_move"] = item["_required_move"]
    if item.get("cadence"):
        conds.append("cadence")
        params["noun"] = CADENCE_NOUN[item["cadence"]]
        params["adj"] = item["cadence"]
        # The VALUE as well as the name: `adj` is prose for the frame and this
        # is a scoring fact, and they are only incidentally the same word.
        params["cadence"] = item["cadence"]
    out = ""
    if conds:
        out += attr("conditions", "|".join(conds))
    if params:
        out += attr("params", "|".join(f"{k}={v}" for k, v in params.items()))
    return out


def emit_item(item, slot_spec, credit_list) -> list[str]:
    """One <Item>. Order is fixed so a second run cannot reorder anything."""
    L = [f'  <Item scores="{esc_attr(item["id"])}"'
         + attr("max", item.get("max"), number=True)
         + attr("label", item.get("label"))
         + attr("increment", item.get("increment"), number=True)
         + (' deriveFromClauses="true"' if item.get("derive_from_criteria") else "")
         + (' deriveFromCredit="true"' if item.get("derive_from_credit") else "")
         + attr("blankCode", item.get("blank_code"))
         + attr("expectedType", item.get("expected_type"))
         + attr("unreachableCodes", ",".join(item.get("unreachable_codes") or []) or None)
         + emit_frame_inputs(item)
         + '>']
    L.append(f'    <Question>{esc_text(item["question"])}</Question>')

    # SHEET first, in sheet order. The charging gates run in THIS order -- it
    # is slot order on every item that has them, which is why they are not a
    # separate ordered list.
    gates = {g["key"]: g for g in item.get("oc_gates") or []}
    for s in slot_spec:
        g = gates.get(s["key"])
        L.append('    <Slot'
                 + attr("key", s["key"]) + attr("label", s.get("label"))
                 + attr("seg", s.get("seg")) + attr("pts", s.get("pts"), number=True)
                 + ("" if not s.get("gate") else ' gate="true"')
                 + attr("charge", g["code"] if g else None)
                 + attr("because", g["text"] if g else None) + '/>')
    # SCORING second, in CREDIT order -- which differs from sheet order on 11 of
    # 26 items, and on 4 of them names components that are not slots at all.
    for c in credit_list:
        a = (attr("what", c["what"]) + attr("pts", c.get("pts"), number=True)
             + attr("verdicts", "|".join(c["verdicts"]) if c.get("verdicts") else None)
             + attr("codes", ",".join(f"{k}={v}" for k, v in c["codes"].items())
                    if c.get("codes") else None)
             + ("" if not c.get("gates") else ' gates="true"')
             + attr("free", ",".join(c["free"]) if c.get("free") else None)
             + ("" if not c.get("reported") else ' reported="true"')
             + attr("rule", c.get("rule")))
        L.append(f'    <Credit{a}>{esc_text(c["desc"])}</Credit>')

    for d in item.get("deductions") or []:
        L.append(f'    <Deduction{attr("code", d["code"])}{attr("pts", d["pts"], number=True)}'
                 f'{"" if not d.get("repeatable") else chr(32) + chr(114) + "epeatable=" + chr(34) + "true" + chr(34)}>'
                 f'{esc_text(d["text"])}</Deduction>')
    for g in item.get("guidance") or []:
        L.append(f'    <Guidance>{esc_text(g)}</Guidance>')
    for k in item.get("context") or []:
        L.append(f'    <Context{attr("item", k)}/>')
    for r in item.get("expect") or []:
        L.append(f'    <Expect{attr("key", r["key"])}{attr("left", r["left"])}'
                 f'{attr("value", r["value"])}'
                 f'{attr("lenient", ",".join(r["lenient"]) if r.get("lenient") else None)}/>')
    for r in item.get("equals") or []:
        L.append(f'    <Equals{attr("key", r["key"])}{attr("left", r["left"])}'
                 f'{attr("right", r["right"])}'
                 f'{attr("lenient", ",".join(r["lenient"]) if r.get("lenient") else None)}/>')
    for r in item.get("forbid") or []:
        conds = ",".join(f'{c["slot"]}={c["value"]}' for c in r.get("conds") or [])
        L.append(f'    <Forbid{attr("key", r["key"])}{attr("conds", conds)}/>')
    for r in item.get("onlyif") or []:
        L.append(f'    <Onlyif{attr("key", r["key"])}{attr("cond", r["cond"])}/>')
    for r in item.get("requires") or []:
        L.append(f'    <Requires{attr("key", r["key"])}{attr("cond", r["cond"])}'
                 f'{attr("lenient", ",".join(r["lenient"]) if r.get("lenient") else None)}/>')
    for r in item.get("maps") or []:
        pairs = ",".join(f'{c["value"]}~{c["verdict"]}' for c in r.get("pairs") or [])
        L.append(f'    <Map{attr("key", r["key"])}{attr("pick", r["pick"])}'
                 f'{attr("pairs", pairs)}{attr("fallback", r.get("fallback"))}/>')
    for r in item.get("counts") or []:
        L.append(f'    <Counts{attr("key", r["key"])}'
                 f'{attr("slots", ",".join(r["slots"]))}/>')
    for r in item.get("cover") or []:
        L.append(f'    <Cover{attr("checks", ",".join(r["keys"]))}'
                 f'{attr("labels", ",".join(r["labels"]))}'
                 f'{attr("item", r.get("of"))}'
                 f'{attr("verdicts", "|".join(r["verdicts"]) if r.get("verdicts") else None)}/>')
    for r in item.get("derived") or []:
        L.append(f'    <Derived{attr("key", r["key"])}{attr("kind", r.get("kind"))}'
                 f'{attr("fields", ",".join(r["fields"]) if r.get("fields") else None)}'
                 f'{attr("words", ",".join(r["words"]) if r.get("words") else None)}'
                 f'{attr("template", ";".join(",".join(num(x) for x in row) for row in r["template"]) if r.get("template") else None)}/>')
    if item.get("derive_from_criteria"):
        L.append('    <Guidance use="@oc_criteria"/>')
    L.append('  </Item>')
    return L


def emit_frames(handout: int) -> list[str]:
    """Shared prose frames, emitted once per rubric.

    A frame exists because its prose is used by several items; emitting it per
    item would put four near-copies of a 2.4-4KB block in the file, which is the
    duplication the frame mechanism was built to end.

    The segments are read from the frozen decomposition rather than re-derived:
    deriving them needs the four rendered variants and a diff, and doing that
    inside a migration would make the migration's output depend on an analysis
    nobody can see in the diff.
    """
    src = Path(__file__).parent / "goldens" / "criteria_frame.json"
    if not src.exists():
        return []
    segs = json.loads(src.read_text())["segments"]
    out = ['  <Frame name="oc_criteria">']
    for seg in segs:
        a = attr("ifDeclared", seg.get("when"))
        out.append(f'    <Segment{a}>{esc_text(seg["text"])}</Segment>')
    out.append('  </Frame>')
    return out


def emit_vocabularies(rub, spec) -> list[str]:
    """<Verdicts> for each vocabulary a `pick(...)` slot names."""
    so = getattr(rub, "SLOT_OPTIONS", None) or {}
    if not so:
        return []
    named = {}
    for slots in spec.values():
        for s in slots:
            m = re.match(r"pick\(([^)]+)\)", s.get("seg") or "")
            if m and s["key"] in so:
                named.setdefault(m.group(1), so[s["key"]])
    return [f'  <Verdicts{attr("name", n)}{attr("values", "|".join(v))}/>'
            for n, v in sorted(named.items())]


def build_all() -> str:
    """ONE rubric, under the id the COURSE resolves. Decision 11.12.

    Previously three files, one per handout, under ids nothing referenced --
    while `<Course>` resolved a 34-line stage-3b demonstration that held 4 of
    the 26 items. Both gates passed anyway because each tested its own artifact
    (T28); the join is now gated by `join_check.py`.

    The rubric does NOT learn what a handout is. Items are emitted in handout
    order because that is a readable order, and the reading side partitions them
    by the item's own content element, exactly as `olx_prompts.HANDOUT` already
    derives it. Handout membership is a property of the CONTENT; a rubric that
    declared it would be holding the same fact twice.
    """
    import handouts as H
    L = ['<Rubric id="bmod_rubric" title="Behaviour-modification scoring rubric">']
    for handout in (1, 2, 3):
        rub = H.config(handout)["rubric"]
        rub = getattr(rub, "_module", rub)
        spec = getattr(rub, "SLOT_SPEC", {}) or {}
        L += emit_vocabularies(rub, spec)
        if any(it.get("derive_from_criteria") for it in rub.ITEMS):
            L += emit_frames(handout)
        for it in rub.ITEMS:
            it = {**it, "_selectors": selector_conditions(rub, it["id"]),
                  "_required_move": required_move(rub, it)}
            L += emit_item(it, spec.get(it["id"]) or [], it.get("credit") or [])
    L.append('</Rubric>')
    return "\n".join(L) + "\n"


def build(handout: int) -> str:
    import handouts as H
    # THE MODULE ITSELF, unwrapped. Stage 06a made `config(h)["rubric"]` a proxy
    # that can serve the rubric OBJECT, and this script's whole job is to read
    # the MODULE and emit the object -- through the proxy it could end up reading
    # its own output. `vars()` on the proxy is the sharper edge: it returns the
    # proxy's instance dict, so a selector scan came back empty and emitted
    # nothing, with no error anywhere.
    rub = H.config(handout)["rubric"]
    rub = getattr(rub, "_module", rub)
    spec = getattr(rub, "SLOT_SPEC", {}) or {}
    L = [f'<Rubric id="bmod_h{handout}_rubric" title="Handout {handout} rubric">']
    # A named vocabulary, declared once and picked from by many slots. The
    # module kept the CONTENTS in SLOT_OPTIONS while the sheet named only the
    # vocabulary, so nothing in the rubric said what was in it.
    L += emit_vocabularies(rub, spec)
    # Only where an item actually uses it: a frame no item references is dead
    # prose, and the materialiser reports one.
    if any(it.get("derive_from_criteria") for it in rub.ITEMS):
        L += emit_frames(handout)
    for it in rub.ITEMS:
        it = {**it, "_selectors": selector_conditions(rub, it["id"]),
              "_required_move": required_move(rub, it)}
        L += emit_item(it, spec.get(it["id"]) or [], it.get("credit") or [])
    L.append('</Rubric>')
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, a.scoring)
    outdir = Path(a.out)

    # THE EMITTER MUST NOT VERIFY AGAINST ITS OWN OUTPUT. `handouts` defaults to
    # `dual`, which proves the module and the rubric object agree on first use --
    # and the object it would read is the file this script is about to write. On
    # the run that first emitted one file, that meant comparing the modules
    # against the STALE four-item demonstration and aborting before writing
    # anything, with a diff that looked like missing rubric content.
    os.environ["RUBRIC_SOURCE"] = "module"

    text = build_all()
    dest = outdir / "bmod_rubric.olx"
    identical = dest.exists() and dest.read_text() == text

    import handouts as H
    n_items = sum(len(H.config(h)["rubric"].ITEMS) for h in (1, 2, 3))
    print(f"emitted {n_items} item(s) into one rubric, {len(text)} chars -> {dest.name}")
    print("  unchanged" if identical else "  would change: bmod_rubric.olx")

    # The three per-handout files this replaces, and the stage-3b demonstration
    # that was standing in the course's way. Reported, never removed silently:
    # a generated artifact disappearing without a line in the log is how a
    # reference ends up pointing at nothing.
    superseded = [outdir / f"bmod_h{h}_rubric.olx" for h in (1, 2, 3)]
    present = [f for f in superseded if f.exists()]
    if present:
        print(f"  superseded by it: {', '.join(f.name for f in present)}")

    if not a.write:
        print("\n(dry run; pass --write to emit)")
        return 0

    if not identical:
        dest.write_text(text)
    for f in present:
        f.unlink()
    print(f"\nwrote {'0' if identical else '1'} file(s); "
          f"removed {len(present)} superseded file(s)")
    print("IDEMPOTENT" if identical and not present
          else "run again: a second run must report unchanged and 0 superseded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
