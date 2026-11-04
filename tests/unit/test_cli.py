"""CLI (REQ-CLI-1) — exit codes and error reporting."""

from __future__ import annotations

from pathlib import Path

import pytest

from flyin.cli import main

EASY_01 = Path("maps/easy/01_linear_path.txt")


def test_cli_valid_map_exit_0() -> None:
    """REQ-CLI-1 — a valid map exits 0."""
    assert main([str(EASY_01)]) == 0


def test_cli_bad_args_exit_nonzero() -> None:
    """REQ-CLI-1 — missing/unknown arguments exit non-zero."""
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code != 0
    with pytest.raises(SystemExit) as exc:
        main(["--nope"])
    assert exc.value.code != 0


def test_cli_missing_file_exit_nonzero(capsys: pytest.CaptureFixture[str]) -> None:
    """REQ-ERR-1 — a missing map file reports to stderr and exits non-zero."""
    assert main(["/tmp/does_not_exist_flyin_cli.txt"]) == 1
    assert "error: map file not found" in capsys.readouterr().err


def test_cli_invalid_map_exit_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """REQ-CLI-1 — an invalid map reports the cause to stderr and exits non-zero."""
    bad_map = tmp_path / "bad.txt"
    bad_map.write_text("nb_drones: 0\nstart_hub: start 0 0\nend_hub: goal 1 0\n")
    assert main([str(bad_map)]) == 1
    assert "error: line 1: nb_drones" in capsys.readouterr().err
