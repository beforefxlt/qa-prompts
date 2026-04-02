#!/usr/bin/env python3
"""
Docker 自动构建脚本
自动构建前后端镜像，确保最新代码被打包
用法: python scripts/build_docker.py [--backend] [--frontend] [--all]
"""
import subprocess
import sys
import os
import time

# 从 family_health_record_app/scripts/ 出发
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(SCRIPT_DIR)  # family_health_record_app/
INFRA_DIR = os.path.join(APP_DIR, 'infra')


def run(cmd, cwd=None, check=True):
    print(f"\n>>> {cmd}")
    return subprocess.run(cmd, shell=True, cwd=cwd or INFRA_DIR, check=check)


def check_docker():
    try:
        subprocess.run("docker info", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        print("[FAIL] Docker 未运行，请先启动 Docker Desktop")
        return False


def check_frontend_files():
    """检查前端关键文件是否存在且不是目录"""
    issues = []
    frontend_dir = os.path.join(APP_DIR, 'frontend')
    
    for name in ['next.config.ts', 'tailwind.config.js', 'postcss.config.js', 'tsconfig.json']:
        path = os.path.join(frontend_dir, name)
        if os.path.isdir(path):
            issues.append(f"[FAIL] {name} 是目录而非文件！")
        elif not os.path.exists(path):
            issues.append(f"[FAIL] {name} 不存在！")
    
    return issues


def fix_frontend_files():
    """修复前端文件问题"""
    frontend_dir = os.path.join(APP_DIR, 'frontend')
    fixed = False
    
    # 修复 next.config.ts 如果是目录
    next_config = os.path.join(frontend_dir, 'next.config.ts')
    if os.path.isdir(next_config):
        print("  修复 next.config.ts...")
        subprocess.run(f'rmdir /s /q "{next_config}"', shell=True)
        with open(next_config, 'w', encoding='utf-8') as f:
            f.write('import type { NextConfig } from "next";\n\nconst nextConfig: NextConfig = {};\n\nexport default nextConfig;\n')
        fixed = True
    
    # 修复 tailwind.config 如果是目录
    for name in ['tailwind.config.ts', 'tailwind.config.js']:
        path = os.path.join(frontend_dir, name)
        if os.path.isdir(path):
            print(f"  修复 {name}...")
            subprocess.run(f'rmdir /s /q "{path}"', shell=True)
            fixed = True
    
    # 修复 postcss.config 如果是目录
    for name in ['postcss.config.mjs', 'postcss.config.js']:
        path = os.path.join(frontend_dir, name)
        if os.path.isdir(path):
            print(f"  修复 {name}...")
            subprocess.run(f'rmdir /s /q "{path}"', shell=True)
            fixed = True
    
    # 确保 tailwind.config.js 存在
    tw_path = os.path.join(frontend_dir, 'tailwind.config.js')
    if not os.path.exists(tw_path):
        print("  创建 tailwind.config.js...")
        with open(tw_path, 'w', encoding='utf-8') as f:
            f.write("/** @type {import('tailwindcss').Config} */\nmodule.exports = {\n  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],\n  theme: { extend: {} },\n  plugins: [],\n};\n")
        fixed = True
    
    # 确保 postcss.config.js 存在
    pc_path = os.path.join(frontend_dir, 'postcss.config.js')
    if not os.path.exists(pc_path):
        print("  创建 postcss.config.js...")
        with open(pc_path, 'w', encoding='utf-8') as f:
            f.write("export default {\n  plugins: {\n    tailwindcss: {},\n    autoprefixer: {},\n  },\n};\n")
        fixed = True
    
    return fixed


def build_backend():
    print("\n" + "="*60)
    print(">>> 构建后端镜像 <<<")
    print("="*60)
    
    # 检查 requirements.txt
    req_file = os.path.join(APP_DIR, 'backend', 'requirements.txt')
    with open(req_file, encoding='utf-8') as f:
        content = f.read()
    
    if 'pytest' not in content:
        print("[WARN] requirements.txt 缺少 pytest，自动添加...")
        with open(req_file, 'a', encoding='utf-8') as f:
            f.write('\npytest\npytest-asyncio\n')
    
    run("docker compose build backend --no-cache")
    print("[PASS] 后端镜像构建完成")


def build_frontend():
    print("\n" + "="*60)
    print(">>> 构建前端镜像 <<<")
    print("="*60)
    
    # 检查文件问题
    issues = check_frontend_files()
    if issues:
        for issue in issues:
            print(issue)
        print("\n正在修复...")
        
        if fix_frontend_files():
            print("[PASS] 文件修复完成")
        else:
            print("[FAIL] 文件修复失败")
            return False
    
    run("docker compose build frontend --no-cache")
    print("[PASS] 前端镜像构建完成")
    return True


def main():
    print("\n" + "="*60)
    print(">>> Docker 自动构建脚本 <<<")
    print("="*60)
    
    if not check_docker():
        sys.exit(1)
    
    args = sys.argv[1:]
    build_backend_flag = '--backend' in args or '--all' in args or not args
    build_frontend_flag = '--frontend' in args or '--all' in args or not args
    
    if build_backend_flag:
        try:
            build_backend()
        except subprocess.CalledProcessError as e:
            print(f"\n[FAIL] 后端构建失败: {e}")
            sys.exit(1)
    
    if build_frontend_flag:
        try:
            if not build_frontend():
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"\n[FAIL] 前端构建失败: {e}")
            sys.exit(1)
    
    print("\n" + "="*60)
    print(">>> 构建完成！ <<<")
    print("="*60)
    print(f"\n启动服务: cd {INFRA_DIR} && docker compose up -d")
    print("访问: http://localhost:3001")


if __name__ == "__main__":
    main()
