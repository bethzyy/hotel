# 专家团队头脑风暴：代码修改后服务器不刷新问题

## 问题现象
修改 Python 代码后重启服务器，但 API 仍然返回旧的行为（如返回 0 个房型而不是 34 个）。

---

## 专家团队

### 👨‍💻 专家 A：Python 运行时专家
**关注点**：Python 模块加载机制、字节码缓存、import 系统

### 👩‍💻 专家 B：Flask/Web 开发专家
**关注点**：开发服务器机制、热重载、调试模式

### 🧑‍💻 专家 C：DevOps/系统专家
**关注点**：进程管理、端口占用、Windows 特有问题

---

## 头脑风暴会议记录

### 第一轮：问题根因分析

**专家 A（Python 运行时）**：
```
我认为主要问题是 Python 的字节码缓存机制：

1. __pycache__ 目录
   - Python 会将 .py 文件编译成 .pyc 字节码
   - 缓存存在 app/__pycache__/ 和 app/services/__pycache__/
   - 如果源文件时间戳没有变化（快速修改），可能使用旧缓存

2. 模块导入机制
   - Python 模块只导入一次，后续 import 返回已加载的模块
   - Flask 服务器进程不退出时，内存中仍是旧模块
   - 即使文件修改了，已导入的模块不会自动重新加载

3. importlib.reload() 问题
   - 需要手动调用才能重新加载模块
   - 但嵌套导入的模块不会自动重新加载
```

**专家 B（Flask/Web）**：
```
我补充几个 Web 框架层面的问题：

1. Flask 开发服务器不是真正的重启
   - `debug=True` 的热重载只监控入口文件
   - 深层模块（如 app/services/rollinggo.py）修改可能不触发重载

2. 应用上下文问题
   - Flask app 对象在内存中
   - 某些配置和服务在启动时初始化，不会随代码更新

3. 请求级别的缓存
   - 某些数据可能在请求级别被缓存
   - g 对象、session 等可能保留旧状态
```

**专家 C（DevOps/系统）**：
```
从系统角度看，Windows 环境有特殊问题：

1. 端口占用问题（今天遇到的主要问题！）
   - 我们发现 5000 端口有 36 个进程在监听！
   - 新启动的服务器可能连接到旧的进程
   - Windows 的端口复用行为与 Linux 不同

2. 进程管理困难
   - taskkill 有时无法杀掉进程
   - 子进程可能变成孤儿进程
   - Windows 服务管理器不参与

3. 文件系统延迟
   - Windows 文件系统有时有延迟
   - 删除文件后可能仍被占用
   - 网络驱动器更明显
```

---

### 第二轮：问题优先级排序

| 优先级 | 问题 | 影响程度 | 今天是否遇到 |
|--------|------|----------|--------------|
| 🔴 P0 | 多个旧服务器进程占用端口 | 严重 | ✅ 是（36个进程） |
| 🔴 P0 | SQLite 缓存返回旧数据 | 严重 | ✅ 是 |
| 🟡 P1 | __pycache__ 字节码缓存 | 中等 | ⚠️ 可能 |
| 🟡 P1 | Flask 热重载不触发 | 中等 | ⚠️ 可能 |
| 🟢 P2 | 模块导入机制 | 低 | ❓ 不确定 |

---

### 第三轮：解决方案讨论

**专家 A（Python 运行时）的方案**：

```bash
# 方案 A1：启动前清理所有缓存
rm -rf app/__pycache__ app/*/__pycache__

# 方案 A2：设置环境变量禁用字节码缓存
export PYTHONDONTWRITEBYTECODE=1  # Linux/Mac
set PYTHONDONTWRITEBYTECODE=1     # Windows

# 方案 A3：使用 -B 标志
python -B run.py
```

**专家 B（Flask/Web）的方案**：

```python
# 方案 B1：使用 Flask 的 extra_files 监控所有文件
if __name__ == '__main__':
    from werkzeug.serving import run_simple
    # 监控所有 Python 文件
    extra_files = []
    for root, dirs, files in os.walk('app'):
        for f in files:
            if f.endswith('.py'):
                extra_files.append(os.path.join(root, f))
    run_simple('0.0.0.0', 5000, app, use_debugger=True, extra_files=extra_files)

# 方案 B2：使用真正的开发服务器（waitress/gunicorn）
pip install watchdog
watchmedo auto-restart -d . -p "*.py" -- python run.py
```

**专家 C（DevOps/系统）的方案**：

```bash
# 方案 C1：彻底清理脚本（推荐！）
# 创建 restart.sh 或 restart.bat

# === restart.bat (Windows) ===
@echo off
echo [1/4] Stopping all Python processes...
taskkill /F /IM python.exe 2>nul

echo [2/4] Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [3/4] Clearing SQLite cache...
python -c "import sqlite3; c=sqlite3.connect('data/hotel.db'); c.execute('DELETE FROM api_cache'); c.commit()"

echo [4/4] Starting server...
python -u run.py

# === restart.sh (Linux/Mac) ===
#!/bin/bash
echo "[1/4] Stopping all Python processes..."
pkill -f "python.*run.py" 2>/dev/null || true

echo "[2/4] Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "[3/4] Clearing SQLite cache..."
python -c "import sqlite3; c=sqlite3.connect('data/hotel.db'); c.execute('DELETE FROM api_cache'); c.commit()"

echo "[4/4] Starting server..."
python -u run.py
```

---

### 第四轮：最终推荐方案

**三位专家一致同意的最佳实践**：

#### 🎯 短期方案（立即可用）

创建一个 `restart.py` 脚本：

```python
#!/usr/bin/env python
"""
彻底重启服务器脚本
解决：旧进程、字节码缓存、SQLite缓存 三大问题
"""
import os
import sys
import subprocess
import sqlite3
import shutil

def kill_python_processes():
    """杀掉所有 Python 进程"""
    print("[1/4] 停止所有 Python 进程...")
    if sys.platform == 'win32':
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'],
                      capture_output=True)
    else:
        subprocess.run(['pkill', '-f', 'python.*run.py'],
                      capture_output=True)

def clear_pycache():
    """清除所有 __pycache__ 目录"""
    print("[2/4] 清除 Python 字节码缓存...")
    count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                count += 1
            except:
                pass
    print(f"      清除了 {count} 个缓存目录")

def clear_sqlite_cache():
    """清除 SQLite API 缓存"""
    print("[3/4] 清除 SQLite 缓存...")
    db_path = 'data/hotel.db'
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM api_cache')
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            print(f"      清除了 {deleted} 条缓存记录")
        except Exception as e:
            print(f"      警告: {e}")
    else:
        print("      数据库文件不存在，跳过")

def start_server():
    """启动服务器"""
    print("[4/4] 启动服务器...")
    print("-" * 40)
    # 使用 -u 禁用输出缓冲，-B 禁用字节码缓存
    os.execv(sys.executable, [sys.executable, '-u', '-B', 'run.py'])

if __name__ == '__main__':
    print("=" * 40)
    print("彻底重启服务器")
    print("=" * 40)

    kill_python_processes()
    clear_pycache()
    clear_sqlite_cache()
    start_server()
```

#### 🎯 长期方案（架构改进）

1. **使用环境变量控制缓存**
   ```python
   # config.py
   import os

   # 开发环境禁用缓存
   CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'false').lower() == 'true'
   DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
   ```

2. **添加版本号到 API 响应**
   ```python
   # app/__init__.py
   __version__ = "1.2.3"  # 每次修改后更新

   # 路由中返回
   return jsonify({
       'success': True,
       'data': result,
       'version': app.config.get('VERSION', 'unknown')
   })
   ```

3. **使用进程管理工具**
   ```bash
   # 推荐：honcho（跨平台）
   pip install honcho
   honcho start  # 自动管理进程

   # 或：supervisor（生产环境）
   ```

4. **添加健康检查端点**
   ```python
   @app.route('/api/health')
   def health():
       return {
           'status': 'ok',
           'version': __version__,
           'cache_count': get_cache_count()
       }
   ```

---

## 会议总结

### 核心问题
1. **多个旧进程占用端口** - 今天的主要问题
2. **SQLite 缓存** - 今天的主要问题
3. **Python 字节码缓存** - 潜在问题

### 推荐行动
1. ✅ 立即：创建 `restart.py` 脚本
2. ⏳ 短期：添加版本号到 API 响应
3. ⏳ 长期：使用进程管理工具

### 日常开发建议
```bash
# 每次修改代码后，运行：
python restart.py

# 而不是：
python run.py
```

---

**会议结束时间**: 2026-03-21
**参与专家**: Python 运行时专家、Flask/Web 专家、DevOps/系统专家
