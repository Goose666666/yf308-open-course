#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把运行后端装到远程服务器上跑，并把它的端口映射到本机。

    pip install paramiko
    python connect_server.py --host 10.16.13.145 --user liutianrui

跑起来之后在网页的运行设置里填 http://127.0.0.1:8760，代码就在服务器上执行。
按 Ctrl+C 结束，会顺手把服务器上的进程关掉。

走 SSH 端口转发而不是让服务器直接对外监听，一是浏览器只信任本机地址，
二是这个端口能执行任意代码，不该暴露在网络上。
"""
import argparse
import os
import select
import socket
import socketserver
import sys
import threading
import time

try:
    import paramiko
except ImportError:
    sys.exit("先装 paramiko：pip install paramiko")

HERE = os.path.dirname(os.path.abspath(__file__))


class ForwardHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel(
                "direct-tcpip", (self.remote_host, self.remote_port), self.request.getpeername())
        except Exception:
            return
        if chan is None:
            return
        try:
            while True:
                r, _, _ = select.select([self.request, chan], [], [], 1)
                if self.request in r:
                    data = self.request.recv(16384)
                    if not data:
                        break
                    chan.sendall(data)
                if chan in r:
                    data = chan.recv(16384)
                    if not data:
                        break
                    self.request.sendall(data)
        except (OSError, socket.error):
            pass
        finally:
            chan.close()
            self.request.close()


def start_tunnel(transport, local_port, remote_host, remote_port):
    handler = type("H", (ForwardHandler,), {
        "ssh_transport": transport, "remote_host": remote_host, "remote_port": remote_port})
    server = socketserver.ThreadingTCPServer(("127.0.0.1", local_port), handler)
    server.daemon_threads = True
    server.allow_reuse_address = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run(client, cmd):
    _, out, err = client.exec_command(cmd)
    return out.read().decode("utf-8", "replace").strip(), err.read().decode("utf-8", "replace").strip()


def main():
    ap = argparse.ArgumentParser(description="把课程的运行后端放到远程服务器上")
    ap.add_argument("--host", default="10.16.13.145")
    ap.add_argument("--user", default="liutianrui")
    ap.add_argument("--key", default=os.path.expanduser("~/.ssh/id_rsa"))
    ap.add_argument("--password", default=None)
    ap.add_argument("--remote-dir", default="/data1/liutianrui/open-course-runner")
    ap.add_argument("--port", type=int, default=8760)
    ap.add_argument("--python", default=None)
    args = ap.parse_args()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kw = {"username": args.user, "timeout": 15, "look_for_keys": False, "allow_agent": False}
    if args.password:
        kw["password"] = args.password
    elif os.path.isfile(args.key):
        kw["key_filename"] = args.key
    else:
        sys.exit("找不到密钥 %s，用 --password 或 --key 指定" % args.key)
    print("连接 %s@%s" % (args.user, args.host))
    client.connect(args.host, **kw)

    py = args.python
    if not py:
        for cand in ("python3", "python"):
            out, _ = run(client, "command -v %s" % cand)
            if out:
                py = out.splitlines()[0]
                break
    if not py:
        sys.exit("服务器上找不到 python")
    ver, _ = run(client, "%s -c 'import platform;print(platform.python_version())'" % py)
    host, _ = run(client, "hostname")
    print("服务器 %s  Python %s  %s" % (host, ver, py))

    run(client, "mkdir -p %s/pysrc" % args.remote_dir)
    sftp = client.open_sftp()
    for name, local in (("serve.py", os.path.join(HERE, "serve.py")),
                        ("checks.json", os.path.join(HERE, "..", "python", "data", "checks.json"))):
        if os.path.isfile(local):
            sftp.put(local, "%s/%s" % (args.remote_dir, name))
    pysrc = os.path.join(HERE, "..", "llm", "pysrc")
    n_mod = 0
    if os.path.isdir(pysrc):
        for fn in sorted(os.listdir(pysrc)):
            if fn.endswith(".py"):
                sftp.put(os.path.join(pysrc, fn), "%s/pysrc/%s" % (args.remote_dir, fn))
                n_mod += 1
    sftp.close()
    print("传了 serve.py、判定规则和 %d 个模块" % n_mod)

    run(client, "pkill -f 'serve.py --port %d' || true" % args.port)
    time.sleep(0.5)
    client.exec_command(
        "cd %s && nohup %s serve.py --port %d > run.log 2>&1 & echo started"
        % (args.remote_dir, py, args.port))
    time.sleep(1.5)
    log, _ = run(client, "cat %s/run.log" % args.remote_dir)
    if "Traceback" in log:
        print(log)
        sys.exit("后端没起来")

    server = start_tunnel(client.get_transport(), args.port, "127.0.0.1", args.port)
    print("\n通了。网页运行设置里填：http://127.0.0.1:%d\n按 Ctrl+C 结束" % args.port)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n收尾")
    finally:
        server.shutdown()
        run(client, "pkill -f 'serve.py --port %d' || true" % args.port)
        client.close()


if __name__ == "__main__":
    main()
