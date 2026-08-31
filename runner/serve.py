#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开放课程的代码运行后端。

网页默认在浏览器里跑 Python，什么都不用装。想用自己机器上的 Python，
或者用远程服务器的 GPU 环境，就跑这个脚本，然后在网页的运行设置里填它的地址。

    python serve.py                     # 监听 127.0.0.1:8760
    python serve.py --port 9000
    python serve.py --host 0.0.0.0      # 只在你信任的内网里这么开

安全须知
    它会执行网页提交过来的任意 Python 代码，等同于在这台机器上开了一个
    命令执行入口。默认只监听 127.0.0.1，也就是只有本机能连。远程机器请用
    SSH 端口转发把它映射到本机，不要直接 --host 0.0.0.0 暴露出去：

        ssh -L 8760:127.0.0.1:8760 用户名@服务器地址

只依赖标准库，不用 pip 装任何东西。
"""
import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import tempfile
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 300
MAX_CODE = 200_000
MAX_OUTPUT = 60_000

_lock = threading.Lock()
CHECKS = {}
MODULES_DIR = None      # 大模型课的练习要 import 这里的从零实现模块

# 跑完之后把 matplotlib 画的图取出来，随输出一起回给网页
CAPTURE = r'''
def __capture():
    import sys
    if "matplotlib" not in sys.modules:
        return
    try:
        import io, base64, matplotlib.pyplot as plt
    except Exception:
        return
    for n in plt.get_fignums():
        b = io.BytesIO()
        try:
            plt.figure(n).savefig(b, format="png", dpi=110, bbox_inches="tight")
        except Exception:
            continue
        print("\n__FIG__" + base64.b64encode(b.getvalue()).decode())
    plt.close("all")
__capture()
'''


def load_checks(path):
    global CHECKS
    for cand in ([path] if path else []) + [
        os.path.join(HERE, "checks.json"),
        os.path.join(HERE, "..", "python", "data", "checks.json"),
    ]:
        if cand and os.path.isfile(cand):
            with open(cand, encoding="utf-8") as f:
                CHECKS = json.load(f)
            return cand
    return None


def load_modules(path):
    global MODULES_DIR
    for cand in ([path] if path else []) + [
        os.path.join(HERE, "pysrc"),
        os.path.join(HERE, "..", "llm", "pysrc"),
    ]:
        if cand and os.path.isdir(cand):
            MODULES_DIR = os.path.abspath(cand)
            return MODULES_DIR
    return None


def clip(text):
    if len(text) <= MAX_OUTPUT:
        return text
    return "…前面省略…\n" + text[-MAX_OUTPUT:]


def run_code(code, stdin_text=""):
    """跑一段代码。返回三样东西：是否正常结束、输出文本、图片列表。"""
    work = os.path.join(tempfile.gettempdir(), "opencourse_%s" % uuid.uuid4().hex)
    os.makedirs(work, exist_ok=True)
    fn = os.path.join(work, "cell.py")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(code + "\n\n" + CAPTURE)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", MPLBACKEND="Agg")
    if MODULES_DIR:
        env["PYTHONPATH"] = MODULES_DIR + os.pathsep + env.get("PYTHONPATH", "")
    try:
        p = subprocess.run([sys.executable, fn], cwd=work, env=env,
                           input=(stdin_text or "").encode("utf-8"),
                           capture_output=True, timeout=TIMEOUT)
        out = p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        text = out + (("\n" + err) if err.strip() else "")
        ok = p.returncode == 0
    except subprocess.TimeoutExpired as e:
        text = (e.stdout.decode("utf-8", "replace") if e.stdout else "")
        text += "\n[超时] 运行超过 %d 秒被终止。写了 while 循环的话，检查一下条件是不是永远为真。" % TIMEOUT
        ok = False
    finally:
        try:
            for root, dirs, files in os.walk(work, topdown=False):
                for x in files:
                    os.remove(os.path.join(root, x))
                for x in dirs:
                    os.rmdir(os.path.join(root, x))
            os.rmdir(work)
        except OSError:
            pass

    figs, lines = [], []
    for line in text.split("\n"):
        if line.startswith("__FIG__"):
            figs.append(line[7:])
        else:
            lines.append(line)
    return ok, clip("\n".join(lines).strip()), figs


def do_check(code, ex_id):
    rule = CHECKS.get(str(ex_id))
    if not code.strip():
        return {"ok": None, "msg": "还没有写代码。"}
    if rule is None:
        return {"ok": None, "msg": "这道题暂时没有自动判定，自己对照预期结果看看。"}
    ok_run, out, _ = run_code(code + "\n\n" + rule.get("append", ""))
    items = [{"desc": d, "pass": needle in out} for d, needle in rule["items"]]
    passed = sum(1 for it in items if it["pass"])
    ok = passed == len(items)
    if ok:
        msg = "全部通过，%d 项检查都对了。" % len(items)
    elif passed == 0 and not ok_run:
        msg = "代码没能跑通，先看下面的报错。"
    else:
        msg = "通过 %d 项，还差 %d 项。" % (passed, len(items) - passed)
    return {"ok": ok, "msg": msg, "items": items, "output": out}


class Handler(BaseHTTPRequestHandler):
    server_version = "OpenCourseRunner/1.0"

    def log_message(self, fmt, *args):
        pass

    def _cors(self):
        origin = self.headers.get("Origin", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        # 浏览器从公网页面连本机地址时要这一条
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Max-Age", "86400")

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/api/env":
            return self._json({
                "python": platform.python_version(),
                "host": socket.gethostname(),
                "platform": platform.platform(terse=True),
                "checks": len(CHECKS),
                "modules": bool(MODULES_DIR),
            })
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._json({"ok": False, "output": "请求内容解析失败，代码要用 UTF-8 提交。"})

        code = data.get("code", "")
        if len(code) > MAX_CODE:
            return self._json({"ok": False, "output": "代码太长了。"})
        if not _lock.acquire(blocking=False):
            return self._json({"ok": False, "output": "正忙：还有一段代码在运行，等它跑完再试。"})
        try:
            if path == "/api/run":
                if not code.strip():
                    return self._json({"ok": False, "output": "没有代码可运行。"})
                ok, out, figs = run_code(code, data.get("stdin", ""))
                return self._json({"ok": ok, "output": out, "figs": figs})
            if path == "/api/check":
                return self._json(do_check(code, data.get("id", "")))
        finally:
            _lock.release()
        self._json({"error": "not found"}, 404)


def main():
    ap = argparse.ArgumentParser(description="开放课程的代码运行后端")
    ap.add_argument("--port", type=int, default=8760)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--checks", default=None)
    ap.add_argument("--modules", default=None)
    args = ap.parse_args()

    found = load_checks(args.checks)
    mods = load_modules(args.modules)
    print("Python %s  %s" % (platform.python_version(), sys.executable))
    print("判定规则 %d 道%s" % (len(CHECKS), ("  %s" % found) if found else "  没找到 checks.json，只能运行不能提交检查"))
    print("从零实现模块 %s" % (mods if mods else "没找到 pysrc，大模型课的练习会 import 失败"))
    if args.host != "127.0.0.1":
        print("注意：正在对外监听 %s，这个端口能执行任意代码，只在信任的网络里这么用。" % args.host)
    print("\n网页运行设置里填：http://127.0.0.1:%d\n" % args.port)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
