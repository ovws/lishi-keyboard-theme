#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李氏三拼3x5a键盘主题处理工具 - TX-02 专用版
正确配置 TX-02 字体
"""
import zipfile
import os
import shutil
import re

# 配置
KEYBOARD_ZIP = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
TX02_FONT = "/projects/.openclaw/media/inbound/TX-02---ad1c6b35-20c0-4e00-a6a8-11823212584d.zip"
OUTPUT_FILE = "/root/.openclaw/李氏三拼3x5a键盘_TX02版.hskin"
TEMP_DIR = "/tmp/keyboard_tx02"

def update_font_config(config_path, tx02_font_file):
    """更新字体配置：只使用 TX-02 字体"""
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除旧的 fontFace 配置
    pattern = r'fontFace:.*?(?=\n[a-zA-Z_]|\Z)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # 添加新的字体配置（只用 TX-02）
    font_config = f"""fontFace:
  - url: {tx02_font_file}

"""
    
    # 在 author: 后插入字体配置
    content = re.sub(
        r'(author:[\s\S]*?\n)',
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
    print("李氏三拼3x5a键盘 - TX-02 专用版")
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
    
    # 删除原字体，添加 TX-02 字体
    print("\n2. 替换为 TX-02 字体...")
    fonts_dir = os.path.join(theme_dir, "fonts")
    
    # 清空 fonts 目录
    if os.path.exists(fonts_dir):
        shutil.rmtree(fonts_dir)
    os.makedirs(fonts_dir)
    
    # 解压 TX-02 字体
    tx02_temp = "/tmp/tx02_extract"
    if os.path.exists(tx02_temp):
        shutil.rmtree(tx02_temp)
    os.makedirs(tx02_temp)
    
    with zipfile.ZipFile(TX02_FONT, 'r') as zip_ref:
        zip_ref.extractall(tx02_temp)
    
    # 查找并复制所有 TX-02 字体文件
    tx02_files = []
    for root, dirs, files in os.walk(tx02_temp):
        for file in files:
            if file.endswith(('.otf', '.ttf')):
                tx02_files.append(os.path.join(root, file))
    
    if not tx02_files:
        print("   ✗ 错误：未找到 TX-02 字体文件")
        return False
    
    # 复制所有字体文件
    copied_fonts = []
    for font_file in tx02_files:
        font_name = os.path.basename(font_file)
        shutil.copy(font_file, os.path.join(fonts_dir, font_name))
        copied_fonts.append(font_name)
        print(f"   ✓ 添加字体: {font_name}")
    
    # 清理临时目录
    shutil.rmtree(tx02_temp)
    
    # 更新字体配置（使用第一个字体文件）
    print("\n3. 更新字体配置...")
    config_path = os.path.join(theme_dir, "config.yaml")
    update_font_config(config_path, copied_fonts[0])
    print(f"   ✓ 主字体: {copied_fonts[0]}")
    
    # 验证
    print("\n4. 验证配置...")
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
        if 'fontFace' in config_content and copied_fonts[0] in config_content:
            print("   ✓ 字体配置正确")
        else:
            print("   ⚠ 警告：字体配置可能有问题")
    
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
    print(f"  • 使用 TX-02 字体系列")
    print(f"  • 包含 {len(copied_fonts)} 个字体文件")
    print("  • 字体配置已正确设置")
    print("  • 文件格式: .hskin")
    
    return True

if __name__ == "__main__":
    success = process_keyboard()
    exit(0 if success else 1)
