"""Review r2 harness: seeded differential of production is_claimant_or_partner
against the test module's reference, beyond the 25 derandomized examples.
One Simulation; no datasets."""
import random
import numpy as np
from policyengine_uk.tests import test_child_and_adult_definitions_properties as t

rng = random.Random(20261002)
EDU = t.EDUCATIONS
fams, kinds = [], []

# A) arbitrary units: 0, 1 or 2 heads, random flags/education, ages 0-90.
for _ in range(1500):
    size = rng.randint(1, 6)
    nheads = rng.choice([0, 1, 1, 1, 2])
    heads = set(rng.sample(range(size), min(nheads, size)))
    fams.append([t.person(rng.randint(0, 90), current_education=rng.choice(EDU),
                          is_in_approved_training=rng.random() < 0.5,
                          is_parent=rng.random() < 0.3,
                          is_benunit_head=i in heads) for i in range(size)])
    kinds.append("arbitrary")

# B) every unflagged pair 20-90 with the YOUNGER as explicit head: couple.
for a in range(20, 91):
    for b in range(20, a + 1):
        fams.append([t.person(b, is_benunit_head=True), t.person(a)])
        kinds.append("younger_head")

# C) child head (not an HBAI adult) with two unflagged adults: claimant is the eldest adult.
for gap in (15, 19, 20, 25, 40):
    fams.append([t.person(10, is_benunit_head=True), t.person(70), t.person(70 - gap)])
    kinds.append("child_head_gap%d" % gap)
    fams.append([t.person(10, is_benunit_head=True), t.person(70 - gap), t.person(70)])
    kinds.append("child_head_rev_gap%d" % gap)

# D) no head flags at all (calculator default computes the head).
for gap in (19, 20, 25):
    fams.append([t.person(70 - gap), t.person(70)])
    kinds.append("nohead_gap%d" % gap)

# E) valid families (as in the generator) with the round-2 count invariant.
valid_start = len(fams)
for _ in range(800):
    adults = [rng.randint(20, 90) for _ in range(rng.randint(1, 2))]
    deps = [rng.randint(0, 19) for _ in range(rng.choice([0, 0, 1, 2, 3]))]
    fam = [t.person(age, is_parent=bool(deps), is_benunit_head=i == 0, is_SP_age=age >= 66)
           for i, age in enumerate(adults)]
    for age in deps:
        edu = rng.choice(EDU)
        tr = rng.random() < 0.5
        if age >= 18 and edu in {"NOT_IN_EDUCATION", "TERTIARY"}:
            tr = True
        fam.append(t.person(age, current_education=edu, is_in_approved_training=tr))
    fams.append(fam)
    kinds.append("valid")

sim = t.simulate(fams)
actual = sim.calculate("is_claimant_or_partner", t.YEAR)
mism, off = [], 0
counts = {}
for fam, kind in zip(fams, kinds):
    got = list(actual[off:off + len(fam)])
    ref = t.claimants_or_partners(fam)
    counts[kind.split("_gap")[0]] = counts.get(kind.split("_gap")[0], 0) + 1
    if got != ref:
        mism.append((kind, [(p["age"], p["is_benunit_head"], p["is_parent"], p["current_education"]) for p in fam], got, ref))
    if kind == "younger_head":
        assert got == [True, True], (fam, got)
    if kind.startswith("child_head") or kind.startswith("nohead"):
        print(kind, [p["age"] for p in fam], got)
    if kind == "valid":
        ad = [p for p in fam if p["age"] >= 20]
        wide = len(ad) == 2 and not ad[0]["is_parent"] and ad[0]["age"] - ad[1]["age"] >= 20
        assert sum(got) == len(ad) - wide, (fam, got)
    off += len(fam)
print("families by kind:", counts)
print("model-vs-reference mismatches:", len(mism))
for m in mism[:10]:
    print(m)
