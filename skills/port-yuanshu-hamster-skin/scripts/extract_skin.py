from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path


def decoded_name(member: zipfile.ZipInfo) -> str:
    name = member.filename
    if member.flag_bits & 0x800:
        return name
    try:
        candidate = name.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name
    return candidate


def safe_extract(source: Path, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    resolved_output = output.resolve()
    with zipfile.ZipFile(source) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"CRC failure: {bad}")
        for member in archive.infolist():
            name = decoded_name(member)
            target = (output / name).resolve()
            if resolved_output != target and resolved_output not in target.parents:
                raise ValueError(f"unsafe archive path: {name}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source_file, target.open("wb") as output_file:
                shutil.copyfileobj(source_file, output_file)

    configs = sorted(output.rglob("config.yaml"))
    if len(configs) != 1:
        raise ValueError(f"expected exactly one config.yaml, found {len(configs)}")
    return configs[0].parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely extract a cskin or hskin archive.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Remove an existing output directory before extraction.",
    )
    args = parser.parse_args()
    source = args.input.resolve()
    output = args.output_dir.resolve()

    if output.exists():
        if not args.replace:
            raise SystemExit(f"output exists; pass --replace to recreate it: {output}")
        if output == output.anchor or len(output.parts) < 3:
            raise SystemExit(f"refusing to remove broad path: {output}")
        shutil.rmtree(output)

    root = safe_extract(source, output)
    print(
        json.dumps(
            {
                "archive": str(source),
                "outputDirectory": str(output),
                "skinRoot": str(root),
                "config": str(root / "config.yaml"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
