"""Compare per-test outcomes of the Python masking runs.

MASKED = fails with the means-test perturbation and the limb off, passes with
the perturbation and the limb on, and passes with the limb off alone.
"""
import xml.etree.ElementTree as ET

def outcomes(name):
    root = ET.parse(f"pymask_{name}.xml").getroot()
    out = {}
    for tc in root.iter("testcase"):
        key = f'{tc.get("classname")}::{tc.get("name")}'
        if tc.find("failure") is not None or tc.find("error") is not None:
            out[key] = "fail"
        elif tc.find("skipped") is not None:
            out[key] = "skip"
        else:
            out[key] = "pass"
    return out

runs = {n: outcomes(n) for n in ["head", "limb_off", "pert_on", "pert_off"]}
for n, o in runs.items():
    print(n, {s: sum(1 for v in o.values() if v == s) for s in ("pass", "fail", "skip")})
keys = sorted(set().union(*runs.values()))
print("head failures:", [k for k in keys if runs["head"].get(k) == "fail"])
print("limb_off failures:", [k for k in keys if runs["limb_off"].get(k) == "fail"])
print("perturbation detected (pert_on fails):", len([k for k in keys if runs["pert_on"].get(k) == "fail"]))
masked = [k for k in keys if runs["pert_off"].get(k) == "fail" and runs["pert_on"].get(k) == "pass" and runs["limb_off"].get(k) == "pass"]
print("MASKED:", masked)
diff = [k for k in keys if runs["pert_off"].get(k) != runs["pert_on"].get(k)]
print("pert_on vs pert_off differ:", [(k, runs["pert_on"].get(k), runs["pert_off"].get(k)) for k in diff])
