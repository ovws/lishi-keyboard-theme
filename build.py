#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李氏三拼3x5a键盘主题处理工具 v3
功能：
1. 添加 TX-02 字体用于英文字母
2. 保留 kafei.ttf 用于特殊符号
3. 放大候选词区域字体（横排、展开）
4. 保持按键字母原始大小
"""
import zipfile
import os
import shutil
import re

# 配置
KEYBOARD_ZIP = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
TX02_FONT = "/projects/.openclaw/media/inbound/TX-02---ad1c6b35-20c0-4e00-a6a8-11823212584d.zip"
OUTPUT_FILE = "/root/.openclaw/李氏三拼3x5a键盘_完美版.hskin"
TEMP_DIR = "/tmp/keyboard_perfect"

# 候选词字体放大系数
CANDIDATE_SCALE = 1.3  # 横排和展开文字放大 30%

def enlarge_candidate_fonts(content, scale):
    """放大候选词相关字体"""
    def replace_anchor(match):
        anchor_label = match.group(1)
        anchor_name = match.group(2)
        size_str = match.group(3)
        
        # 只放大候选词相关字体
        if any(keyword in anchor_label for keyword in ['横排文字', '展开文字', '横排序号', '展开序号']):
            try:
                if 'em' in size_str:
                    value = float(size_str.replace('em', ''))
                    new_value = round(value * scale, 4)
                    print(f"      放大 {anchor_label}: {size_str} -> {new_value}em")
                    return f"{anchor_label}: &{anchor_name} {new_value}em"
            except:
                pass
        
        return match.group(0)
    
    pattern = r'([\u4e00-\u9fa5]+字体大小):\s*&(\w+)\s+([\d.]+(?:em)?)'
    return re.sub(pattern, replace_anchor, content)

def update_font_config(config_path, tx02_font_name):
    """更新字体配置：TX-02 用于英文，kafei.ttf 用于其他"""
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除旧的 fontFace 配置
    pattern = r'fontFace:.*?(?=\n[a-zA-Z_]|\Z)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # 添加新的双字体配置
    font_config = f"""fontFace:
  # TX-02 字体用于英文字母
  - name: {tx02_font_name}
  # kafei 字体用于中文和特殊符号
  - url: kafei.ttf

"""
    
    # 在 name: 后插入字体配置
    content = re.sub(
        r'(name:[\s\S]*?author:[\s\S]*?\n)',
        r'\1' + font_config,
        content,
        count=1
    )
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_keyboard():
    """主处理流程"""
    
    # 清理临时目录
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    
    print("=" * 60)
    print("李氏三拼3x5a键盘主题处理工具 v3")
    print("=" * 60)
    
    # 解压键盘主题
    print("\n1. 解压键盘主题包...")
    with zipfile.ZipFile(KEYBOARD_ZIP, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)
    
    theme_dirs = [d for d in os.listdir(TEMP_DIR) if os.path.isdir(os.path.join(TEMP_DIR, d))]
    if not theme_dirs:
        print("   ✗ 错误：未找到主题目录")
        return False
    
    theme_dir = os.path.join(TEMP_DIR, theme_dirs[0])
    print(f"   ✓ 主题目录: {os.path.basename(theme_dir)}")
    
    # 解压并添加 TX-02 字体
    print("\n2. 添加 TX-02 字体...")
    fonts_dir = os.path.join(theme_dir, "fonts")
    
    tx02_temp = "/tmp/tx02_extract"
    if os.path.exists(tx02_temp):
        shutil.rmtree(tx02_temp)
    os.makedirs(tx02_temp)
    
    with zipfile.ZipFile(TX02_FONT, 'r') as zip_ref:
        zip_ref.extractall(tx02_temp)
    
    # 查找 TX-02 字体文件
    tx02_files = []
    for root, dirs, files in os.walk(tx02_temp):
        for file in files:
            if file.endswith(('.otf', '.ttf')) and 'TX-02' in file or 'Regular' in file:
                tx02_files.append(os.path.join(root, file))
    
    if not tx02_files:
        print("   ✗ 错误：未找到 TX-02 字体文件")
        return False
    
    # 复制 Regular 字体
    tx02_font_file = None
    for font_file in tx02_files:
        if 'Regular' in font_file or 'TX-02-Regular' in font_file:
            tx02_font_file = font_file
            break
    
    if not tx02_font_file:
        tx02_font_file = tx02_files[0]
    
    tx02_font_name = os.path.basename(tx02_font_file)
    shutil.copy(tx02_font_file, os.path.join(fonts_dir, tx02_font_name))
    print(f"   ✓ 添加字体: {tx02_font_name}")
    
    # 清理临时目录
    shutil.rmtree(tx02_temp)
    
    # 更新字体配置
    print("\n3. 更新字体配置...")
    config_path = os.path.join(theme_dir, "config.yaml")
    # 提取字体名称（去掉扩展名）
    font_name_base = os.path.splitext(tx02_font_name)[0]
    update_font_config(config_path, font_name_base)
    print(f"   ✓ 英文字体: {font_name_base}")
    print(f"   ✓ 其他字体: kafei.ttf")
    
    # 放大候选词字体
    print("\n4. 放大候选词区域字体...")
    processed_count = 0
    
    for root, dirs, files in os.walk(theme_dir):
        for file in files:
            if not file.endswith('.yaml') or file == 'config.yaml':
                continue
            
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, theme_dir)
            
            # 处理所有布局文件（主要是中文拼音布局有候选词）
            if 'pinyin' in file.lower() or 'alphabetic' in file.lower():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original = content
                    new_content = enlarge_candidate_fonts(content, CANDIDATE_SCALE)
                    
                    if new_content != original:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        processed_count += 1
                        print(f"   ✓ {relative_path}")
                
                except Exception as e:
                    print(f"   ✗ 处理失败 {relative_path}: {e}")
    
    print(f"\n   共处理 {processed_count} 个布局文件")
    
    # 打包
    print("\n5. 打包为 .hskin 格式...")
    with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(theme_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, TEMP_DIR)
                zipf.write(file_path, arcname)
    
    file_size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"   ✓ 文件大小: {file_size_kb:.1f} KB")
    print(f"   ✓ 输出文件: {OUTPUT_FILE}")
    
    # 清理
    shutil.rmtree(TEMP_DIR)
    
    print("\n" + "=" * 60)
    print("✅ 处理完成！")
    print("=" * 60)
    print("\n优化方案:")
    print(f"  • 英文字母使用 TX-02 字体")
    print(f"  • 特殊符号使用 kafei.ttf 字体")
    print(f"  • 候选词区域字体放大 {int((CANDIDATE_SCALE-1)*100)}%")
    print("  • 按键字母保持原始大小")
    print("  • 文件格式: .hskin")
    
    return True

if __name__ == "__main__":
    success = process_keyboard()
    exit(0 if success else 1)
