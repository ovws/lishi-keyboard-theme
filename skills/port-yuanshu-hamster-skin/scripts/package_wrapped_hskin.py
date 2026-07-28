from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path


def zip_info(name: str, *, directory: bool = False) -> zipfile.ZipInfo:
    if directory and not name.endswith("/"):
        name += "/"
    info = zipfile.ZipInfo(name)
    info.create_system = 0
    info.external_attr = 0x10 if directory else 0
    info.compress_type = zipfile.ZIP_STORED
    return info


def package(stage: Path, output: Path, wrapper: str) -> dict[str, object]:
    if not stage.is_dir() or not (stage / "config.yaml").is_file():
        raise ValueError(f"stage must contain config.yaml: {stage}")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", wrapper):
        raise ValueError("wrapper must contain ASCII letters, digits, dot, underscore, or hyphen")

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    directories = sorted(
        [path for path in stage.rglob("*") if path.is_dir()],
        key=lambda path: path.relative_to(stage).as_posix(),
    )
    files = sorted(
        [path for path in stage.rglob("*") if path.is_file()],
        key=lambda path: (
            0 if path.relative_to(stage).as_posix() == "config.yaml" else 1,
            path.relative_to(stage).as_posix(),
        ),
    )

    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_STORED,
        allowZip64=False,
    ) as archive:
        archive.writestr(zip_info(wrapper, directory=True), b"")
        for directory in directories:
            relative = directory.relative_to(stage).as_posix()
            archive.writestr(zip_info(f"{wrapper}/{relative}", directory=True), b"")
        for path in files:
            relative = path.relative_to(stage).as_posix()
            archive_name = f"{wrapper}/{relative}"
            if not archive_name.isascii():
                raise ValueError(f"archive path must be ASCII: {archive_name}")
            archive.writestr(zip_info(archive_name), path.read_bytes())

    with tempfile.TemporaryDirectory(prefix="hskin-verify-") as temp_dir:
        verify_root = Path(temp_dir)
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            bad = archive.testzip()
            archive.extractall(verify_root)
        extracted_config = verify_root / wrapper / "config.yaml"
        top_level = sorted(
            {name.rstrip("/").split("/", 1)[0] for name in names if name.rstrip("/")}
        )
        if bad is not None:
            raise ValueError(f"CRC failure: {bad}")
        if top_level != [wrapper]:
            raise ValueError(f"expected one top-level directory, found: {top_level}")
        if not extracted_config.is_file():
            raise ValueError("config.yaml missing after independent extraction")

    return {
        "output": str(output),
        "bytes": output.stat().st_size,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest().upper(),
        "entryCount": len(names),
        "singleTopLevelDirectory": top_level,
        "configPath": f"{wrapper}/config.yaml",
        "asciiPathsOnly": all(name.isascii() for name in names),
        "compression": "stored",
        "extractionVerified": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Package a converted Hamster skin directory as an iOS-compatible .hskin."
    )
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wrapper", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            package(args.stage.resolve(), args.output.resolve(), args.wrapper),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
