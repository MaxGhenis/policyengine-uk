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
- trees with changes that ``git status`` reports, or with a file the wheel
  would include that git does not track.

The file is written to a temporary directory, never into the source tree, and
the sdist does not contain it.
"""

from __future__ import annotations

from collections.abc import Iterable
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import ModuleType
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

BUILD_METADATA_PATH = Path("policyengine_uk", "build_metadata.py")
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
            included_paths = [
                included_file.relative_path
                for included_file in self.build_config.builder.recurse_included_files()
            ]
            root = Path(self.root)
            build_metadata = load_build_metadata(root)
            git_sha, reason = find_build_commit(root, included_paths, build_metadata)
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
    spec.loader.exec_module(module)
    return module


def find_build_commit(
    root: Path,
    included_paths: Iterable[str],
    build_metadata: ModuleType,
) -> tuple[str | None, str]:
    """Return the commit that a wheel built at ``root`` packages.

    ``included_paths`` are the project-relative paths of the files the wheel
    will contain. The result is ``(HEAD, "")`` only when ``root`` is the top
    level of a policyengine-uk checkout (the same checks the runtime lookup
    makes), ``git status`` reports nothing, and git tracks every included
    file. Otherwise it is ``(None, reason)``.
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
    # Git and hatchling ignore files differently: hatchling reads only the
    # top-level .gitignore, not nested ones, .git/info/exclude or the user's
    # global excludes. A file only git ignores would be packaged without
    # being committed.
    tracked = _git_output(build_metadata, root, "ls-files", "-z")
    if tracked is None:
        return None, "git ls-files failed"
    untracked = {os.fsencode(Path(path).as_posix()) for path in included_paths} - set(
        tracked.split(b"\0")
    )
    if untracked:
        example = os.fsdecode(min(untracked))
        return None, f"the wheel would include {example!r}, which git does not track"
    return git_sha, ""


def _git_output(build_metadata: ModuleType, root: Path, *args: str) -> bytes | None:
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
            timeout=GIT_TIMEOUT_SECONDS,
        ).stdout
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
