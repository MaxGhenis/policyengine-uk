"""Record the commit a policyengine-uk wheel is built from.

Hatchling runs this hook when it builds the wheel. If the wheel is built from a
clean checkout of policyengine-uk's own repository, the hook writes

    {"git_sha": "<HEAD>", "version": "<version>"}

to ``<name>-<version>.dist-info/extra_metadata/build_info.json`` in the wheel.
``policyengine_uk.build_metadata`` reads it back for installs that keep no
other record of their commit, such as wheels installed from PyPI.

Every other build records nothing:

- editable builds, which read the checkout's HEAD at runtime;
- wheels built from an sdist, which has no ``.git``;
- builds from another repository, or from a directory inside one;
- trees with changes that ``git status`` reports or cannot see
  (assume-unchanged or skip-worktree files);
- builds where any file whose bytes reach the wheel (packaged files, licence
  files, the readme, ``pyproject.toml`` and this hook) is untracked, a
  symlink, or differs from HEAD in raw bytes or executable bit, for example
  through line-ending conversion, a clean filter or ``core.fileMode=false``;
- Python before 3.11, where ``build_metadata.py`` cannot import ``tomllib``.

The file is written to a temporary directory, never into the source tree, and
the sdist does not contain it.
"""

from __future__ import annotations

import atexit
from collections.abc import Iterable
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

BUILD_METADATA_PATH = Path("policyengine_uk", "build_metadata.py")
# Inputs whose bytes reach the wheel besides the packaged files.
BUILD_CONFIGURATION_PATHS = ("pyproject.toml", "hatch_build.py")
# Wheel options that add files this hook does not check.
UNCHECKED_WHEEL_OPTIONS = (
    "shared_data",
    "shared_scripts",
    "extra_metadata",
    "sbom_files",
)
REGULAR_FILE_MODES = {b"100644": False, b"100755": True}
# Generous for `git status` on a large tree; a hung git records nothing.
GIT_TIMEOUT_SECONDS = 60


class BuildInfoHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        self._build_info_directory: str | None = None
        if version == "editable":
            return
        # Provenance must never stop a build, so any failure records nothing.
        try:
            root = Path(self.root)
            paths, reason = wheel_input_paths(self.build_config.builder)
            git_sha = None
            if paths is not None:
                build_metadata = load_build_metadata(root)
                git_sha, reason = find_build_commit(root, paths, build_metadata)
            if git_sha is not None:
                build_info_path = self._write_build_info(git_sha)
                build_data["extra_metadata"][build_info_path] = (
                    build_metadata.BUILD_INFO_NAME
                )
        except Exception as error:
            git_sha, reason = None, f"the commit lookup failed: {error!r}"
        if git_sha is None:
            self.app.display_info(f"No build commit recorded: {reason}")
        else:
            self.app.display_info(f"Recorded build commit {git_sha}")

    def finalize(
        self, version: str, build_data: dict[str, Any], artifact_path: str
    ) -> None:
        if getattr(self, "_build_info_directory", None) is not None:
            shutil.rmtree(self._build_info_directory, ignore_errors=True)
            self._build_info_directory = None

    def _write_build_info(self, git_sha: str) -> str:
        self._build_info_directory = tempfile.mkdtemp(
            prefix="policyengine-uk-build-info-"
        )
        # finalize removes it; this covers a build that fails before then.
        atexit.register(shutil.rmtree, self._build_info_directory, True)
        path = os.path.join(self._build_info_directory, "build_info.json")
        build_info = {"git_sha": git_sha, "version": self.metadata.version}
        with open(path, "w", encoding="utf-8") as file:
            json.dump(build_info, file, sort_keys=True)
            file.write("\n")
        # Reproducible builds normalise file modes; a non-reproducible build
        # would otherwise carry a restrictive umask into the wheel.
        os.chmod(path, 0o644)
        return path


def load_build_metadata(root: Path) -> ModuleType:
    """Load ``policyengine_uk/build_metadata.py`` without importing the package.

    The package imports policyengine-core and the whole model, none of which
    is installed in the build environment. build_metadata itself needs only
    the standard library.
    """
    spec = importlib.util.spec_from_file_location(
        "_policyengine_uk_build_metadata_for_build_hook",
        root / BUILD_METADATA_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    # Leave no __pycache__ in the package directory being built.
    dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = dont_write_bytecode
    return module


def wheel_input_paths(builder: Any) -> tuple[list[str] | None, str]:
    """List the project-relative paths of every file whose bytes reach the wheel.

    These are the files hatchling packages, the licence files and readme it
    copies into the wheel's metadata, and the build configuration. hatchling
    finds licence files by globbing (``LICEN[CS]E*`` and others) without
    regard to .gitignore, so they are listed separately. Returns
    ``(None, reason)`` if the wheel target adds files in ways this hook does
    not check.
    """
    for option in UNCHECKED_WHEEL_OPTIONS:
        if getattr(builder.config, option, None):
            return None, f"the wheel target sets {option.replace('_', '-')}"
    core = builder.metadata.core
    paths = [
        included_file.relative_path
        for included_file in builder.recurse_included_files()
    ]
    paths.extend(core.license_files)
    if core.readme_path:
        paths.append(core.readme_path)
    paths.extend(BUILD_CONFIGURATION_PATHS)
    return paths, ""


def find_build_commit(
    root: Path,
    paths: Iterable[str],
    build_metadata: ModuleType,
) -> tuple[str | None, str]:
    """Return the commit that a wheel built at ``root`` packages.

    ``paths`` are the project-relative paths of the files whose bytes reach
    the wheel (see ``wheel_input_paths``). The result is ``(HEAD, "")`` only
    when all of these hold:

    - ``root`` is the top level of a policyengine-uk checkout, by the same
      checks the runtime lookup makes;
    - ``git status`` reports nothing, and git compares every tracked file
      with the working tree;
    - every path is a tracked regular file whose raw bytes and executable bit
      equal HEAD's.

    Otherwise it is ``(None, reason)``.
    """
    try:
        git_sha = build_metadata._get_checkout_git_sha(root / "policyengine_uk")
    except Exception as error:
        # For example an unreadable pyproject.toml.
        return None, f"the checkout lookup failed: {error!r}"
    if git_sha is None:
        return None, "not built from the top level of a policyengine-uk checkout"
    status = _git_output(
        build_metadata,
        root,
        "--no-optional-locks",
        "status",
        "--porcelain",
        "--untracked-files=normal",
    )
    if status is None:
        return None, "git status failed"
    if status:
        return None, "the checkout has uncommitted changes or untracked files"
    # Each index entry is "<tag> <mode> <object> <stage>\t<path>". Status
    # does not compare files marked assume-unchanged (lowercase tag) or
    # skip-worktree ("S", as in a sparse checkout) with the working tree, so
    # such a file could differ from HEAD unseen. With status clean, the
    # index's objects are HEAD's.
    index = _git_output(build_metadata, root, "ls-files", "--stage", "-v", "-z")
    if index is None:
        return None, "git ls-files failed"
    committed = {}
    for entry in filter(None, index.split(b"\0")):
        description, _, path = entry.partition(b"\t")
        tag, mode, object_id = description.split(b" ")[:3]
        if tag != b"H":
            return None, (
                f"git does not compare {os.fsdecode(path)!r} with the working "
                "tree (assume-unchanged, skip-worktree or unmerged)"
            )
        committed[path] = (mode, object_id)
    inputs = sorted({os.fsencode(Path(path).as_posix()) for path in paths})
    for path in inputs:
        # Git and hatchling ignore files differently: hatchling reads only
        # the top-level .gitignore, not nested ones, .git/info/exclude or the
        # user's global excludes, and globs licence files regardless. A file
        # only git ignores would be packaged without being committed.
        if path not in committed:
            return None, f"{os.fsdecode(path)!r} is not tracked by git"
        # hatchling packages what a symlink points to, which the commit does
        # not contain.
        if committed[path][0] not in REGULAR_FILE_MODES or b"\n" in path:
            return None, f"{os.fsdecode(path)!r} is not a regular tracked file"
    # Status compares content after line-ending conversion and clean filters,
    # and ignores the executable bit when core.fileMode is false. Compare the
    # raw bytes and the bit that the wheel will actually carry.
    hashed = _git_output(
        build_metadata,
        root,
        "hash-object",
        "--no-filters",
        "--stdin-paths",
        input=b"".join(path + b"\n" for path in inputs),
    )
    object_ids = hashed.split() if hashed is not None else []
    if len(object_ids) != len(inputs):
        return None, "git hash-object failed"
    for path, object_id in zip(inputs, object_ids):
        mode, committed_object_id = committed[path]
        if object_id != committed_object_id:
            return None, f"{os.fsdecode(path)!r} differs from HEAD"
        try:
            st_mode = os.stat(root / os.fsdecode(path)).st_mode
        except OSError:
            return None, f"{os.fsdecode(path)!r} cannot be read"
        # hatchling marks a file executable when its owner may execute it.
        if bool(st_mode & 0o100) != REGULAR_FILE_MODES[mode]:
            return (
                None,
                f"the executable bit of {os.fsdecode(path)!r} differs from HEAD",
            )
    return git_sha, ""


def _git_output(
    build_metadata: ModuleType, root: Path, *args: str, input: bytes | None = None
) -> bytes | None:
    # Raw bytes, so paths are compared without decoding them in the locale's
    # encoding. The runtime lookup's environment rules apply.
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in build_metadata.GIT_REPOSITORY_ENV_VARS
    }
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            check=True,
            env=env,
            input=input,
            timeout=GIT_TIMEOUT_SECONDS,
        ).stdout
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
