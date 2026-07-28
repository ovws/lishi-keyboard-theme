# Troubleshooting

## Code 260: `config.yaml` does not exist

Inspect the skin list and archive topology before editing YAML.

If the list shows entries named `dark`, `fonts`, or `light`, Hamster extracted those directories at its skin-list level and treated each as a skin. Repackage with one outer directory:

```text
SkinName/
  config.yaml
  fonts/
  light/
  dark/
```

Use a new ASCII wrapper name to avoid a failed import directory collision. Delete or ignore the stray `dark`, `fonts`, and `light` skin entries.

Run:

```powershell
python scripts/inspect_skin.py "broken.hskin"
python scripts/package_wrapped_hskin.py --stage "stage" --output "fixed.hskin" --wrapper "SkinName-fixed"
```

## White strip or white block above the keyboard

Inspect `light/resources/bg.png` and `dark/resources/bg.png` alpha:

- Current top row should be fully transparent.
- Alpha should ramp to opaque below the top/preedit region.
- Do not replace the current image with an older opaque `.bak`.

If the archive has a transparent gradient but the device still shows white, request a full keyboard screenshot including the safe area and note device model, orientation, display zoom, and whether inline preedit is enabled.

## Font changed in candidates but not keycaps

The key labels are probably baked into PNG atlases. `fontFace` only affects live text. Rebuild the referenced atlas rectangles and keep descriptor coordinates unchanged.

For narrow glyphs such as `I`, `i`, `l`, and `1`, fit by original height rather than original width; width fitting makes them visibly smaller than neighboring keys.

For composite `SPACE`/`VOICE` images, repaint only text regions. Preserve microphone strokes, the rounded pill boundary, alpha, and highlight variants.

## Missing images although PNG files exist

Each image reference requires:

- `<file>.png`
- `<file>.yaml`
- an image key in that YAML matching the requested `image`

Count and validate references across every light/dark keyboard YAML. Do not assume an atlas file alone is sufficient.

## YAML parses but Hamster layout is broken

Check for YuanShu-only keys:

- `buttonStyleType`
- `hintSymbolsStyle`
- `symbolStyles`
- `selectedBackgroundStyle`
- `preeditStyle`
- `toolbarStyle`
- `toolbarLayout`
- `horizontalCandidatesStyle`
- `horizontalCandidatesLayout`
- `verticalCandidatesStyle`
- `verticalCandidatesLayout`
- `conditionKey`
- `animationType`
- `shortcut`
- `useRimeEngine`

Also verify that toolbar secondary buttons were reversed for Hamster's right-to-left ordering.

## Import works but old broken entries remain

Importing a fixed archive does not necessarily remove directories created by an earlier failed import. Remove the stray entries from Hamster's skin list or file manager, then import the fixed package under a distinct wrapper name.
