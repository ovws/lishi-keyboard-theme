from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path


def inspect(source: Path) -> dict[str, object]:
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        bad = archive.testzip()
        files = [name for name in names if not name.endswith("/")]
        top_level = sorted(
            {name.rstrip("/").split("/", 1)[0] for name in names if name.rstrip("/")}
        )
        configs = [name for name in files if name == "config.yaml" or name.endswith("/config.yaml")]
        ascii_only = all(name.isascii() for name in names)
        compression = sorted({item.compress_type for item in archive.infolist()})

        diagnosis: list[str] = []
        if "config.yaml" in files and len(top_level) > 1:
            diagnosis.append(
                "Root-level config with sibling dark/fonts/light directories may be "
                "misread as several skins by Hamster; package one outer skin directory."
            )
        if len(top_level) == 1 and f"{top_level[0]}/config.yaml" in files:
            diagnosis.append("Single wrapped skin directory detected.")
        if not configs:
            diagnosis.append("No config.yaml exists in the archive.")
        if len(configs) > 1:
            diagnosis.append("Multiple config.yaml files exist; split the skins or choose one.")

        extracted_configs: list[str] = []
        with tempfile.TemporaryDirectory(prefix="skin-inspect-") as temp_dir:
            archive.extractall(temp_dir)
            root = Path(temp_dir)
            extracted_configs = [
                path.relative_to(root).as_posix()
                for path in root.rglob("config.yaml")
                if path.is_file()
            ]

    return {
        "archive": str(source),
        "bytes": source.stat().st_size,
        "crcFailure": bad,
        "entryCount": len(names),
        "topLevelEntries": top_level,
        "configEntries": configs,
        "configsAfterExtraction": extracted_configs,
        "asciiPathsOnly": ascii_only,
        "compressionMethods": compression,
        "diagnosis": diagnosis,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect cskin/hskin archive topology.")
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.archive.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
