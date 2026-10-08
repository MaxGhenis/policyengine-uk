"""Tests for hatch_build.py, which records a wheel's build commit.

The hook may record a commit only when the wheel it builds is exactly what a
clean checkout of that commit builds. These tests build real wheels and
sdists with hatchling from small policyengine-uk projects in temporary git
repositories. Each project uses this repository's pyproject.toml,
.gitignore, hatch_build.py and build_metadata.py.
"""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import venv
import zipfile

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
import pytest

pytest.importorskip("hatchling")
from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder

REPO_ROOT = Path(__file__).resolve().parents[2]
HATCH_BUILD_PATH = REPO_ROOT / "hatch_build.py"
BUILD_METADATA_PATH = REPO_ROOT / "policyengine_uk" / "build_metadata.py"
if not HATCH_BUILD_PATH.is_file():
    pytest.skip("hatch_build.py is only in a source checkout", allow_module_level=True)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


hatch_build = _load("policyengine_uk_hatch_build_under_test", HATCH_BUILD_PATH)
build_metadata = _load(
    "policyengine_uk_build_metadata_for_hook_test", BUILD_METADATA_PATH
)

SHA = "0123456789abcdef0123456789abcdef01234567"
OTHER_SHA = "89abcdef0123456789abcdef0123456789abcdef"
BUILD_INFO = "extra_metadata/build_info.json"
# hermetic_git only sets environment variables, so examples may share it.
SUPPRESSED_HEALTH_CHECKS = [HealthCheck.too_slow, HealthCheck.function_scoped_fixture]


@pytest.fixture(autouse=True)
def hermetic_git(monkeypatch):
    # Neither the tests' git calls nor the hook's may be shaped by the
    # user's git configuration or redirected by the caller's environment.
    for key in build_metadata.GIT_REPOSITORY_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(cwd), *args], stderr=subprocess.DEVNULL, text=True
    ).strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        message,
    )
    return _git(repo, "rev-parse", "HEAD")


def _make_project(root: Path) -> str:
    """Create a committed policyengine-uk project at ``root``; return HEAD."""
    package = root / "policyengine_uk"
    (package / "parameters").mkdir(parents=True)
    for name in ("pyproject.toml", ".gitignore", "hatch_build.py"):
        shutil.copyfile(REPO_ROOT / name, root / name)
    shutil.copyfile(BUILD_METADATA_PATH, package / "build_metadata.py")
    (package / "__init__.py").write_text("")
    (package / "parameters" / "rate.yaml").write_text("values:\n  2025-01-01: 0.2\n")
    for name in ("README.md", "LICENSE", "CHANGELOG.md"):
        (root / name).write_text(f"{name}\n")
    _git(root, "init", "-q")
    return _commit(root, str(root))


def _project_version(root: Path) -> str:
    return WheelBuilder(str(root)).metadata.version


def _included_paths(root: Path) -> list[str]:
    return [
        included_file.relative_path
        for included_file in WheelBuilder(str(root)).recurse_included_files()
    ]


def _find_build_commit(root: Path) -> tuple[str | None, str]:
    return hatch_build.find_build_commit(root, _included_paths(root), build_metadata)


def _build_wheel(root: Path, out: Path, version: str = "standard") -> Path:
    [artifact] = WheelBuilder(str(root)).build(directory=str(out), versions=[version])
    return Path(artifact)


def _build_sdist(root: Path, out: Path) -> Path:
    [artifact] = SdistBuilder(str(root)).build(
        directory=str(out), versions=["standard"]
    )
    return Path(artifact)


def _wheel_build_info(wheel: Path) -> dict | None:
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.endswith(BUILD_INFO)]
        if not names:
            return None
        [name] = names
        return json.loads(archive.read(name))


@pytest.fixture
def project(tmp_path) -> tuple[Path, str]:
    root = tmp_path / "policyengine-uk"
    return root, _make_project(root)


# find_build_commit: the commit is recorded only for a clean checkout of
# policyengine-uk whose packaged files are all tracked.


def test_records_head_of_clean_checkout(project):
    root, head = project

    assert _find_build_commit(root) == (head, "")


def test_records_head_beside_files_both_tools_ignore(project):
    # A development tree or CI runner has bytecode, a virtualenv, build
    # output and data files that both git and hatchling ignore.
    root, head = project
    package = root / "policyengine_uk"
    (package / "__pycache__").mkdir()
    (package / "__pycache__" / "build_metadata.cpython-313.pyc").write_bytes(b"pyc")
    (package / "frs_2023.h5").write_bytes(b"data")
    (root / ".venv" / "bin").mkdir(parents=True)
    (root / ".venv" / "bin" / "python").write_text("")
    (root / "dist").mkdir()
    (root / "dist" / "old.whl").write_bytes(b"")

    assert _find_build_commit(root) == (head, "")


def _modify_tracked(root: Path) -> None:
    (root / "policyengine_uk" / "parameters" / "rate.yaml").write_text("changed\n")


def _stage_change(root: Path) -> None:
    _modify_tracked(root)
    _git(root, "add", "-A")


def _staged_then_reverted(root: Path) -> None:
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    original = rate.read_bytes()
    _stage_change(root)
    rate.write_bytes(original)


def _delete_tracked(root: Path) -> None:
    (root / "policyengine_uk" / "parameters" / "rate.yaml").unlink()


def _untracked_in_package(root: Path) -> None:
    (root / "policyengine_uk" / "scratch.py").write_text("x = 1\n")


def _untracked_outside_package(root: Path) -> None:
    (root / "notes.txt").write_text("notes\n")


def _modify_pyproject(root: Path) -> None:
    with (root / "pyproject.toml").open("a") as file:
        file.write("\n# local change\n")


def _ignored_by_info_exclude(root: Path) -> None:
    with (root / ".git" / "info" / "exclude").open("a") as file:
        file.write("*.local\n")
    (root / "policyengine_uk" / "settings.local").write_text("secret\n")


def _ignored_by_excludes_file(root: Path) -> None:
    excludes = root.parent / "global-excludes"
    excludes.write_text("*.local\n")
    _git(root, "config", "core.excludesFile", str(excludes))
    (root / "policyengine_uk" / "settings.local").write_text("secret\n")


def _ignored_by_committed_nested_gitignore(root: Path) -> None:
    (root / "policyengine_uk" / ".gitignore").write_text("*.local\n")
    _commit(root, "nested gitignore")
    (root / "policyengine_uk" / "settings.local").write_text("secret\n")


DIRTY_TREES = {
    "modified tracked file": _modify_tracked,
    "staged change": _stage_change,
    "staged change reverted in the working tree": _staged_then_reverted,
    "deleted tracked file": _delete_tracked,
    "untracked file in the package": _untracked_in_package,
    "untracked file outside the package": _untracked_outside_package,
    "modified pyproject": _modify_pyproject,
    "package file ignored by .git/info/exclude": _ignored_by_info_exclude,
    "package file ignored by core.excludesFile": _ignored_by_excludes_file,
    "package file ignored by a nested .gitignore": (
        _ignored_by_committed_nested_gitignore
    ),
}


@pytest.mark.parametrize("make_dirty", DIRTY_TREES.values(), ids=DIRTY_TREES.keys())
def test_records_nothing_for_dirty_tree(project, make_dirty):
    root, _ = project
    make_dirty(root)

    git_sha, reason = _find_build_commit(root)

    assert git_sha is None
    assert reason


@pytest.mark.skipif(os.name == "nt", reason="needs POSIX file modes")
def test_records_nothing_after_mode_change(project):
    # The wheel records the executable bit, so a mode change alters it.
    root, _ = project
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    rate.chmod(rate.stat().st_mode | stat.S_IXUSR)

    assert _find_build_commit(root)[0] is None


def test_records_nothing_without_git_directory(project):
    # An unpacked sdist.
    root, _ = project
    shutil.rmtree(root / ".git")

    assert _find_build_commit(root)[0] is None


def test_records_nothing_for_another_project(project):
    root, _ = project
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace(
            'name = "policyengine-uk"', 'name = "policyengine-uk-fork"', 1
        )
    )
    _commit(root, "rename")

    assert _find_build_commit(root)[0] is None


def test_records_nothing_for_project_inside_another_repository(tmp_path):
    # For example an sdist unpacked and committed inside a uk-data checkout.
    outer = tmp_path / "policyengine-uk-data"
    root = outer / "vendor" / "policyengine-uk"
    _make_project(root)
    shutil.rmtree(root / ".git")
    _git(outer, "init", "-q")
    _commit(outer, "vendor")

    assert _find_build_commit(root)[0] is None
    # Git skips an empty .git directory and finds the outer repository.
    (root / ".git").mkdir()
    assert _find_build_commit(root)[0] is None


def test_records_nothing_for_unreadable_pyproject(project):
    root, _ = project
    (root / "pyproject.toml").write_text("[project\n")
    _commit(root, "break pyproject")

    git_sha, reason = hatch_build.find_build_commit(
        root, ["policyengine_uk/__init__.py"], build_metadata
    )

    assert git_sha is None
    assert "lookup failed" in reason


def test_ignores_git_environment_overrides(project, tmp_path, monkeypatch):
    root, head = project
    outer = tmp_path / "outer"
    outer.mkdir()
    _git(outer, "init", "-q")
    _commit(outer, "outer")
    # Each would make the checkout look dirty or point git elsewhere.
    monkeypatch.setenv("GIT_DIR", str(outer / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(outer))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "empty-index"))

    assert _find_build_commit(root) == (head, "")


def test_records_nothing_without_git_executable(project, monkeypatch):
    root, _ = project

    def missing_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(hatch_build.subprocess, "run", missing_git)

    assert _find_build_commit(root)[0] is None


def test_records_nothing_when_git_times_out(project, monkeypatch):
    root, _ = project
    timeouts = []

    def slow_git(args, **kwargs):
        timeouts.append(kwargs.get("timeout"))
        raise subprocess.TimeoutExpired(args, kwargs.get("timeout"))

    monkeypatch.setattr(hatch_build.subprocess, "run", slow_git)

    assert _find_build_commit(root)[0] is None
    assert timeouts and all(timeout is not None for timeout in timeouts)


def test_build_metadata_loads_with_the_standard_library_only(tmp_path):
    # hatch_build.py loads build_metadata.py in the build environment, where
    # none of policyengine-uk's dependencies are installed. -S leaves out
    # site-packages.
    probe = (
        "import importlib.util, sys\n"
        "from pathlib import Path\n"
        "spec = importlib.util.spec_from_file_location('probe', sys.argv[1])\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
        "print(module._get_git_sha(Path(sys.argv[2])))\n"
    )

    output = subprocess.check_output(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            probe,
            str(BUILD_METADATA_PATH),
            str(tmp_path / "policyengine_uk"),
        ],
        text=True,
    )

    assert output.strip() == "None"


# The hook inside real hatchling builds.


def test_wheel_records_head(project, tmp_path):
    root, head = project

    wheel = _build_wheel(root, tmp_path / "dist")

    assert _wheel_build_info(wheel) == {
        "git_sha": head,
        "version": _project_version(root),
    }
    with zipfile.ZipFile(wheel) as archive:
        [name] = [name for name in archive.namelist() if name.endswith(BUILD_INFO)]
        assert (
            name == f"policyengine_uk-{_project_version(root)}.dist-info/{BUILD_INFO}"
        )
        assert archive.getinfo(name).external_attr >> 16 & 0o777 == 0o644
        assert name in archive.read(name.replace(BUILD_INFO, "RECORD")).decode()


def test_wheel_from_dirty_tree_records_nothing(project, tmp_path):
    root, _ = project
    _modify_tracked(root)

    assert _wheel_build_info(_build_wheel(root, tmp_path / "dist")) is None


def _initialize_hook(root: Path, out: Path, version: str) -> dict:
    builder = WheelBuilder(str(root))
    hook = hatch_build.BuildInfoHook(
        str(root),
        {"path": "hatch_build.py"},
        builder.config,
        builder.metadata,
        str(out),
        "wheel",
        builder.app,
    )
    build_data = {"extra_metadata": {}}
    hook.initialize(version, build_data)
    recorded = {
        target: json.loads(Path(source).read_text())
        for source, target in build_data["extra_metadata"].items()
    }
    hook.finalize(version, build_data, str(out / "artifact.whl"))
    return recorded


def test_hook_records_head_for_a_standard_wheel(project, tmp_path):
    root, head = project

    assert _initialize_hook(root, tmp_path, "standard") == {
        "build_info.json": {"git_sha": head, "version": _project_version(root)}
    }


def test_hook_records_nothing_for_an_editable_wheel(project, tmp_path):
    # An editable install reads the checkout's HEAD at runtime instead.
    root, _ = project

    assert _initialize_hook(root, tmp_path, "editable") == {}


def test_wheel_built_from_sdist_records_nothing(project, tmp_path):
    root, _ = project
    sdist = _build_sdist(root, tmp_path / "dist")
    with tarfile.open(sdist) as archive:
        names = archive.getnames()
        archive.extractall(tmp_path / "unpacked", filter="data")
    [unpacked] = (tmp_path / "unpacked").iterdir()

    wheel = _build_wheel(unpacked, tmp_path / "dist-from-sdist")

    assert any(name.endswith("/hatch_build.py") for name in names)
    assert not any(name.endswith("build_info.json") for name in names)
    assert _wheel_build_info(wheel) is None


def test_sdist_does_not_depend_on_the_commit(project, tmp_path):
    root, head = project
    first_sdist = _build_sdist(root, tmp_path / "first").read_bytes()
    first_wheel = _wheel_build_info(_build_wheel(root, tmp_path / "first"))
    next_head = _commit(root, "next")

    second_sdist = _build_sdist(root, tmp_path / "second").read_bytes()
    second_wheel = _wheel_build_info(_build_wheel(root, tmp_path / "second"))

    assert first_sdist == second_sdist
    assert first_wheel["git_sha"] == head != next_head == second_wheel["git_sha"]


def test_wheel_build_is_reproducible(project, tmp_path):
    root, _ = project

    first = _build_wheel(root, tmp_path / "first").read_bytes()
    second = _build_wheel(root, tmp_path / "second").read_bytes()

    assert first == second


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def test_build_writes_nothing_into_the_source_tree(project, tmp_path, monkeypatch):
    root, _ = project
    before = _tree_snapshot(root)
    temporary = []
    real_mkdtemp = hatch_build.tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        temporary.append(real_mkdtemp(*args, **kwargs))
        return temporary[-1]

    # hatchling loads its own copy of hatch_build.py, which shares the
    # tempfile module.
    monkeypatch.setattr(hatch_build.tempfile, "mkdtemp", recording_mkdtemp)

    wheel = _build_wheel(root, tmp_path / "dist")

    assert _wheel_build_info(wheel) is not None
    assert _tree_snapshot(root) == before
    assert _git(root, "status", "--porcelain", "--ignored") == ""
    assert temporary and not any(Path(path).exists() for path in temporary)


def test_failed_lookup_records_nothing_and_the_wheel_still_builds(project, tmp_path):
    root, _ = project
    (root / "policyengine_uk" / "build_metadata.py").unlink()
    _commit(root, "drop build_metadata")

    wheel = _build_wheel(root, tmp_path / "dist")

    assert wheel.is_file()
    assert _wheel_build_info(wheel) is None


# Property: whenever the hook records commit S, the wheel is byte-identical to
# the wheel built from a fresh clone of S. A tree with no changes records
# HEAD.


def _add_bytecode(root: Path) -> None:
    cache = root / "policyengine_uk" / "__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "build_metadata.cpython-313.pyc").write_bytes(b"pyc")


def _add_ignored_data(root: Path) -> None:
    (root / "policyengine_uk" / "frs_2023.h5").write_bytes(b"data")


def _commit_change(root: Path) -> None:
    rate = root / "policyengine_uk" / "parameters" / "rate.yaml"
    rate.write_text(rate.read_text() + "  2026-01-01: 0.21\n")
    _commit(root, "change rate")


BENIGN_CHANGES = {
    "bytecode": _add_bytecode,
    "ignored data": _add_ignored_data,
    "new commit": _commit_change,
}
TREE_CHANGES = {**BENIGN_CHANGES, **DIRTY_TREES}


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=SUPPRESSED_HEALTH_CHECKS,
)
@given(changes=st.lists(st.sampled_from(sorted(TREE_CHANGES)), max_size=3))
def test_recorded_commit_rebuilds_the_same_wheel(tmp_path_factory, changes):
    base = tmp_path_factory.mktemp("property")
    root = base / "policyengine-uk"
    _make_project(root)
    for change in changes:
        try:
            TREE_CHANGES[change](root)
        except (FileNotFoundError, FileExistsError):
            # The change no longer applies, for example a second deletion.
            pass

    wheel = _build_wheel(root, base / "dist")
    build_info = _wheel_build_info(wheel)

    if all(change in BENIGN_CHANGES for change in changes):
        assert build_info is not None
        assert build_info["git_sha"] == _git(root, "rev-parse", "HEAD")
    if build_info is not None:
        clone = base / "clone"
        subprocess.check_call(
            ["git", "clone", "-q", "--no-hardlinks", str(root), str(clone)],
            stderr=subprocess.DEVNULL,
        )
        _git(clone, "checkout", "-q", build_info["git_sha"])
        assert (
            wheel.read_bytes() == _build_wheel(clone, base / "dist-clone").read_bytes()
        )


# The runtime reader: _get_git_sha falls back to the recorded commit.

_get_git_sha = build_metadata._get_git_sha
_get_build_info_git_sha = build_metadata._get_build_info_git_sha


def _install(
    site_packages: Path,
    build_info: object = None,
    direct_url: object = None,
    version: str = "2.0.0",
) -> Path:
    """Lay out an installed policyengine-uk with optional dist-info records."""
    package_root = site_packages / "policyengine_uk"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("")
    dist_info = site_packages / f"policyengine_uk-{version}.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: policyengine-uk\nVersion: {version}\n"
    )
    for relative_path, record in (
        (BUILD_INFO, build_info),
        ("direct_url.json", direct_url),
    ):
        if record is not None:
            path = dist_info / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(record if isinstance(record, str) else json.dumps(record))
    return package_root


def test_git_sha_reads_recorded_build_commit(tmp_path):
    package_root = _install(
        tmp_path / "site-packages", {"git_sha": SHA, "version": "2.0.0"}
    )

    assert _get_git_sha(package_root) == SHA


def test_git_sha_reads_recorded_build_commit_inside_another_repository(tmp_path):
    # The policyengine-uk-data layout, installed from PyPI.
    uk_data = tmp_path / "policyengine-uk-data"
    uk_data.mkdir()
    _git(uk_data, "init", "-q")
    _commit(uk_data, "uk-data")
    package_root = _install(
        uk_data / ".venv/lib/python3.13/site-packages",
        {"git_sha": SHA, "version": "2.0.0"},
    )

    assert _get_git_sha(package_root) == SHA


def test_git_sha_prefers_installer_record_to_recorded_build_commit(tmp_path):
    package_root = _install(
        tmp_path / "site-packages",
        build_info={"git_sha": OTHER_SHA, "version": "2.0.0"},
        direct_url={
            "url": "https://example.com",
            "vcs_info": {"vcs": "git", "commit_id": SHA},
        },
    )

    assert _get_git_sha(package_root) == SHA


def test_git_sha_ignores_recorded_build_commit_of_another_copy(tmp_path, monkeypatch):
    other_site_packages = tmp_path / "other-site-packages"
    _install(other_site_packages, {"git_sha": SHA, "version": "2.0.0"})
    monkeypatch.syspath_prepend(str(other_site_packages))
    package_root = _install(tmp_path / "site-packages")

    assert _get_git_sha(package_root) is None


def test_git_sha_ignores_build_info_in_a_source_tree(tmp_path):
    # Only an installed distribution's dist-info is read, never a file that
    # sits in a checkout or source directory.
    root = tmp_path / "src"
    (root / "policyengine_uk").mkdir(parents=True)
    (root / "extra_metadata").mkdir()
    (root / BUILD_INFO).write_text(json.dumps({"git_sha": SHA, "version": "2.0.0"}))

    assert _get_git_sha(root / "policyengine_uk") is None


@pytest.mark.parametrize(
    "build_info",
    [
        "not json",
        [],
        {},
        {"git_sha": SHA},
        {"git_sha": SHA, "version": "1.9.0"},
        {"git_sha": SHA.upper(), "version": "2.0.0"},
        {"git_sha": SHA[:12], "version": "2.0.0"},
        {"git_sha": None, "version": "2.0.0"},
        {"git_sha": SHA, "version": None},
    ],
)
def test_git_sha_ignores_unusable_build_info(tmp_path, build_info):
    package_root = _install(tmp_path / "site-packages", build_info)

    assert _get_git_sha(package_root) is None


JSON_VALUES = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(max_size=8),
    lambda children: (
        st.lists(children, max_size=3)
        | st.dictionaries(st.text(max_size=8), children, max_size=3)
    ),
    max_leaves=8,
)
GIT_SHAS = st.one_of(
    st.text(alphabet="0123456789abcdef", min_size=40, max_size=40),
    st.text(alphabet="0123456789abcdef", min_size=64, max_size=64),
    st.text(alphabet="0123456789abcdefABCDEF", max_size=70),
    JSON_VALUES,
)
BUILD_INFOS = st.one_of(
    JSON_VALUES,
    st.fixed_dictionaries(
        {
            "git_sha": GIT_SHAS,
            "version": st.one_of(
                st.sampled_from(["2.0.0", "2.0", "2.0.1"]), JSON_VALUES
            ),
        }
    ),
)


@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=SUPPRESSED_HEALTH_CHECKS,
)
@given(build_info=BUILD_INFOS)
def test_build_info_property_never_invents_a_sha(tmp_path_factory, build_info):
    package_root = _install(
        tmp_path_factory.mktemp("site-packages"), json.dumps(build_info)
    )
    git_sha = build_info.get("git_sha") if isinstance(build_info, dict) else None
    is_recorded_commit = (
        isinstance(build_info, dict)
        and build_info.get("version") == "2.0.0"
        and isinstance(git_sha, str)
        and len(git_sha) in {40, 64}
        and set(git_sha) <= set("0123456789abcdef")
    )

    assert _get_build_info_git_sha(package_root) == (
        git_sha if is_recorded_commit else None
    )


# Round trip: build a wheel in a temporary policyengine-uk repository,
# install it into a virtualenv inside an unrelated repository, and read the
# commit back with the installed copy's own build_metadata.

ROUND_TRIP_PROBE = """
import importlib.util, json, sys, sysconfig, types
from pathlib import Path

# The wheel is installed without dependencies; stand in for the one that
# get_runtime_metadata calls.
core = types.ModuleType("policyengine_core")
core.get_runtime_metadata = lambda: {"name": "policyengine-core"}
sys.modules["policyengine_core"] = core
path = Path(sysconfig.get_paths()["purelib"], "policyengine_uk", "build_metadata.py")
spec = importlib.util.spec_from_file_location("installed_build_metadata", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
metadata = module.get_runtime_metadata()
print(json.dumps({"path": str(path), "git_sha": metadata["git_sha"],
                  "version": metadata["version"]}))
"""


def _venv_python(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _install_with_pip(environment: Path, wheel: Path) -> None:
    # Symlinks, as `python -m venv` uses on POSIX: a copied interpreter can
    # miss its shared library.
    venv.EnvBuilder(with_pip=True, symlinks=os.name != "nt").create(environment)
    subprocess.check_call(
        [
            str(_venv_python(environment)),
            "-m",
            "pip",
            "install",
            "--quiet",
            "--no-deps",
            "--no-index",
            str(wheel),
        ]
    )


def _install_with_uv(environment: Path, wheel: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is not installed")
    env = {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
    subprocess.check_call(
        [uv, "venv", "--quiet", "--python", sys.executable, str(environment)], env=env
    )
    subprocess.check_call(
        [
            uv,
            "pip",
            "install",
            "--quiet",
            "--offline",
            "--no-deps",
            "--python",
            str(_venv_python(environment)),
            str(wheel),
        ],
        env=env,
    )


@pytest.mark.parametrize("install", [_install_with_pip, _install_with_uv])
def test_built_wheel_round_trip(tmp_path, install):
    root = tmp_path / "policyengine-uk"
    head = _make_project(root)
    wheel = _build_wheel(root, tmp_path / "dist")
    uk_data = tmp_path / "policyengine-uk-data"
    uk_data.mkdir()
    _git(uk_data, "init", "-q")
    uk_data_head = _commit(uk_data, "uk-data")

    install(uk_data / ".venv", wheel)
    output = subprocess.check_output(
        [str(_venv_python(uk_data / ".venv")), "-I", "-c", ROUND_TRIP_PROBE],
        cwd=uk_data,
        text=True,
    )
    result = json.loads(output)

    assert Path(result["path"]).resolve().is_relative_to((uk_data / ".venv").resolve())
    assert result["version"] == _project_version(root)
    assert result["git_sha"] == head
    assert head != uk_data_head
