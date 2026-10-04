"""Run policyengine-core YAML tests for a source root, sharded across processes.

Usage: run_yaml.py <root> <out_prefix> <shards> <path> [<path> ...]
Paths are relative to root; directories are expanded to their YAML files.
"""
import glob, os, subprocess, sys, json

W = "/Users/maxghenis/.subfleet/worktrees/20261004-091830-uk-2133-review-r2"
root, prefix, shards, *paths = sys.argv[1:]
shards = int(shards)
files = []
for p in paths:
    full = os.path.join(root, p)
    if os.path.isdir(full):
        files += sorted(glob.glob(os.path.join(full, "**/*.yaml"), recursive=True))
    else:
        files.append(full)
# Balance by file size
files.sort(key=lambda f: -os.path.getsize(f))
buckets = [[] for _ in range(shards)]
sizes = [0] * shards
for f in files:
    i = sizes.index(min(sizes))
    buckets[i].append(f)
    sizes[i] += os.path.getsize(f)
env = dict(os.environ, PYTHONPATH=root)
procs = []
for i, b in enumerate(buckets):
    if not b:
        continue
    log = open(f"{prefix}.shard{i}.log", "w")
    procs.append(
        subprocess.Popen(
            ["uv", "run", "--frozen", "--no-sync", "--project", W,
             "policyengine-core", "test", *b, "-c", "policyengine_uk"],
            cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
    )
codes = [p.wait() for p in procs]
json.dump({"root": root, "files": len(files), "codes": codes}, open(f"{prefix}.done.json", "w"))
