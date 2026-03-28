#!/usr/bin/env python3
import zipfile, os, shutil, re

ZIP_FILE = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
OUTPUT = "/root/.openclaw/李氏三拼3x5a键盘_完美版V3.hskin"
TEMP = "/tmp/kb_final_v3"

if os.path.exists(TEMP):
    shutil.rmtree(TEMP)
os.makedirs(TEMP)

print("=" * 60)
print("李氏三拼3x5a键盘 - 完美版 V3")
print("=" * 60)

print("\n1. 解压...")
with zipfile.ZipFile(ZIP_FILE, 'r') as z:
    z.extractall(TEMP)

theme_dir = os.path.join(TEMP, os.listdir(TEMP)[0])
print(f"   ✓ {os.path.basename(theme_dir)}")

# 删除字体
print("\n2. 删除字体文件...")
if os.path.exists(os.path.join(theme_dir, "fonts")):
    shutil.rmtree(os.path.join(theme_dir, "fonts"))
    print("   ✓ fonts/ 已删除")

# 删除字体配置
print("\n3. 删除字体配置...")
cfg = os.path.join(theme_dir, "config.yaml")
with open(cfg, 'r', encoding='utf-8') as f:
    txt = f.read()
txt = re.sub(r'fontFace:.*?(?=\n[a-zA-Z_]|\Z)', '', txt, flags=re.DOTALL)
txt = re.sub(r'\n\n\n+', '\n\n', txt)
with open(cfg, 'w', encoding='utf-8') as f:
    f.write(txt)
print("   ✓ config.yaml 已清理")

print("\n4. 调整字体大小...")

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
        
        if is_pinyin:
            # 拼音：按键75%，候选词和空格键保持100%
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
                        if in_cand or in_space:
                            # 候选词和空格键保持
                            pass
                        else:
                            # 按键缩小75%
                            line = re.sub(r'fontSize:\s*[\d.]+em', f'fontSize: {round(v*0.75, 4)}em', line)
                
                lines.append(line)
            
            txt = '\n'.join(lines)
            
            if txt != orig:
                print(f"   ✓ [拼音] 按键75% 候选/空格100% - {fname}")
        
        elif is_numeric:
            # 数字：按键保持100%（不缩放），候选词保持100%
            # 也就是说，数字键盘全部不缩放
            print(f"   ✓ [数字] 全部保持100% - {fname}")
        
        elif is_alpha:
            # 英文：全部放大120%
            txt = re.sub(r'(fontSize:\s*)([\d.]+)(em)', 
                        lambda m: f"{m.group(1)}{round(float(m.group(2))*1.2, 4)}{m.group(3)}", txt)
            if txt != orig:
                print(f"   ✓ [英文] 120% - {fname}")
        
        if txt != orig:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(txt)

print("\n5. 打包...")
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(theme_dir):
        for f in files:
            fp = os.path.join(root, f)
            z.write(fp, os.path.relpath(fp, TEMP))

shutil.rmtree(TEMP)

file_size = os.path.getsize(OUTPUT) / 1024
print(f"   ✓ {file_size:.1f} KB")

print("\n" + "=" * 60)
print("✅ 完成！")
print("=" * 60)
print("\n特点:")
print("  • 拼音按键 75%")
print("  • 拼音空格键 100%（保持清晰）")
print("  • 拼音候选词 100%（保持不变）")
print("  • 数字按键 100%（不缩小，保持清晰）")
print("  • 数字候选词 100%（与拼音一致）")
print("  • 英文 120%")
print(f"\n输出: {OUTPUT}")
