#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李氏三拼3x5a键盘主题处理工具
功能：
1. 删除所有字体文件和字体配置
2. 只调整英文(alphabetic)和数字(numeric)布局的字体大小
3. 中文(pinyin)、符号(symbolic)、表情(emoji)等保持原样
4. 打包为 .hskin 格式
"""
import zipfile
import os
import shutil
import re

# 配置
KEYBOARD_ZIP = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
OUTPUT_FILE = "/root/.openclaw/李氏三拼3x5a键盘_优化版.hskin"
TEMP_DIR = "/tmp/keyboard_optimized"

# 字体大小调整系数（只用于英文和数字）
ALPHABETIC_SCALE = 1.2   # 英文放大 20%
NUMERIC_SCALE = 1.2      # 数字放大 20%

def adjust_fontsize(content, scale):
    """调整 fontSize 值"""
    def replace_size(match):
        size_str = match.group(1)
        try:
            if 'em' in size_str:
                value = float(size_str.replace('em', ''))
                new_value = round(value * scale, 4)
                return f"fontSize: {new_value}em"
            else:
                value = float(size_str)
                new_value = round(value * scale, 4)
                return f"fontSize: {new_value}em"
        except:
            return match.group(0)
    
    pattern = r'fontSize:\s*([\d.]+(?:em)?)'
    return re.sub(pattern, replace_size, content)

def adjust_anchor_fontsize(content, scale):
    """调整锚点定义的字体大小"""
    def replace_anchor(match):
        anchor_label = match.group(1)
        anchor_name = match.group(2)
        size_str = match.group(3)
        try:
            if 'em' in size_str:
                value = float(size_str.replace('em', ''))
                new_value = round(value * scale, 4)
                return f"{anchor_label}: &{anchor_name} {new_value}em"
            else:
                value = float(size_str)
                new_value = round(value * scale, 4)
                return f"{anchor_label}: &{anchor_name} {new_value}em"
        except:
            return match.group(0)
    
    pattern = r'([\u4e00-\u9fa5]+字体大小):\s*&(\w+)\s+([\d.]+(?:em)?)'
    return re.sub(pattern, replace_anchor, content)

def clean_font_config(config_path):
    """删除 config.yaml 中的所有字体配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除 fontFace 段落
    pattern = r'fontFace:.*?(?=\n[a-zA-Z_]|\Z)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # 清理多余空行
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_keyboard():
    """主处理流程"""
    
    # 清理临时目录
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    
    print("=" * 60)
    print("李氏三拼3x5a键盘主题处理工具")
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
    
    # 删除字体文件
    fonts_dir = os.path.join(theme_dir, "fonts")
    if os.path.exists(fonts_dir):
        print("\n2. 删除字体文件...")
        font_files = os.listdir(fonts_dir)
        for font_file in font_files:
            print(f"   - {font_file}")
        shutil.rmtree(fonts_dir)
        print("   ✓ fonts 目录已删除")
    else:
        print("\n2. 未找到 fonts 目录（已删除）")
    
    # 清理 config.yaml
    config_path = os.path.join(theme_dir, "config.yaml")
    if os.path.exists(config_path):
        print("\n3. 清理 config.yaml 字体配置...")
        clean_font_config(config_path)
        print("   ✓ 已删除所有字体配置")
    
    # 只调整英文和数字的字体大小
    print("\n4. 调整英文和数字布局字体大小...")
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
                    # 英文字体放大
                    new_content = adjust_fontsize(content, ALPHABETIC_SCALE)
                    new_content = adjust_anchor_fontsize(new_content, ALPHABETIC_SCALE)
                    alphabetic_count += 1
                    print(f"   ✓ [英文放大120%] {relative_path}")
                elif is_numeric:
                    # 数字字体放大
                    new_content = adjust_fontsize(content, NUMERIC_SCALE)
                    new_content = adjust_anchor_fontsize(new_content, NUMERIC_SCALE)
                    numeric_count += 1
                    print(f"   ✓ [数字放大120%] {relative_path}")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            except Exception as e:
                print(f"   ✗ 处理失败 {relative_path}: {e}")
    
    print(f"\n   调整 {alphabetic_count} 个英文布局文件")
    print(f"   调整 {numeric_count} 个数字布局文件")
    print(f"   保持 {skipped_count} 个其他布局文件不变（中文、符号、表情等）")
    
    # 验证
    print("\n5. 验证配置...")
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
        if 'fontFace' in config_content or '.ttf' in config_content or '.otf' in config_content:
            print("   ⚠ 警告：可能仍有字体相关配置残留")
            return False
        else:
            print("   ✓ 确认：无任何字体配置残留")
    
    # 打包
    print("\n6. 打包为 .hskin 格式...")
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
    print("\n特性:")
    print("  • 删除所有字体文件和字体配置")
    print("  • 英文布局字体放大 120%（避免字母太小）")
    print("  • 数字布局字体放大 120%（避免数字太小）")
    print("  • 中文、符号、表情等保持原始大小（避免重叠）")
    print("  • 使用系统默认字体")
    print("  • 文件格式: .hskin")
    
    return True

if __name__ == "__main__":
    success = process_keyboard()
    exit(0 if success else 1)
