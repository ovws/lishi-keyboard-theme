#!/usr/bin/env python3
import zipfile, os, shutil, re

KEYBOARD_ZIP = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
OUTPUT_FILE = "/root/.openclaw/李氏三拼3x5a键盘_精调版.hskin"
TEMP_DIR = "/tmp/kb_final"

PINYIN_SCALE = 0.75
ALPHABETIC_SCALE = 1.2

if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR)

print("解压...")
with zipfile.ZipFile(KEYBOARD_ZIP, 'r') as z:
    z.extractall(TEMP_DIR)

theme_dir = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])

# 删除字体
fonts_dir = os.path.join(theme_dir, "fonts")
if os.path.exists(fonts_dir):
    shutil.rmtree(fonts_dir)

# 删除字体配置
config_path = os.path.join(theme_dir, "config.yaml")
with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'fontFace:.*?(?=\n[a-zA-Z_]|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\n\n\n+', '\n\n', content)
with open(config_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("调整字体...")
for root, dirs, files in os.walk(theme_dir):
    for file in files:
        if not file.endswith('.yaml') or file == 'config.yaml':
            continue
        
        file_path = os.path.join(root, file)
        is_pinyin = 'pinyin' in file.lower()
        is_alphabetic = 'alphabetic' in file.lower()
        
        if not (is_pinyin or is_alphabetic):
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        scale = PINYIN_SCALE if is_pinyin else ALPHABETIC_SCALE
        
        def replace_font(m):
            try:
                v = float(m.group(1).replace('em', ''))
                return f"fontSize: {round(v * scale, 4)}em"
            except:
                return m.group(0)
        
        content = re.sub(r'fontSize:\s*([\d.]+em)', replace_font, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  {file} - {int(scale*100)}%")

print("打包...")
with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(theme_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, TEMP_DIR)
            zipf.write(file_path, arcname)

shutil.rmtree(TEMP_DIR)
print(f"完成！{OUTPUT_FILE}")
print(f"拼音75%, 英文120%")
