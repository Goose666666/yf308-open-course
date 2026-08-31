# -*- coding: utf-8 -*-
"""把两套课程的 Python 内容导出成静态站点用的 JSON，并拷贝资源文件。"""
import importlib.util, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = r"D:\software\claude\paper"
LLM_SRC = os.path.join(PAPER, "深度学习大模型复习")
PY_SRC = os.path.join(PAPER, "python-hands-on")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def build_llm():
    v1 = load("content_v1", os.path.join(LLM_SRC, "webapp", "_archive_v1", "content.py"))
    v2 = load("content_v2", os.path.join(LLM_SRC, "webapp", "content.py"))

    sections = {}
    for sid, s in v1.DISPLAY_SECTIONS.items():
        sections[sid] = dict(s)
    for sid, s in v2.SECTIONS.items():
        merged = dict(s)
        old = v1.DISPLAY_SECTIONS.get(sid)
        if old and old.get("qa"):
            merged["qa"] = old["qa"]          # v2 没写简答题，沿用 v1 的
        if old and not merged.get("module"):
            merged["module"] = old.get("module")
        sections[sid] = merged

    cur = v2.DISPLAY_CUR
    ready = {it["id"] for p in cur for it in p["items"] if it.get("ready")}
    for p in cur:
        for it in p["items"]:
            it["ready"] = it["id"] in sections
    sections = {k: v for k, v in sections.items()}

    out = {"curriculum": cur, "sections": sections}
    dst = os.path.join(ROOT, "llm", "data")
    os.makedirs(dst, exist_ok=True)
    with open(os.path.join(dst, "course.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    # 从零实现的模块，练习里 import 它们
    pysrc = os.path.join(ROOT, "llm", "pysrc")
    os.makedirs(pysrc, exist_ok=True)
    mods = {}
    for fn in sorted(os.listdir(os.path.join(LLM_SRC, "代码"))):
        if fn.endswith(".py") and not fn.startswith("_"):
            src = open(os.path.join(LLM_SRC, "代码", fn), encoding="utf-8").read()
            shutil.copy2(os.path.join(LLM_SRC, "代码", fn), os.path.join(pysrc, fn))
            mods[fn] = src
    with open(os.path.join(pysrc, "modules.json"), "w", encoding="utf-8") as f:
        json.dump(mods, f, ensure_ascii=False)

    img_src = os.path.join(LLM_SRC, "webapp", "static", "img")
    img_dst = os.path.join(ROOT, "llm", "static", "img")
    if os.path.isdir(img_dst):
        shutil.rmtree(img_dst)
    shutil.copytree(img_src, img_dst)

    mj = os.path.join(LLM_SRC, "webapp", "static", "mathjax-tex-svg.js")
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    shutil.copy2(mj, os.path.join(ROOT, "assets", "mathjax-tex-svg.js"))

    n_ex = sum(len(s.get("exercises", [])) for s in sections.values())
    n_qa = sum(len(s.get("qa", [])) for s in sections.values())
    print("LLM: %d 节 / %d 练习 / %d 简答 / %d 模块 / %d 图" %
          (len(sections), n_ex, n_qa, len(mods), len(os.listdir(img_dst))))


def build_python():
    chk = load("checks_py", os.path.join(PY_SRC, "checks.py"))
    dst = os.path.join(ROOT, "python", "data")
    os.makedirs(dst, exist_ok=True)
    with open(os.path.join(dst, "checks.json"), "w", encoding="utf-8") as f:
        json.dump(chk.CHECKS, f, ensure_ascii=False)
    for sub in ("pages", "pdf"):
        s, d = os.path.join(PY_SRC, "web", sub), os.path.join(ROOT, "python", sub)
        if os.path.isdir(d):
            shutil.rmtree(d)
        shutil.copytree(s, d)
    print("PY: %d 道判定 / %d 讲义页 / %d 份 PDF" %
          (len(chk.CHECKS), len(os.listdir(os.path.join(ROOT, "python", "pages"))),
           len(os.listdir(os.path.join(ROOT, "python", "pdf")))))


if __name__ == "__main__":
    build_llm()
    build_python()
