"""Check that a release build records the commit it was built from.

Usage: python .github/check_release_build.py DIST_DIRECTORY COMMIT

Exits non-zero unless the wheel in DIST_DIRECTORY records COMMIT and its own
version in ``.dist-info/extra_metadata/build_info.json`` (written by
hatch_build.py), and the sdist records no commit.
"""

import json
from pathlib import Path
import sys
import tarfile
import zipfile

BUILD_INFO_SUFFIX = ".dist-info/extra_metadata/build_info.json"


def main(dist_directory: str, commit: str) -> int:
    [wheel] = sorted(Path(dist_directory).glob("*.whl"))
    [sdist] = sorted(Path(dist_directory).glob("*.tar.gz"))
    with zipfile.ZipFile(wheel) as archive:
        names = [
            name for name in archive.namelist() if name.endswith(BUILD_INFO_SUFFIX)
        ]
        if len(names) != 1:
            print(f"{wheel.name} records no build commit")
            return 1
        build_info = json.loads(archive.read(names[0]))
    expected = {"git_sha": commit, "version": wheel.name.split("-")[1]}
    if build_info != expected:
        print(f"{wheel.name} records {build_info}, expected {expected}")
        return 1
    with tarfile.open(sdist) as archive:
        if any(name.endswith("build_info.json") for name in archive.getnames()):
            print(f"{sdist.name} contains a build_info.json")
            return 1
    print(f"{wheel.name} records {build_info}; {sdist.name} records no commit")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
