#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李氏三拼3x5a键盘主题处理工具 v2
功能：
1. 保留原始字体文件（确保特殊符号显示正常）
2. 统一英文字母大小（避免大小不一致）
3. 数字适度放大（提升可读性）
4. 中文保持原样（避免重叠）
"""
import zipfile
import os
import shutil
import re

# 配置
KEYBOARD_ZIP = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
OUTPUT_FILE = "/root/.openclaw/李氏三拼3x5a键盘_最终版.hskin"
TEMP_DIR = "/tmp/keyboard_final"

# 字体大小统一方案
UNIFIED_SIZE = 1.1  # 统一英文为 1.1em（既不太大也不太小）
NUMERIC_SIZE = 1.1  # 数字也统一为 1.1em

def unify_fontsize(content, unified_size):
    """统一所有 fontSize 为指定大小"""
    def replace_size(match):
        return f"fontSize: {unified_size}em"
    
    pattern = r'fontSize:\s*([\d.]+(?:em)?)'
    return re.sub(pattern, replace_size, content)

def unify_anchor_fontsize(content, unified_size):
    """统一锚点定义的字体大小"""
    def replace_anchor(match):
        anchor_label = match.group(1)
        anchor_name = match.group(2)
        # 注释类字体保持较小
        if '注释' in anchor_label:
            size = round(unified_size * 0.7, 2)
        else:
            size = unified_size
        return f"{anchor_label}: &{anchor_name} {size}em"
    
    pattern = r'([\u4e00-\u9fa5]+字体大小):\s*&(\w+)\s+([\d.]+(?:em)?)'
    return re.sub(pattern, replace_anchor, content)

def process_keyboard():
    """主处理流程"""
    
    # 清理临时目录
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    
    print("=" * 60)
    print("李氏三拼3x5a键盘主题处理工具 v2")
    print("=" * 60)
    
    # 解压
    print("\n1. 解压键盘主题包...")
    with zipfile.ZipFile(KEYBOARD_ZIP, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)
    
    theme_dirs = [d for d in os.listdir(TEMP_DIR) if os.path.isdir(os.path.join(TEMP_DIR, d))]
    if not theme_dirs:
        print("   ✗ 错误：未找到主题目录")
        return False
    
    theme_dir = os.path.join(TEMP_DIR, theme_dirs[0])
    print(f"   ✓ 主题目录: {os.path.basename(theme_dir)}")
    
    # 保留字体文件
    fonts_dir = os.path.join(theme_dir, "fonts")
    if os.path.exists(fonts_dir):
        print("\n2. 检查字体文件...")
        font_files = os.listdir(fonts_dir)
        for font_file in font_files:
            print(f"   ✓ 保留字体: {font_file}")
        print("   ✓ 字体文件保留（确保特殊符号正常显示）")
    
    # 处理布局文件
    print("\n3. 统一字体大小...")
    alphabetic_count = 0
    numeric_count = 0
    skipped_count = 0
    
    for root, dirs, files in os.walk(theme_dir):
        for file in files:
            if not file.endswith('.yaml') or file == 'config.yaml':
                continue
            
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, theme_dir)
            
            # 只处理英文和数字布局
            is_alphabetic = 'alphabetic' in file.lower()
            is_numeric = 'numeric' in file.lower()
            
            if not (is_alphabetic or is_numeric):
                skipped_count += 1
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if is_alphabetic:
                    # 统一英文字母大小
                    new_content = unify_fontsize(content, UNIFIED_SIZE)
                    new_content = unify_anchor_fontsize(new_content, UNIFIED_SIZE)
                    alphabetic_count += 1
                    print(f"   ✓ [英文统一{UNIFIED_SIZE}em] {relative_path}")
                elif is_numeric:
                    # 统一数字大小
                    new_content = unify_fontsize(content, NUMERIC_SIZE)
                    new_content = unify_anchor_fontsize(new_content, NUMERIC_SIZE)
                    numeric_count += 1
                    print(f"   ✓ [数字统一{NUMERIC_SIZE}em] {relative_path}")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            except Exception as e:
                print(f"   ✗ 处理失败 {relative_path}: {e}")
    
    print(f"\n   统一 {alphabetic_count} 个英文布局文件")
    print(f"   统一 {numeric_count} 个数字布局文件")
    print(f"   保持 {skipped_count} 个其他布局不变")
    
    # 打包
    print("\n4. 打包为 .hskin 格式...")
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
    print(f"  • 保留原始字体文件（特殊符号正常显示）")
    print(f"  • 英文字母统一为 {UNIFIED_SIZE}em（大小一致）")
    print(f"  • 数字统一为 {NUMERIC_SIZE}em（提升可读性）")
    print("  • 中文、符号、表情保持原样（避免重叠）")
    print("  • 文件格式: .hskin")
    
    return True

if __name__ == "__main__":
    success = process_keyboard()
    exit(0 if success else 1)
