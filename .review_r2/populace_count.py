"""Aggregate-only: childless unflagged two-adult benefit units 20+ years apart in the
pinned populace_uk_2023 overlay (sha256 f17306cc...), split by head order. No records printed;
counts under 10 suppressed."""
import pandas as pd, numpy as np
F = "/Users/maxghenis/.cache/huggingface/hub/datasets--policyengine--populace-uk-private/snapshots/a75a9a831d6b07aaffbd09713f2a1124f5c0f08f/populace_uk_2023.h5"
store = pd.HDFStore(F, "r")
pcols = list(store.select("person", start=0, stop=0).columns)
hcols = list(store.select("household", start=0, stop=0).columns)
want = [c for c in ("person_benunit_id", "person_household_id", "age", "is_parent", "is_benunit_head") if c in pcols]
print("person cols used:", want, "| has is_claimant_or_partner:", "is_claimant_or_partner" in pcols)
p = store.select("person", columns=want)
h = store.select("household", columns=[c for c in ("household_id", "household_weight") if c in hcols])
tp = store.select("time_period") if "/time_period" in store.keys() else None
store.close()
print("time_period:", None if tp is None else tp.values.ravel()[:3])
g = p.groupby("person_benunit_id")
size = g["age"].transform("size")
two = p[size == 2].copy()
two["min_age"] = two.groupby("person_benunit_id")["age"].transform("min")
two["max_age"] = two.groupby("person_benunit_id")["age"].transform("max")
two["any_parent"] = two.groupby("person_benunit_id")["is_parent"].transform("max").astype(bool)
u = two[(two.min_age >= 20) & (two.max_age - two.min_age >= 20) & ~two.any_parent]
units = u.groupby("person_benunit_id").agg(hh=("person_household_id", "first"))
# head order: is the elder the flagged head?
eld = u.sort_values("age", ascending=False).groupby("person_benunit_id").first()
units["elder_is_head"] = eld["is_benunit_head"].astype(bool)
units["any_head"] = u.groupby("person_benunit_id")["is_benunit_head"].max().astype(bool)
w = h.set_index("household_id")["household_weight"] if "household_weight" in h else None
def rep(mask, label):
    n = int(mask.sum())
    wt = float(w.reindex(units.loc[mask, "hh"]).sum()) if w is not None else float("nan")
    print(f"{label}: units={'<10 (suppressed)' if n < 10 else n}" + ("" if n < 10 else f", weighted households≈{wt/1e3:.0f}k"))
rep(units.elder_is_head | ~units.any_head, "split by this PR (elder is head, or no head flag)")
rep(units.any_head & ~units.elder_is_head, "kept (younger is head)")
# Scale and de-duplicated household weights.
print("total weighted households≈%.1fm; share of person rows flagged is_parent=%.2f" % (float(w.sum())/1e6, float(p.is_parent.mean())))
for mask, label in ((units.elder_is_head | ~units.any_head, "split"), (units.any_head & ~units.elder_is_head, "kept")):
    hh = units.loc[mask, "hh"].unique()
    print(label, "unique households", len(hh) if len(hh) >= 10 else "<10", "weighted≈%.0fk" % (float(w.reindex(hh).sum())/1e3))
