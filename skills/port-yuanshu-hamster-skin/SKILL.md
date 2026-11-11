---
name: port-yuanshu-hamster-skin
description: Convert compiled YuanShu input-method skins (`.cskin`) into validated Hamster/仓 skins (`.hskin`), including YuanShu-v3-to-Hamster configuration mapping, custom Latin and CJK font embedding, deterministic rebuilding of baked key-label atlases, modern iOS top-safe-area transparency handling, missing-resource repair, wrapped ZIP packaging, and Code 260 `config.yaml` import diagnosis. Use for cskin/hskin migration, 仓输入法皮肤制作 or repair, keyboard font replacement, iOS top white-strip fixes, or Hamster skin import failures.
---

# Port YuanShu skins to Hamster

Convert a compiled YuanShu skin into a Hamster skin without requiring Jsonnet source. Preserve the visual design, replace live and baked fonts, and produce the single-wrapper archive topology used by Hamster's skin list.

## Required inputs

Collect:

- Source `.cskin`, or an extracted source directory containing one `config.yaml`.
- Latin font directory containing `TX-02-Regular.otf`, `TX-02-Medium.otf`, and `TX-02-Bold.otf`, unless adapting the script for another family.
- CJK `.ttf` or `.otf`.
- Output `.hskin` path and an ASCII-only wrapper name.

Do not copy fonts into the Skill or a public repository. Treat font licensing as the user's responsibility.

## Workflow

1. Inspect the source archive:

   ```powershell
   python scripts/inspect_skin.py "input.cskin"
   ```

2. Extract it safely into a task-local work directory:

   ```powershell
   python scripts/extract_skin.py `
     --input "input.cskin" `
     --output-dir "work/source" `
     --replace
   ```

   Use the reported `skinRoot` as `--source-root`.

3. Ensure Python can import `yaml`, `PIL`, and `fontTools`. Prefer an existing workspace runtime; otherwise install `PyYAML`, `Pillow`, and `fonttools` into a task-local dependency directory.

4. Convert the compiled light/dark YAML, rebuild supported atlases, copy fonts, validate resources, and package:

   ```powershell
   python scripts/convert_compiled_skin.py `
     --source-root "work/source/SkinName" `
     --stage "work/converted-stage" `
     --output "outputs/SkinName-Hamster.hskin" `
     --tx-dir "fonts/TX-02" `
     --cjk-font "fonts/CJK.ttf" `
     --skin-name "Skin Name · 仓" `
     --author "Original author（仓适配）" `
     --wrapper-name "SkinName-Hamster"
   ```

   The wrapper must match `[A-Za-z0-9._-]+`. Keep the displayed `--skin-name` Unicode if desired.

5. Inspect the final archive:

   ```powershell
   python scripts/inspect_skin.py "outputs/SkinName-Hamster.hskin"
   ```

   Require exactly one top-level directory and exactly one config at `<wrapper>/config.yaml`.

6. Visually inspect at least:

   - `light/resources/bg.png` and `dark/resources/bg.png`.
   - Rebuilt `letter1.png`, `letter1ax.png`, `letter2.png`, and `letter2ax.png`.
   - Composite `more.png` labels such as `SPACE` and `VOICE`.

7. Report static validation results and state that actual iOS runtime behavior still requires device testing.

## Non-negotiable packaging rule

Package one outer skin directory:

```text
SkinName-Hamster/
├── config.yaml
├── demo.png
├── fonts/
├── light/
└── dark/
```

Do not put `config.yaml`, `dark/`, `fonts/`, and `light/` directly at ZIP root. Some Hamster versions expose those directories as separate skins and then raise `NSCocoaErrorDomain Code=260` because, for example, `dark/config.yaml` does not exist.

Use ZIP Stored mode, ASCII archive paths, explicit directory entries, and a distinct wrapper name when repairing a failed import.

## iOS top-area handling

Preserve a source `bg.png` whose alpha changes from transparent at the top to opaque below the preedit/toolbar region. Exclude an opaque `.bak` alternative. Validate both light and dark backgrounds:

- Top row alpha maximum equals `0`.
- A lower sample row, typically around pixel 120 for a 1179×860 atlas, is mostly opaque.

Do not add a white fill to compensate for safe-area changes.

## Font handling

- Declare live fonts in root `config.yaml` through `fontFace`.
- Include multiple Latin weights so `fontWeight` can resolve appropriately.
- Give Latin and CJK fonts non-overlapping Unicode ranges where practical.
- Rebuild text baked into PNG atlases; changing `fontFace` alone does not affect image labels.
- Use deterministic Pillow rendering and preserve the original atlas rectangles, dominant colors, alignment centers, microphone icons, and pill shapes.
- Do not use generative image tools for exact glyph atlases.

## Conversion behavior

The bundled converter targets compiled YuanShu v3 skins with `light/`, `dark/`, and `resources/`, including the U/森林集 atlas conventions used during development. It:

- Reconstructs Hamster toolbar and candidate style objects.
- Converts long-press symbol structures and actions.
- Rewrites YuanShu actions and scale animations.
- Moves collection data sources to the Hamster layout.
- Strips leading `#` from color fields.
- Repairs known missing aliases (`more2`, `cand2`, `sym2`, `letterax`, and `bj`).
- Validates every YAML file, font, image descriptor reference, archive path, and background gradient.

Read [references/format-mapping.md](references/format-mapping.md) before changing transformation logic or supporting a different source family. Read [references/troubleshooting.md](references/troubleshooting.md) when import, layout, font, or top-area behavior differs.

## Repackage an existing stage

If conversion is already correct but archive topology is wrong:

```powershell
python scripts/package_wrapped_hskin.py `
  --stage "work/converted-stage" `
  --output "outputs/SkinName-fixed.hskin" `
  --wrapper "SkinName-fixed"
```

Run `inspect_skin.py` afterward and verify the extracted config path.
