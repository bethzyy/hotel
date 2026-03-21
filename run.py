"""
Hotel Search Application Entry Point
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))


def kill_port_processes(port: int) -> bool:
    """
    Kill all processes listening on the specified port.
    Returns True if any process was killed.
    """
    killed = False

    if sys.platform == 'win32':
        try:
            # Find processes on the port
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

            # Kill each process
            for pid in pids_to_kill:
                try:
                    subprocess.run(
                        ['taskkill', '/F', '/PID', str(pid)],
                        capture_output=True,
                        timeout=5
                    )
                    print(f"[Startup] Killed process {pid} on port {port}")
                    killed = True
                except Exception as e:
                    print(f"[Startup] Failed to kill process {pid}: {e}")

            if killed:
                time.sleep(1)  # Wait for ports to be released

        except Exception as e:
            print(f"[Startup] Error finding/killing processes: {e}")

    return killed


def clear_pycache():
    """Clear Python bytecode cache."""
    import shutil
    count = 0
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and hidden directories
        if 'venv' in root or '.git' in root or 'node_modules' in root:
            continue
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                count += 1
            except Exception:
                pass
    if count > 0:
        print(f"[Startup] Cleared {count} __pycache__ directories")


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))

    # Kill any existing processes on this port
    kill_port_processes(port)

    # Clear Python cache
    clear_pycache()

    # Load environment variables from .env file BEFORE importing config
    from dotenv import load_dotenv
    load_dotenv()

    from app import create_app

    app = create_app()

    print(f"[Startup] Starting server on port {port}...")
    print(f"[Startup] Visit http://localhost:{port}")

    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', True),
        use_reloader=False  # 禁用 Watchdog 防止频繁重启导致 ERR_CONNECTION_RESET
    )
