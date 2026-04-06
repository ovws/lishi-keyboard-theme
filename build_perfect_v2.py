#!/usr/bin/env python3
import zipfile, os, shutil, re

ZIP_FILE = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
OUTPUT = "/root/.openclaw/李氏三拼3x5a键盘_完美版V2.hskin"
TEMP = "/tmp/kb_final_v2"

if os.path.exists(TEMP):
    shutil.rmtree(TEMP)
os.makedirs(TEMP)

print("解压...")
with zipfile.ZipFile(ZIP_FILE, 'r') as z:
    z.extractall(TEMP)

theme_dir = os.path.join(TEMP, os.listdir(TEMP)[0])

# 删除字体
if os.path.exists(os.path.join(theme_dir, "fonts")):
    shutil.rmtree(os.path.join(theme_dir, "fonts"))

# 删除字体配置
cfg = os.path.join(theme_dir, "config.yaml")
with open(cfg, 'r', encoding='utf-8') as f:
    txt = f.read()
txt = re.sub(r'fontFace:.*?(?=\n[a-zA-Z_]|\Z)', '', txt, flags=re.DOTALL)
txt = re.sub(r'\n\n\n+', '\n\n', txt)
with open(cfg, 'w', encoding='utf-8') as f:
    f.write(txt)

print("调整字体...")

CANDIDATE_KW = ['候选', '工具栏', '列表']
SPACE_KW = ['space前景']

for root, _, files in os.walk(theme_dir):
    for fname in files:
        if not fname.endswith('.yaml') or fname == 'config.yaml':
            continue
        
        fpath = os.path.join(root, fname)
        
        with open(fpath, 'r', encoding='utf-8') as f:
            txt = f.read()
        
        orig = txt
        is_pinyin = 'pinyin' in fname.lower()
        is_alpha = 'alphabetic' in fname.lower()
        is_numeric = 'numeric' in fname.lower()
        
        if is_pinyin or is_numeric:
            # 拼音/数字：逐行处理
            lines = []
            in_cand = False
            in_space = False
            
            for line in txt.split('\n'):
                # 检测块类型
                if any(kw in line for kw in CANDIDATE_KW):
                    in_cand = True
                    in_space = False
                elif any(kw in line for kw in SPACE_KW):
                    in_space = True
                    in_cand = False
                elif line and not line.startswith(' ') and ':' in line:
                    if '&' not in line or 'fontSize' in line:
                        pass
                    else:
                        in_cand = False
                        in_space = False
                
                # 处理 fontSize
                if 'fontSize:' in line and 'em' in line:
                    m = re.search(r'fontSize:\s*([\d.]+)em', line)
                    if m:
                        v = float(m.group(1))
                        if in_cand:
                            # 候选词保持
                            pass
                        elif in_space:
                            # 空格键保持原样
                            pass
                        else:
                            # 按键缩小75%
                            line = re.sub(r'fontSize:\s*[\d.]+em', f'fontSize: {round(v*0.75, 4)}em', line)
                
                lines.append(line)
            
            txt = '\n'.join(lines)
            
            if txt != orig:
                print(f"  {fname} - 拼音/数字")
        
        elif is_alpha:
            # 英文：全部放大120%
            txt = re.sub(r'(fontSize:\s*)([\d.]+)(em)', lambda m: f"{m.group(1)}{round(float(m.group(2))*1.2, 4)}{m.group(3)}", txt)
            if txt != orig:
                print(f"  {fname} - 英文120%")
        
        if txt != orig:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(txt)

print("打包...")
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(theme_dir):
        for f in files:
            fp = os.path.join(root, f)
            z.write(fp, os.path.relpath(fp, TEMP))

shutil.rmtree(TEMP)
print(f"完成！{OUTPUT}")
print("特点：")
print("  • 拼音按键 75%")
print("  • 拼音空格键 100%（保持清晰）")
print("  • 拼音候选词 100%（保持不变）")
print("  • 英文 120%")
