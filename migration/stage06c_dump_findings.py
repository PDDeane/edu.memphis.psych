import sys, json
sys.path.insert(0, ".")
import equivalence
raw = equivalence.enforcement_audit()[0]
out = []
for f in raw:
    # findings are tuples; keep the kind and a trimmed message
    kind = f[1] if len(f) > 1 else "?"
    msg = f[2] if len(f) > 2 else ""
    out.append({"kind": str(kind), "msg": str(msg)[:150]})
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(f"  {len(out)} raw finding(s) -> {sys.argv[1]}")
