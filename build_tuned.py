#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李氏三拼3x5a键盘主题处理工具 - 字体微调版
1. 缩小李氏三拼页面的主字体
2. 放大英文26键键盘的主字体
3. 不影响其他小字体（上划字符、注释等）
"""
import zipfile
import os
import shutil
import re

# 配置
KEYBOARD_ZIP = "/projects/.openclaw/media/inbound/E6_9D_8E_E6_B0_8F_E4_B8_89_E6_8B_BC3x5a_E9_94_AE_E7_9B_98_09---bd922eb2-15d6-479a-855e-bc4833c837dd.zip"
OUTPUT_FILE = "/root/.openclaw/李氏三拼3x5a键盘_微调版.hskin"
TEMP_DIR = "/tmp/keyboard_tuned"

# 字体大小调整
PINYIN_MAIN_SCALE = 0.85  # 李氏三拼主字体缩小至 85%
ALPHABETIC_MAIN_SCALE = 1.2  # 英文主字体放大至 120%

def adjust_main_font_only(content, scale):
    """只调整主键字符的字体，不动其他"""
    def replace_main_font(match):
        full_match = match.group(0)
        var_name = match.group(1)
        size_str = match.group(2)
        
        # 只调整主键字符（&zf），不动上划字符（&uhzf）等
        if var_name == 'zf':
            try:
                if 'em' in size_str:
                    value = float(size_str.replace('em', ''))
                    new_value = round(value * scale, 4)
                    return f"主键字符: &zf\n  center:\n    y: 0.8\n  fontSize: {new_value}em"
            except:
                pass
        
        return full_match
    
    # 匹配主键字符配置块
    pattern = r'主键字符: &(\w+)\n(?:.*\n)*?.*fontSize:\s*([\d.]+(?:em)?)'
    return re.sub(pattern, replace_main_font, content, flags=re.MULTILINE)

def clean_font_config(config_path):
    """删除字体配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'fontFace:.*?(?=\n[a-zA-Z_]|\Z)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_keyboard():
    """主处理流程"""
    
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)
    
    print("=" * 60)
    print("李氏三拼3x5a键盘 - 字体微调版")
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
    
    # 删除字体
    fonts_dir = os.path.join(theme_dir, "fonts")
    if os.path.exists(fonts_dir):
        print("\n2. 删除字体文件...")
        shutil.rmtree(fonts_dir)
        print("   ✓ fonts 目录已删除")
    
    # 清理 config.yaml
    config_path = os.path.join(theme_dir, "config.yaml")
    if os.path.exists(config_path):
        print("\n3. 删除字体配置...")
        clean_font_config(config_path)
        print("   ✓ config.yaml 字体配置已删除")
    
    # 调整字体大小
    print("\n4. 调整主字体大小...")
    pinyin_count = 0
    alphabetic_count = 0
    
    for root, dirs, files in os.walk(theme_dir):
        for file in files:
            if not file.endswith('.yaml') or file == 'config.yaml':
                continue
            
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, theme_dir)
            
            is_pinyin = 'pinyin' in file.lower()
            is_alphabetic = 'alphabetic' in file.lower()
            
            if not (is_pinyin or is_alphabetic):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original = content
                
                if is_pinyin:
                    new_content = adjust_main_font_only(content, PINYIN_MAIN_SCALE)
                    if new_content != original:
                        pinyin_count += 1
                        print(f"   ✓ [拼音主字体缩小] {relative_path}")
                elif is_alphabetic:
                    new_content = adjust_main_font_only(content, ALPHABETIC_MAIN_SCALE)
                    if new_content != original:
                        alphabetic_count += 1
                        print(f"   ✓ [英文主字体放大] {relative_path}")
                
                if new_content != original:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
            
            except Exception as e:
                print(f"   ✗ 处理失败 {relative_path}: {e}")
    
    print(f"\n   调整 {pinyin_count} 个拼音布局")
    print(f"   调整 {alphabetic_count} 个英文布局")
    
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
    
    shutil.rmtree(TEMP_DIR)
    
    print("\n" + "=" * 60)
    print("✅ 处理完成！")
    print("=" * 60)
    print("\n调整说明:")
    print(f"  • 李氏三拼主字体缩小至 {int(PINYIN_MAIN_SCALE*100)}%")
    print(f"  • 英文键盘主字体放大至 {int(ALPHABETIC_MAIN_SCALE*100)}%")
    print("  • 上划字符、注释等小字体保持不变")
    print("  • 无字体文件，使用全局字体")
    
    return True

if __name__ == "__main__":
    success = process_keyboard()
    exit(0 if success else 1)
