#!/usr/bin/env python3
"""Create a derived SQL prediction file with backticks removed."""

from __future__ import annotations

import argparse
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConversionStats:
    """Summary of a completed conversion."""

    removed_backticks: int
    physical_lines: int
    input_bytes: int
    output_bytes: int


def default_output_path(input_path: Path) -> Path:
    """Return the default sibling path for the converted file."""

    return input_path.with_name(
        f"{input_path.stem}_no_backticks{input_path.suffix}"
    )


def _physical_line_count(payload: bytes) -> int:
    return payload.count(b"\n") + int(bool(payload) and not payload.endswith(b"\n"))


def remove_backticks(
    input_path: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
) -> ConversionStats:
    """Remove byte ``0x60`` and atomically write a separate output file."""

    input_path = input_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()

    if not input_path.is_file():
        raise FileNotFoundError(f"input file does not exist: {input_path}")
    if input_path == output_path:
        raise ValueError("output path must differ from the input path")
    if not output_path.parent.is_dir():
        raise NotADirectoryError(
            f"output directory does not exist: {output_path.parent}"
        )
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"output file already exists: {output_path}; pass --force to replace it"
        )

    source = input_path.read_bytes()
    converted = source.replace(b"`", b"")
    physical_lines = _physical_line_count(source)
    if _physical_line_count(converted) != physical_lines:
        raise RuntimeError("line count changed unexpectedly during conversion")

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as temporary_file:
            temporary_file.write(converted)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.chmod(temporary_path, stat.S_IMODE(input_path.stat().st_mode))
        os.replace(temporary_path, output_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise

    return ConversionStats(
        removed_backticks=source.count(b"`"),
        physical_lines=physical_lines,
        input_bytes=len(source),
        output_bytes=len(converted),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Remove backticks from a SQL prediction file without modifying the source."
        )
    )
    parser.add_argument("input", type=Path, help="source SQL prediction file")
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "destination path (default: <input_stem>_no_backticks<input_suffix> "
            "beside the input)"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace the destination if it already exists",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = args.output or default_output_path(args.input)

    try:
        stats = remove_backticks(args.input, output_path, overwrite=args.force)
    except (OSError, RuntimeError, ValueError) as error:
        raise SystemExit(f"error: {error}") from error

    print(f"input={args.input.resolve()}")
    print(f"output={output_path.resolve()}")
    print(f"removed_backticks={stats.removed_backticks}")
    print(f"physical_lines={stats.physical_lines}")
    print(f"bytes={stats.input_bytes}->{stats.output_bytes}")


if __name__ == "__main__":
    main()
