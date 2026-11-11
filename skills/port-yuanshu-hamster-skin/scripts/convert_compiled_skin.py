from __future__ import annotations

import argparse
import copy
import json
import shutil
import statistics
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont


LATIN_RANGES = [
    {"location": 32, "length": 95},
    {"location": 160, "length": 96},
    {"location": 256, "length": 336},
    {"location": 592, "length": 96},
    {"location": 768, "length": 112},
]

CJK_RANGES = [
    {"location": 8192, "length": 112},
    {"location": 12288, "length": 64},
    {"location": 12544, "length": 48},
    {"location": 13312, "length": 6592},
    {"location": 19968, "length": 20992},
    {"location": 63744, "length": 512},
    {"location": 65280, "length": 240},
]

UNSUPPORTED_KEYS = {
    "buttonStyleType",
    "hintSymbolsStyle",
    "symbolStyles",
    "selectedBackgroundStyle",
    "preeditStyle",
    "toolbarStyle",
    "toolbarLayout",
    "horizontalCandidatesStyle",
    "horizontalCandidatesLayout",
    "verticalCandidatesStyle",
    "verticalCandidatesLayout",
    "conditionKey",
    "conditionValue",
    "styleName",
    "animationType",
    "shortcut",
    "useRimeEngine",
}

ACTION_SHORTCUT_MAP = {
    "#copy": "#复制",
    "#paste": "#粘贴",
    "#cut": "#剪切",
    "#keyboardMenu": "#方案切换",
}

ACTION_STRING_MAP = {
    "returnLastKeyboard": "returnPrimaryKeyboard",
}

PAGE_ACTION_MAP = {
    "#verticalCandidatesPageDown": "pageDown",
    "#verticalCandidatesPageUp": "pageUp",
    "#subCollectionPageDown": "pageDown",
    "#subCollectionPageUp": "pageUp",
}

ANIMATION_VALUE = [
    {
        "type": "bounds",
        "duration": 60,
        "repeatCount": 1,
        "fromScale": 1,
        "toScale": 0.87,
    },
    {
        "type": "bounds",
        "duration": 80,
        "repeatCount": 1,
        "fromScale": 0.87,
        "toScale": 1,
    },
]


def yaml_load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def yaml_dump(path: Path, value: Any) -> None:
    path.write_text(
        yaml.safe_dump(
            value,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=160,
        ),
        encoding="utf-8",
        newline="\n",
    )


def iter_nodes(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_nodes(child)


def convert_conditional_style(value: list[Any]) -> str | list[Any]:
    if not value or not all(isinstance(item, dict) and "conditionKey" in item for item in value):
        return value
    first_key = value[0].get("conditionKey")
    if first_key == "rime$simplification":
        true_style = next(
            (item.get("styleName") for item in value if item.get("conditionValue") is True),
            "tranStyle",
        )
        false_style = next(
            (item.get("styleName") for item in value if item.get("conditionValue") is False),
            "simpStyle",
        )
        return (
            "// JavaScript\n"
            "function getText() {\n"
            f'  return $getRimeOptionState("simplification") ? "{true_style}" : "{false_style}";\n'
            "}"
        )
    if first_key == "$symbolicKeyboardLockState":
        true_style = next(
            (item.get("styleName") for item in value if item.get("conditionValue") is True),
            "lockButtonForegroundStyle",
        )
        false_style = next(
            (item.get("styleName") for item in value if item.get("conditionValue") is False),
            "unlockButtonForegroundStyle",
        )
        return (
            "// JavaScript\n"
            "function getText() {\n"
            f'  return $symbolicKeyboardLockState ? "{true_style}" : "{false_style}";\n'
            "}"
        )
    return value


def convert_action(value: Any) -> Any:
    if isinstance(value, str):
        return ACTION_STRING_MAP.get(value, value)
    if not isinstance(value, dict):
        return value

    if "openURL" in value and str(value["openURL"]).startswith("hamster3://"):
        return "systemSettings"

    result: dict[str, Any] = {}
    for key, child in value.items():
        new_key = "shortcutCommand" if key == "shortcut" else key
        result[new_key] = convert_action(child)

    shortcut = result.get("shortcutCommand")
    if shortcut in PAGE_ACTION_MAP:
        return PAGE_ACTION_MAP[shortcut]
    if shortcut == "#candidatesBarStateToggle":
        return None
    if shortcut in ACTION_SHORTCUT_MAP:
        result["shortcutCommand"] = ACTION_SHORTCUT_MAP[shortcut]
    return result


def convert_generic(value: Any, parent_key: str | None = None) -> Any:
    if isinstance(value, list):
        conditional = convert_conditional_style(value)
        if isinstance(conditional, str):
            return conditional
        return [convert_generic(item, parent_key) for item in value]

    if not isinstance(value, dict):
        if isinstance(value, str) and value == "$rimeSchemaName":
            return "拼音"
        return value

    if parent_key and (
        parent_key == "action"
        or parent_key.endswith("Action")
        or parent_key in {"actions", "candidateContextMenu"}
    ):
        converted_action = convert_action(value)
        if converted_action is not value:
            if converted_action is None or isinstance(converted_action, str):
                return converted_action
            value = converted_action

    result: dict[str, Any] = {}
    for key, child in value.items():
        if key == "buttonStyleType":
            if child == "geometry":
                result["type"] = "original"
            continue
        if key == "hintSymbolsStyle":
            new_key = "holdSymbolsStyle"
        elif key == "selectedBackgroundStyle":
            new_key = "selectedStyle"
        elif key == "preeditStyle":
            new_key = "preedit"
        elif key == "shortcut":
            new_key = "shortcutCommand"
        elif key == "useRimeEngine":
            continue
        else:
            new_key = key

        if new_key == "animation":
            continue

        converted = convert_generic(child, new_key)
        if converted is None and (
            new_key == "action" or new_key.endswith("Action") or new_key == "actions"
        ):
            continue
        if (
            isinstance(converted, str)
            and converted.startswith("#")
            and "color" in new_key.lower()
        ):
            converted = converted[1:]
        result[new_key] = converted

    if "shortcutCommand" in result:
        shortcut = result["shortcutCommand"]
        if shortcut in PAGE_ACTION_MAP:
            return PAGE_ACTION_MAP[shortcut]
        if shortcut == "#candidatesBarStateToggle":
            return None
        result["shortcutCommand"] = ACTION_SHORTCUT_MAP.get(shortcut, shortcut)

    return result


def extract_cells(layout: Any) -> list[str]:
    cells: list[str] = []
    for node in iter_nodes(layout):
        if isinstance(node, dict) and isinstance(node.get("Cell"), str):
            cells.append(node["Cell"])
    return cells


def synthesize_toolbar(data: dict[str, Any]) -> None:
    if "toolbarStyle" not in data and "horizontalCandidatesStyle" not in data:
        return

    toolbar_style = copy.deepcopy(data.get("toolbarStyle") or {})
    toolbar_cells = extract_cells(data.get("toolbarLayout") or [])

    horizontal_block = data.get("horizontalCandidates") or {}
    candidate_ref = horizontal_block.get("candidateStyle")
    candidate_style = copy.deepcopy(data.get(candidate_ref) or {})
    horizontal_outer = copy.deepcopy(data.get("horizontalCandidatesStyle") or {})
    horizontal_style = candidate_style
    if horizontal_outer.get("insets") is not None:
        horizontal_style["insets"] = horizontal_outer["insets"]
    horizontal_style["candidateStateButtonStyle"] = "expandButton"
    data["horizontalCandidateStyle"] = horizontal_style

    vertical_block = data.get("verticalCandidates") or {}
    vertical_outer = copy.deepcopy(data.get("verticalCandidatesStyle") or {})
    vertical_style: dict[str, Any] = {
        "insets": vertical_outer.get(
            "insets",
            vertical_block.get("insets", {"top": 3, "bottom": 3, "left": 4, "right": 4}),
        ),
        "bottomRowHeight": round(float(data.get("keyboardHeight", 225)) / 5, 1),
        "backgroundStyle": vertical_outer.get(
            "backgroundStyle",
            vertical_block.get("backgroundStyle", "verticalCandidateBackgroundStyle"),
        ),
        "candidateStyle": vertical_block.get(
            "candidateStyle", "verticalCandidateCellStyle"
        ),
        "pageUpButtonStyle": "verticalCandidatePageUpButton",
        "pageDownButtonStyle": "verticalCandidatePageDownButton",
        "returnButtonStyle": "verticalCandidateReturnButton",
        "backspaceButtonStyle": "verticalCandidateBackspaceButton",
    }
    data["verticalCandidateStyle"] = vertical_style

    toolbar: dict[str, Any] = {}
    if toolbar_style.get("backgroundStyle"):
        toolbar["backgroundStyle"] = toolbar_style["backgroundStyle"]
    if toolbar_cells:
        toolbar["primaryButtonStyle"] = toolbar_cells[0]
        toolbar["secondaryButtonStyle"] = list(reversed(toolbar_cells[1:8]))
    toolbar["horizontalCandidateStyle"] = "horizontalCandidateStyle"
    toolbar["verticalCandidateStyle"] = "verticalCandidateStyle"
    if "candidateContextMenu" in data:
        toolbar["candidateContextMenu"] = "candidateContextMenu"
    data["toolbar"] = toolbar

    for key in (
        "toolbarStyle",
        "toolbarLayout",
        "horizontalCandidatesStyle",
        "horizontalCandidatesLayout",
        "horizontalCandidates",
        "verticalCandidatesStyle",
        "verticalCandidatesLayout",
        "verticalCandidates",
    ):
        data.pop(key, None)


def convert_hold_symbols(data: dict[str, Any]) -> None:
    for name, style in list(data.items()):
        if not isinstance(style, dict) or "symbolStyles" not in style:
            continue
        refs = style.pop("symbolStyles")
        foregrounds: list[Any] = []
        actions: list[Any] = []
        for ref in refs:
            item = data.get(ref) or {}
            foregrounds.append(item.get("foregroundStyle"))
            action = convert_action(item.get("action"))
            actions.append(action if action is not None else "space")
        style["foregroundStyle"] = foregrounds
        style["actions"] = actions
        if "selectedBackgroundStyle" in style:
            style["selectedStyle"] = style.pop("selectedBackgroundStyle")
        size = style.pop("size", None)
        if isinstance(size, dict) and "width" in size:
            style["symbolWidth"] = size["width"]


def attach_old_animation(data: dict[str, Any]) -> None:
    used = False
    for name, cell in list(data.items()):
        if not isinstance(cell, dict) or "animation" not in cell:
            continue
        animations = cell.pop("animation")
        if "ButtonScaleAnimation" not in (animations or []):
            continue
        background_ref = cell.get("backgroundStyle")
        if isinstance(background_ref, str) and isinstance(data.get(background_ref), dict):
            data[background_ref]["animation"] = "ButtonScaleAnimation"
            used = True

    for name, value in list(data.items()):
        if isinstance(value, dict) and "animationType" in value:
            data.pop(name)
    if used:
        data["ButtonScaleAnimation"] = copy.deepcopy(ANIMATION_VALUE)


def move_data_sources(data: dict[str, Any]) -> None:
    refs: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "dataSource" and isinstance(child, str):
                    refs.add(child)
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    for value in data.values():
        collect(value)

    moved: dict[str, Any] = {}
    queue = list(refs)
    while queue:
        ref = queue.pop()
        if ref in moved or ref not in data:
            continue
        moved[ref] = data[ref]
        before = set(refs)
        collect(moved[ref])
        queue.extend(refs - before)

    for ref in moved:
        data.pop(ref, None)
    if moved:
        data["dataSource"] = moved


def transform_keyboard(source: Path, destination: Path) -> dict[str, Any]:
    data = yaml_load(source)
    synthesize_toolbar(data)
    convert_hold_symbols(data)
    attach_old_animation(data)
    move_data_sources(data)
    converted = convert_generic(data)
    yaml_dump(destination, converted)
    return converted


def image_rects(descriptor_path: Path) -> dict[str, tuple[int, int, int, int]]:
    descriptor = yaml_load(descriptor_path)
    result: dict[str, tuple[int, int, int, int]] = {}
    for name, value in descriptor.items():
        rect = value["rect"]
        result[name] = (
            int(rect["x"]),
            int(rect["y"]),
            int(rect["width"]),
            int(rect["height"]),
        )
    return result


def dominant_rgba(crop: Image.Image) -> tuple[int, int, int, int]:
    pixels = [p for p in crop.getdata() if p[3] >= 100]
    if not pixels:
        return (255, 255, 255, 255)
    rgb = Counter((p[0], p[1], p[2]) for p in pixels).most_common(1)[0][0]
    alpha_values = [p[3] for p in pixels if (p[0], p[1], p[2]) == rgb]
    return (*rgb, max(180, int(statistics.median(alpha_values or [255]))))


def nontransparent_bbox(crop: Image.Image) -> tuple[int, int, int, int]:
    alpha = crop.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        return bbox
    return (0, 0, crop.width, crop.height)


def fit_font(
    font_path: Path,
    text: str,
    max_width: int,
    max_height: int,
    start_size: int = 70,
) -> ImageFont.FreeTypeFont:
    test_image = Image.new("RGBA", (4, 4))
    test_draw = ImageDraw.Draw(test_image)
    for size in range(start_size, 5, -1):
        font = ImageFont.truetype(str(font_path), size=size)
        bbox = test_draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width and bbox[3] - bbox[1] <= max_height:
            return font
    return ImageFont.truetype(str(font_path), size=6)


def redraw_text_rect(
    atlas: Image.Image,
    rect: tuple[int, int, int, int],
    text: str,
    font_path: Path,
    *,
    color: tuple[int, int, int, int] | None = None,
    target_bbox: tuple[int, int, int, int] | None = None,
) -> None:
    x, y, width, height = rect
    crop = atlas.crop((x, y, x + width, y + height))
    original_bbox = target_bbox or nontransparent_bbox(crop)
    color = color or dominant_rgba(crop)
    atlas.paste((0, 0, 0, 0), (x, y, x + width, y + height))

    if len(text) == 1 and text.isalnum():
        # Narrow glyphs such as I, i, l and 1 must be sized by height. Matching
        # their old width would make them much smaller than the surrounding keys.
        target_width = width - 6
    else:
        target_width = min(
            width - 4, max(8, int((original_bbox[2] - original_bbox[0]) * 1.10))
        )
    target_height = min(height - 4, max(8, int((original_bbox[3] - original_bbox[1]) * 1.08)))
    font = fit_font(font_path, text, target_width, target_height)
    draw = ImageDraw.Draw(atlas)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    center_x = x + (original_bbox[0] + original_bbox[2]) / 2
    center_y = y + (original_bbox[1] + original_bbox[3]) / 2
    draw_x = center_x - text_width / 2 - bbox[0]
    draw_y = center_y - text_height / 2 - bbox[1]
    draw.text((draw_x, draw_y), text, font=font, fill=color)


def rebuild_letter_atlas(
    resources: Path,
    atlas_name: str,
    mapping: dict[int, tuple[str, str]],
    latin_font: Path,
    cjk_font: Path,
) -> None:
    png_path = resources / f"{atlas_name}.png"
    yaml_path = resources / f"{atlas_name}.yaml"
    if not png_path.exists() or not yaml_path.exists():
        return
    atlas = Image.open(png_path).convert("RGBA")
    rects = image_rects(yaml_path)
    for index, (text, font_kind) in mapping.items():
        name = f"IMG{index}"
        if name not in rects:
            continue
        font_path = cjk_font if font_kind == "cjk" else latin_font
        redraw_text_rect(atlas, rects[name], text, font_path)
    atlas.save(png_path)


def rebuild_more_atlas(resources: Path, latin_font: Path, cjk_font: Path) -> None:
    png_path = resources / "more.png"
    yaml_path = resources / "more.yaml"
    if not png_path.exists() or not yaml_path.exists():
        return
    atlas = Image.open(png_path).convert("RGBA")
    rects = image_rects(yaml_path)

    # Pure text cells used on the main keyboard.
    for index, text, font_path in (
        (9, "123", latin_font),
        (24, "分词", cjk_font),
    ):
        if f"IMG{index}" in rects:
            redraw_text_rect(atlas, rects[f"IMG{index}"], text, font_path)

    # IMG20–22 contain SPACE above a microphone/VOICE pill. Keep the microphone
    # artwork and pill, but replace both English labels with TX-02.
    draw = ImageDraw.Draw(atlas)
    for index in (20, 21, 22):
        rect = rects.get(f"IMG{index}")
        if not rect:
            continue
        x, y, width, height = rect
        cell = atlas.crop((x, y, x + width, y + height))

        space_crop = cell.crop((0, 0, width, min(42, height)))
        space_color = dominant_rgba(space_crop)
        atlas.paste((0, 0, 0, 0), (x, y, x + width, y + min(42, height)))
        space_font = fit_font(latin_font, "SPACE", 112, 23, 38)
        bbox = draw.textbbox((0, 0), "SPACE", font=space_font)
        space_center_x = x + 66
        space_center_y = y + 23
        draw.text(
            (
                space_center_x - (bbox[2] - bbox[0]) / 2 - bbox[0],
                space_center_y - (bbox[3] - bbox[1]) / 2 - bbox[1],
            ),
            "SPACE",
            font=space_font,
            fill=space_color,
        )

        pill_sample = atlas.getpixel((x + min(width - 2, 135), y + min(height - 2, 60)))
        if pill_sample[3] < 100:
            pill_sample = (163, 205, 244, 255)
        # Repaint only the inner flat part of the existing rounded pill so its
        # curved boundary and microphone icon remain intact.
        voice_box = (x + 52, y + 46, x + 137, y + 73)
        draw.rectangle(voice_box, fill=pill_sample)
        voice_font = fit_font(
            latin_font,
            "VOICE",
            voice_box[2] - voice_box[0] - 4,
            voice_box[3] - voice_box[1] - 4,
            32,
        )
        bbox = draw.textbbox((0, 0), "VOICE", font=voice_font)
        cx = (voice_box[0] + voice_box[2]) / 2
        cy = (voice_box[1] + voice_box[3]) / 2
        draw.text(
            (
                cx - (bbox[2] - bbox[0]) / 2 - bbox[0],
                cy - (bbox[3] - bbox[1]) / 2 - bbox[1],
            ),
            "VOICE",
            font=voice_font,
            fill=(255, 255, 255, 255),
        )
    atlas.save(png_path)


def rebuild_font_atlases(stage: Path, latin_font: Path, cjk_font: Path) -> None:
    letters = "QWERTYUIOPASDFGHJKLZXCVBNM"
    letter1_mapping: dict[int, tuple[str, str]] = {}
    for offset, char in enumerate(letters, start=1):
        letter1_mapping[offset] = (char, "latin")
        letter1_mapping[offset + 26] = (char.lower(), "latin")
    for offset, group in enumerate(
        ("ABC", "DEF", "GHI", "JKL", "MNO", "PQRS", "TUV", "WXYZ"),
        start=53,
    ):
        letter1_mapping[offset] = (group, "latin")
    for offset, char in enumerate("1234567890", start=62):
        letter1_mapping[offset] = (char, "latin")
    letter1_mapping.update(
        {
            72: (".", "latin"),
            73: ("返回", "cjk"),
            74: ("SPACE", "latin"),
            75: ("!", "latin"),
            81: ("通配", "cjk"),
            82: ("分词", "cjk"),
        }
    )

    letter2_text = [
        "QW",
        "ER",
        "TY",
        "UI",
        "OP",
        "AS",
        "DF",
        "GH",
        "JK",
        "L",
        "ZX",
        "CV",
        "BN",
        "M",
        "Q",
        "WE",
        "RT",
        "Y",
        "U",
        "IO",
        "P",
        "A",
        "SD",
        "FG",
        "H",
        "JK",
        "L",
        "Z",
        "XC",
        "V",
        "BN",
        "M",
    ]
    letter2_mapping = {
        index: (text, "latin") for index, text in enumerate(letter2_text, start=1)
    }

    for mode in ("light", "dark"):
        resources = stage / mode / "resources"
        for atlas in ("letter1", "letter1ax"):
            rebuild_letter_atlas(
                resources, atlas, letter1_mapping, latin_font, cjk_font
            )
        for atlas in ("letter2", "letter2ax"):
            rebuild_letter_atlas(
                resources, atlas, letter2_mapping, latin_font, cjk_font
            )
        rebuild_more_atlas(resources, latin_font, cjk_font)


def copy_resources(source_root: Path, stage: Path) -> None:
    for mode in ("light", "dark"):
        source_resources = source_root / mode / "resources"
        destination = stage / mode / "resources"
        destination.mkdir(parents=True, exist_ok=True)
        for item in source_resources.iterdir():
            if item.is_file() and not item.name.endswith(".bak"):
                shutil.copy2(item, destination / item.name)


def create_resource_aliases(stage: Path) -> None:
    aliases = {
        "more2": "moreax",
        "cand2": "candax",
        "sym2": "symax",
        "letterax": "letter1ax",
    }
    for mode in ("light", "dark"):
        resources = stage / mode / "resources"
        for alias, source in aliases.items():
            for suffix in (".png", ".yaml"):
                source_path = resources / f"{source}{suffix}"
                if source_path.exists():
                    shutil.copy2(source_path, resources / f"{alias}{suffix}")
        shutil.copy2(resources / "bg.png", resources / "bj.png")
        yaml_dump(
            resources / "bj.yaml",
            {
                "IMG2": {
                    "rect": {"x": 0, "y": 195, "width": 1179, "height": 648},
                    "insets": {"top": 0, "bottom": 0, "left": 0, "right": 0},
                }
            },
        )


def build_config(
    source_root: Path,
    stage: Path,
    fonts: list[Path],
    cjk_font: Path,
    skin_name: str,
    author: str,
) -> None:
    source_config = yaml_load(source_root / "config.yaml")
    config: dict[str, Any] = {
        "name": skin_name,
        "author": author,
        "fontFace": [
            {"url": fonts[0].name, "ranges": copy.deepcopy(LATIN_RANGES)},
            {"url": fonts[1].name, "ranges": copy.deepcopy(LATIN_RANGES)},
            {"url": fonts[2].name, "ranges": copy.deepcopy(LATIN_RANGES)},
            {"url": cjk_font.name, "ranges": copy.deepcopy(CJK_RANGES)},
        ],
    }
    for keyboard_type in ("pinyin", "alphabetic", "numeric", "symbolic", "panel"):
        if keyboard_type in source_config:
            config[keyboard_type] = source_config[keyboard_type]
    yaml_dump(stage / "config.yaml", config)


def copy_fonts(stage: Path, fonts: list[Path], cjk_font: Path) -> None:
    destination = stage / "fonts"
    destination.mkdir(parents=True, exist_ok=True)
    for font in [*fonts, cjk_font]:
        shutil.copy2(font, destination / font.name)


def build_demo(source_root: Path, stage: Path) -> None:
    demo = source_root / "demo.png"
    if demo.exists():
        shutil.copy2(demo, stage / "demo.png")


def write_readme(stage: Path, skin_name: str) -> None:
    (stage / "README.md").write_text(
        f"# {skin_name}\n\n"
        "- 从元书 `.cskin` 反向适配为仓输入法 `.hskin`。\n"
        "- 英文字体：用户指定的 TX-02 Regular / Medium / Bold。\n"
        "- 中文字体：用户指定的 CJK 字体。\n"
        "- 保留原皮肤背景顶部的透明渐变，适配新版 iOS 顶部延伸区域。\n"
        "- 已将元书的工具栏、候选栏、长按符号、动画和动作字段转换为仓格式。\n",
        encoding="utf-8",
        newline="\n",
    )


def collect_resource_refs(value: Any) -> set[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    for node in iter_nodes(value):
        if (
            isinstance(node, dict)
            and isinstance(node.get("file"), str)
            and isinstance(node.get("image"), str)
        ):
            refs.add((node["file"], node["image"]))
    return refs


def find_keys(value: Any, forbidden: set[str]) -> set[str]:
    found: set[str] = set()
    for node in iter_nodes(value):
        if isinstance(node, dict):
            found.update(forbidden.intersection(node))
    return found


def validate(stage: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    config = yaml_load(stage / "config.yaml")
    parsed_files = 0
    resource_refs = 0

    for keyboard_type, targets in config.items():
        if keyboard_type in {"name", "author", "fontFace"}:
            continue
        for device in targets.values():
            for filename in device.values():
                for mode in ("light", "dark"):
                    path = stage / mode / f"{filename}.yaml"
                    if not path.exists():
                        errors.append(f"missing keyboard: {mode}/{filename}.yaml")

    for mode in ("light", "dark"):
        resources = stage / mode / "resources"
        for yaml_path in sorted((stage / mode).glob("*.yaml")):
            parsed_files += 1
            data = yaml_load(yaml_path)
            forbidden = find_keys(data, UNSUPPORTED_KEYS)
            if forbidden:
                errors.append(
                    f"{mode}/{yaml_path.name}: unsupported keys {sorted(forbidden)}"
                )
            for node in iter_nodes(data):
                if isinstance(node, dict) and "holdSymbolsStyle" in node:
                    style = data.get(node["holdSymbolsStyle"])
                    if isinstance(style, dict):
                        if len(style.get("foregroundStyle", [])) != len(
                            style.get("actions", [])
                        ):
                            errors.append(
                                f"{mode}/{yaml_path.name}: hold symbol length mismatch"
                            )
                if isinstance(node, dict):
                    for key, child in node.items():
                        if (
                            "color" in key.lower()
                            and isinstance(child, str)
                            and child.startswith("#")
                        ):
                            errors.append(
                                f"{mode}/{yaml_path.name}: color still begins with #"
                            )
            for file_name, image_name in collect_resource_refs(data):
                resource_refs += 1
                png = resources / f"{file_name}.png"
                descriptor = resources / f"{file_name}.yaml"
                if not png.exists() or not descriptor.exists():
                    errors.append(
                        f"{mode}/{yaml_path.name}: missing resource {file_name}"
                    )
                    continue
                descriptor_data = yaml_load(descriptor)
                if image_name not in descriptor_data:
                    errors.append(
                        f"{mode}/{yaml_path.name}: missing image {file_name}/{image_name}"
                    )

        bg = Image.open(resources / "bg.png").convert("RGBA")
        row0 = [bg.getpixel((x, 0))[3] for x in range(bg.width)]
        row120 = [bg.getpixel((x, min(120, bg.height - 1)))[3] for x in range(bg.width)]
        if max(row0) != 0:
            errors.append(f"{mode}/bg.png: top row is not transparent")
        if statistics.median(row120) < 240:
            errors.append(f"{mode}/bg.png: gradient does not become opaque")

    for face in config["fontFace"]:
        font_path = stage / "fonts" / face["url"]
        if not font_path.exists():
            errors.append(f"missing font: {face['url']}")
            continue
        font = TTFont(str(font_path))
        font.close()

    for required in ("config.yaml", "demo.png", "fonts", "light", "dark"):
        if not (stage / required).exists():
            errors.append(f"missing package root item: {required}")

    excluded = [
        path.relative_to(stage).as_posix()
        for path in stage.rglob("*")
        if path.name.startswith(".")
        or path.suffix == ".bak"
        or "jsonnet" in path.parts
    ]
    if excluded:
        errors.append(f"excluded files present: {excluded}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "keyboardYamlFiles": parsed_files,
        "resourceReferencesChecked": resource_refs,
        "fontsChecked": len(config["fontFace"]),
        "topGradientChecked": ["light/resources/bg.png", "dark/resources/bg.png"],
    }


def package(stage: Path, output: Path, wrapper_name: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_STORED,
        allowZip64=False,
    ) as archive:
        wrapper_info = zipfile.ZipInfo(f"{wrapper_name}/")
        wrapper_info.create_system = 0
        wrapper_info.external_attr = 0x10
        wrapper_info.compress_type = zipfile.ZIP_STORED
        archive.writestr(wrapper_info, b"")
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                relative = path.relative_to(stage).as_posix()
                archive_name = f"{wrapper_name}/{relative}"
                if not archive_name.isascii():
                    raise ValueError(f"archive path must be ASCII: {archive_name}")
                info = zipfile.ZipInfo(archive_name)
                info.create_system = 0
                info.external_attr = 0
                info.compress_type = zipfile.ZIP_STORED
                archive.writestr(info, path.read_bytes())


def validate_archive(output: Path, wrapper_name: str) -> dict[str, Any]:
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        roots = sorted({name.split("/", 1)[0] for name in names})
        errors: list[str] = []
        config_path = f"{wrapper_name}/config.yaml"
        if config_path not in names:
            errors.append(f"{config_path} is missing")
        if roots != [wrapper_name]:
            errors.append(f"expected one top-level skin directory, found {roots}")
        if any(name.startswith("/") for name in names):
            errors.append("absolute archive path found")
        if any(
            name.endswith(".bak")
            or "/." in name
            or name.startswith(".")
            or "jsonnet/" in name
            for name in names
        ):
            errors.append("excluded file found in archive")
        return {
            "ok": not errors,
            "errors": errors,
            "files": len(names),
            "rootEntries": roots,
            "compressedBytes": output.stat().st_size,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tx-dir", type=Path, required=True)
    parser.add_argument("--cjk-font", type=Path, required=True)
    parser.add_argument("--skin-name", default="Converted Hamster Skin")
    parser.add_argument("--author", default="Converted with Codex")
    parser.add_argument(
        "--wrapper-name",
        default="Converted-Hamster-Skin",
        help="ASCII-only outer directory name required by Hamster's skin list",
    )
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    stage = args.stage.resolve()
    output = args.output.resolve()
    tx_fonts = [
        args.tx_dir / "TX-02-Regular.otf",
        args.tx_dir / "TX-02-Medium.otf",
        args.tx_dir / "TX-02-Bold.otf",
    ]

    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    if not args.wrapper_name.isascii() or "/" in args.wrapper_name or "\\" in args.wrapper_name:
        raise SystemExit("--wrapper-name must be a single ASCII path component")

    build_config(
        source_root,
        stage,
        tx_fonts,
        args.cjk_font,
        args.skin_name,
        args.author,
    )
    build_demo(source_root, stage)
    copy_fonts(stage, tx_fonts, args.cjk_font)
    copy_resources(source_root, stage)

    converted: list[str] = []
    for mode in ("light", "dark"):
        for source_yaml in sorted((source_root / mode).glob("*.yaml")):
            destination = stage / mode / source_yaml.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            transform_keyboard(source_yaml, destination)
            converted.append(f"{mode}/{source_yaml.name}")

    rebuild_font_atlases(stage, tx_fonts[1], args.cjk_font)
    create_resource_aliases(stage)
    write_readme(stage, args.skin_name)

    validation = validate(stage)
    if not validation["ok"]:
        raise SystemExit(json.dumps(validation, ensure_ascii=False, indent=2))

    package(stage, output, args.wrapper_name)
    archive_validation = validate_archive(output, args.wrapper_name)
    if not archive_validation["ok"]:
        raise SystemExit(json.dumps(archive_validation, ensure_ascii=False, indent=2))

    report = {
        "output": str(output),
        "wrapperName": args.wrapper_name,
        "converted": converted,
        "validation": validation,
        "archive": archive_validation,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
