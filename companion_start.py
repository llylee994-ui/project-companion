# -*- coding: utf-8 -*-
"""Companion launcher — double-click to start/stop/check status."""
import os
import sys
import json
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
HEALTH_URL = "http://127.0.0.1:9599/health"
STATUS_URL = "http://127.0.0.1:9599/status"


def check_daemon():
    try:
        r = json.loads(urllib.request.urlopen(HEALTH_URL, timeout=2).read())
        return r.get("ok", False)
    except Exception:
        return False


def show_status():
    try:
        r = json.loads(urllib.request.urlopen(STATUS_URL, timeout=2).read())
        print(f"状态: {r['status']}")
        for s in r.get("sessions", []):
            print(f"  项目: {s['name']} ({s['state']}, {s['duration']})")
        if not r.get("sessions"):
            print("  (暂无活跃会话)")
    except Exception:
        print("无法获取状态")


def cmd_start():
    if check_daemon():
        print("AI Coding Companion 已在运行")
        show_status()
        input("\n按 Enter 退出...")
        return

    # Find pythonw.exe alongside current python.exe
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pythonw):
        # Fallback: try same dir
        python_dir = os.path.dirname(sys.executable)
        for f in os.listdir(python_dir):
            if f.lower() == "pythonw.exe":
                pythonw = os.path.join(python_dir, f)
                break

    main_py = os.path.join(ROOT, "main.py")

    # Use CREATE_NO_WINDOW to suppress console
    import subprocess
    kwargs = dict(cwd=ROOT)
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    subprocess.Popen([pythonw, main_py], **kwargs)
    print("AI Coding Companion 已启动 (后台静默)")
    print()
    print("查看状态: python companion_start.py status")
    print("停止后台: python companion_start.py stop")
    print()
    input("按 Enter 关闭...")


def cmd_stop():
    if not check_daemon():
        print("未在运行")
        input("\n按 Enter 退出...")
        return

    pid_file = os.path.join(ROOT, ".companion.pid")
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = f.read().strip()
        os.system(f"taskkill /f /pid {pid} >nul 2>&1")
        try:
            os.remove(pid_file)
        except OSError:
            pass
    print("已停止")
    input("\n按 Enter 退出...")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "start"
    if arg == "stop":
        cmd_stop()
    elif arg == "status":
        if check_daemon():
            show_status()
        else:
            print("未运行")
        input("\n按 Enter 退出...")
    else:
        cmd_start()
