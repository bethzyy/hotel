#!/usr/bin/env python
"""
彻底重启服务器脚本
解决三大问题：旧进程、字节码缓存、SQLite缓存

使用方法：
    python restart.py           # 完整重启（清理所有缓存）
    python restart.py --quick   # 快速重启（只杀进程，不清理缓存）
    python restart.py --clear-cache  # 只清理缓存，不重启
    python restart.py --status  # 显示状态
"""
import os
import sys
import subprocess
import sqlite3
import shutil
import argparse
import time

DB_PATH = 'data/hotel.db'
DEFAULT_PORT = 5000


def kill_port_processes(port: int = DEFAULT_PORT):
    """杀掉监听指定端口的所有进程"""
    print(f"[1/4] 停止端口 {port} 上的进程...")

    if sys.platform != 'win32':
        result = subprocess.run(
            ['pkill', '-f', f'python.*run.py'],
            capture_output=True
        )
        print("      [OK] 已终止相关进程")
        return

    try:
        # 获取监听端口的进程
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=10
        )

        pids_to_kill = set()
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if parts:
                    try:
                        pid = int(parts[-1])
                        pids_to_kill.add(pid)
                    except (ValueError, IndexError):
                        continue

        if not pids_to_kill:
            print(f"      [--] 端口 {port} 没有运行的进程")
            return

        # 杀掉每个进程
        killed_count = 0
        for pid in pids_to_kill:
            try:
                result = subprocess.run(
                    ['taskkill', '/F', '/PID', str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"      [OK] 已终止进程 {pid}")
                    killed_count += 1
            except Exception as e:
                print(f"      [!] 无法终止进程 {pid}: {e}")

        if killed_count > 0:
            time.sleep(2)  # 等待端口释放

    except Exception as e:
        print(f"      [!] 查找进程失败: {e}")


def kill_all_python_processes():
    """杀掉所有 Python 进程（强制模式）"""
    print("[!] 强制停止所有 Python 进程...")
    if sys.platform == 'win32':
        # Kill all python variants (python.exe, python3.11, etc.)
        killed = False
        for proc_name in ['python.exe', 'python3.11', 'python3.10', 'python3.9']:
            result = subprocess.run(
                ['taskkill', '/F', '/IM', proc_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"      [OK] 已终止 {proc_name} 进程")
                killed = True
        if not killed:
            print("      [--] 没有运行的 Python 进程")
    else:
        result = subprocess.run(
            ['pkill', '-f', 'python.*run.py'],
            capture_output=True
        )
        print("      [OK] 已终止相关进程")


def clear_pycache():
    """清除所有 __pycache__ 目录"""
    print("[2/4] 清除 Python 字节码缓存...")
    count = 0
    for root, dirs, files in os.walk('.'):
        # 跳过虚拟环境和隐藏目录
        if 'venv' in root or '.git' in root or 'node_modules' in root:
            continue
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                count += 1
            except Exception as e:
                print(f"      [!] 无法删除 {cache_dir}: {e}")
    print(f"      [OK] 清除了 {count} 个缓存目录")


def clear_sqlite_cache():
    """清除 SQLite API 缓存"""
    print("[3/4] 清除 SQLite 缓存...")
    if not os.path.exists(DB_PATH):
        print("      [--] 数据库文件不存在，跳过")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_cache'")
        if not cursor.fetchone():
            print("      [--] 缓存表不存在，跳过")
            conn.close()
            return

        cursor.execute('DELETE FROM api_cache')
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"      [OK] 清除了 {deleted} 条缓存记录")
    except Exception as e:
        print(f"      [!] 清理缓存失败: {e}")


def start_server():
    """启动服务器"""
    print("[4/4] 启动服务器...")
    print("-" * 40)

    # 设置环境变量
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # 禁用字节码缓存

    # 使用 exec 替换当前进程，确保环境干净
    # -u: 禁用输出缓冲
    # -B: 不写入字节码缓存
    os.execv(sys.executable, [sys.executable, '-u', '-B', 'run.py'])


def show_status():
    """显示当前状态"""
    print("服务器状态检查")
    print("-" * 40)

    # 检查端口占用
    print(f"端口 {DEFAULT_PORT} 占用情况:")
    if sys.platform == 'win32':
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True
        )
        lines = [l for l in result.stdout.split('\n') if f':{DEFAULT_PORT}' in l and 'LISTENING' in l]
        print(f"  监听进程数: {len(lines)}")
        if lines:
            for line in lines[:3]:
                print(f"  {line.strip()}")
            if len(lines) > 3:
                print(f"  ... 还有 {len(lines) - 3} 个")
    else:
        result = subprocess.run(
            ['lsof', '-i', f':{DEFAULT_PORT}'],
            capture_output=True,
            text=True
        )
        print(result.stdout if result.stdout else "  端口空闲")

    # 检查缓存
    print("\n缓存状态:")
    cache_count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in root:
            cache_count += 1
    print(f"  __pycache__ 目录: {cache_count} 个")

    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM api_cache")
            count = cursor.fetchone()[0]
            print(f"  SQLite 缓存记录: {count} 条")
            conn.close()
        except:
            print("  SQLite: 无法读取")

    print("-" * 40)


def main():
    parser = argparse.ArgumentParser(description='彻底重启 Flask 服务器')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='快速重启（只杀进程，不清理缓存）')
    parser.add_argument('--clear-cache', '-c', action='store_true',
                       help='只清理缓存，不重启')
    parser.add_argument('--status', '-s', action='store_true',
                       help='显示当前状态')
    parser.add_argument('--force', '-f', action='store_true',
                       help='强制重启（杀掉所有 Python 进程）')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
                       help=f'指定端口 (默认: {DEFAULT_PORT})')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    print("=" * 40)
    print("彻底重启服务器")
    print("=" * 40)

    if args.clear_cache:
        # 只清理缓存
        clear_pycache()
        clear_sqlite_cache()
        print("[OK] 缓存清理完成")
        return

    # 停止进程
    if args.force:
        kill_all_python_processes()
    else:
        kill_port_processes(args.port)

    if not args.quick:
        clear_pycache()
        clear_sqlite_cache()
    else:
        print("[2/4] 快速模式，跳过缓存清理")
        print("[3/4] 快速模式，跳过缓存清理")

    start_server()


if __name__ == '__main__':
    main()
