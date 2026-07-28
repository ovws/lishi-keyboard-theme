# YuanShu v3 to Hamster mapping

Use these mappings when a compiled YuanShu YAML must run in Hamster.

## Top-level regions

| YuanShu v3 | Hamster |
|---|---|
| `preeditStyle` | `preedit` |
| `toolbarStyle` + `toolbarLayout` | `toolbar` |
| `horizontalCandidatesStyle/Layout` | `horizontalCandidateStyle` referenced by `toolbar` |
| `verticalCandidatesStyle/Layout` | `verticalCandidateStyle` referenced by `toolbar` |
| root `candidateContextMenu` | keep root object and reference it from `toolbar` |

For toolbar buttons, use the first layout cell as `primaryButtonStyle`. Hamster's `secondaryButtonStyle` is ordered right-to-left, so reverse the remaining cells.

Build `horizontalCandidateStyle` from the referenced candidate style, outer insets, and `candidateStateButtonStyle: expandButton`.

Build `verticalCandidateStyle` with:

- `insets`
- `bottomRowHeight`
- `backgroundStyle`
- `candidateStyle`
- `pageUpButtonStyle`
- `pageDownButtonStyle`
- `returnButtonStyle`
- `backspaceButtonStyle`

## Button and long-press styles

| YuanShu v3 | Hamster |
|---|---|
| `buttonStyleType: geometry` | `type: original` |
| other `buttonStyleType` values | remove discriminator |
| button `hintSymbolsStyle` | `holdSymbolsStyle` |
| hold style `selectedBackgroundStyle` | `selectedStyle` |
| hold style `size.width` | `symbolWidth` |
| hold style `symbolStyles` | parallel `foregroundStyle` and `actions` arrays |

Resolve each `symbolStyles` reference to its `foregroundStyle` and `action`. Keep the arrays equal in length.

## Actions

Rename object key `shortcut` to `shortcutCommand`.

| YuanShu value | Hamster value |
|---|---|
| `#copy` | `#复制` |
| `#paste` | `#粘贴` |
| `#cut` | `#剪切` |
| `#keyboardMenu` | `#方案切换` |
| `#verticalCandidatesPageDown` | action string `pageDown` |
| `#verticalCandidatesPageUp` | action string `pageUp` |
| `#subCollectionPageDown` | action string `pageDown` |
| `#subCollectionPageUp` | action string `pageUp` |
| `returnLastKeyboard` | `returnPrimaryKeyboard` |

Remove `#candidatesBarStateToggle` from candidate-state buttons; Hamster controls those framework buttons.

Replace YuanShu-only `hamster3://...` Jsonnet editor actions with action string `systemSettings`, or remove them if opening the main app is misleading.

## Conditional styles

Convert the `rime$simplification` condition list to a Hamster JavaScript style reference using `$getRimeOptionState("simplification")`.

Convert `$symbolicKeyboardLockState` condition lists to JavaScript returning the lock or unlock style reference.

Replace unsupported `$rimeSchemaName` labels with a stable text label unless the target Hamster version exposes an equivalent API.

## Animation

Move cell-level YuanShu scale animation to the referenced background style:

```yaml
ButtonScaleAnimation:
  - type: bounds
    duration: 60
    repeatCount: 1
    fromScale: 1
    toScale: 0.87
  - type: bounds
    duration: 80
    repeatCount: 1
    fromScale: 0.87
    toScale: 1
```

Remove YuanShu `animationType` dictionaries and unsupported cartoon/physics definitions unless they have an explicit Hamster equivalent.

## Collections and colors

Move source arrays referenced by collection `dataSource` under a root `dataSource` map. Follow nested `dataSource` references recursively.

Keep supported collection cell types such as `symbols`, `classifiedSymbols`, and `subClassifiedSymbols`. Remove YuanShu-only `useRimeEngine`.

Hamster color fields use hex strings without a leading `#`. Strip it only from fields whose key contains `color`.

## Resource aliases

Some compiled skins reference aliases absent from the archive. For the U/森林集 family:

| Missing name | Copy from |
|---|---|
| `more2` | `moreax` |
| `cand2` | `candax` |
| `sym2` | `symax` |
| `letterax` | rebuilt `letter1ax` |
| `bj` | `bg` image plus a descriptor for the keyboard region |

Validate both the PNG and YAML descriptor, and confirm every referenced image key exists.
