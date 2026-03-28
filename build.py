#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李氏三拼3x5a键盘主题处理工具
功能：
1. 删除所有字体文件和字体配置
2. 统一所有布局的字体大小为标准值
3. 打包为 .hskin 格式
"""
import zipfile
import os
import shutil
import re

# 配置
KEYBOARD_ZIP = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
OUTPUT_FILE = "/root/.openclaw/李氏三拼3x5a键盘_统一字体版.hskin"
TEMP_DIR = "/tmp/keyboard_unified"

# 统一字体大小配置（单位：em）
UNIFIED_SIZES = {
    '编码字体大小': 1.0,      # 原 0.8125em
    '横排序号字体大小': 1.0,   # 原 1.125em
    '横排文字字体大小': 1.0,   # 原 1.125em
    '横排注释字体大小': 0.75,  # 原 0.75em
    '展开序号字体大小': 1.0,   # 原 1.0625em
    '展开文字字体大小': 1.0,   # 原 1.0625em
    '展开注释字体大小': 0.7,   # 原 0.6875em
}

def unify_fontsize(content):
    """统一所有 fontSize 为 1em"""
    def replace_size(match):
        # 保持注释相关的字体小一些
        return "fontSize: 1em"
    
    pattern = r'fontSize:\s*([\d.]+(?:em)?)'
    return re.sub(pattern, replace_size, content)

def unify_anchor_fontsize(content):
    """统一锚点定义的字体大小"""
    def replace_anchor(match):
        full_match = match.group(0)
        anchor_label = match.group(1)
        anchor_name = match.group(2)
        
        # 根据配置设置统一大小
        if anchor_label in UNIFIED_SIZES:
            size = UNIFIED_SIZES[anchor_label]
            return f"{anchor_label}: &{anchor_name} {size}em"
        
        # 默认使用 1em
        return f"{anchor_label}: &{anchor_name} 1em"
    
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
    
    # 统一字体大小
    print("\n4. 统一所有布局字体大小...")
    processed_count = 0
    
    for root, dirs, files in os.walk(theme_dir):
        for file in files:
            if not file.endswith('.yaml') or file == 'config.yaml':
                continue
            
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, theme_dir)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 统一字体大小
                new_content = unify_fontsize(content)
                new_content = unify_anchor_fontsize(new_content)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    processed_count += 1
                    print(f"   ✓ {relative_path}")
            
            except Exception as e:
                print(f"   ✗ 处理失败 {relative_path}: {e}")
    
    print(f"\n   共处理 {processed_count} 个布局文件")
    
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
    print("  • 统一所有布局字体大小（英文、中文、数字）")
    print("  • 使用系统默认字体")
    print("  • 文件格式: .hskin")
    
    return True

if __name__ == "__main__":
    success = process_keyboard()
    exit(0 if success else 1)
