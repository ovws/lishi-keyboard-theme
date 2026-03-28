#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李氏三拼3x5a键盘主题处理工具 - 无字体版
删除所有字体文件和字体配置，使用全局字体
"""
import zipfile
import os
import shutil
import re

# 配置
KEYBOARD_ZIP = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
OUTPUT_FILE = "/root/.openclaw/李氏三拼3x5a键盘_全局字体版.hskin"
TEMP_DIR = "/tmp/keyboard_global_font"

def clean_font_config(config_path):
    """完全删除字体配置"""
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
    print("李氏三拼3x5a键盘 - 全局字体版")
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
    
    # 删除 fonts 目录
    fonts_dir = os.path.join(theme_dir, "fonts")
    if os.path.exists(fonts_dir):
        print("\n2. 删除所有字体文件...")
        shutil.rmtree(fonts_dir)
        print("   ✓ fonts 目录已删除")
    
    # 清理 config.yaml
    config_path = os.path.join(theme_dir, "config.yaml")
    if os.path.exists(config_path):
        print("\n3. 删除所有字体配置...")
        clean_font_config(config_path)
        print("   ✓ config.yaml 字体配置已删除")
    
    # 验证
    print("\n4. 验证...")
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
        if 'fontFace' in config_content or '.ttf' in config_content or '.otf' in config_content:
            print("   ⚠ 警告：可能仍有字体配置残留")
        else:
            print("   ✓ 确认：无任何字体配置")
    
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
    print("\n特点:")
    print("  • 删除所有字体文件")
    print("  • 删除所有字体配置")
    print("  • 使用系统/全局字体")
    print("  • 可通过输入法全局字体设置覆盖")
    print("  • 文件格式: .hskin")
    
    return True

if __name__ == "__main__":
    success = process_keyboard()
    exit(0 if success else 1)
