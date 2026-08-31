# -*- coding: utf-8 -*-
"""界面走一遍：运行按钮、提交检查、input 输入框、画图、切到自己的 Python。"""
import sys
from playwright.sync_api import sync_playwright, expect

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8799").rstrip("/")
URL = BASE + "/python/index.html"
PROXY = {"server": "http://127.0.0.1:7890", "bypass": "127.0.0.1,localhost"}
BACKEND = "http://127.0.0.1:8760"

fails = []


def check(name, cond, detail=""):
    print("  %-30s %s%s" % (name, "通过" if cond else "不通过", ("  " + detail) if detail and not cond else ""))
    if not cond:
        fails.append(name)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(proxy=PROXY)
        pg = b.new_page(viewport={"width": 1440, "height": 950})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="load")
        pg.evaluate("() => { localStorage.clear(); }")
        pg.reload(wait_until="load")

        # 首次打开会弹运行设置
        pg.wait_for_selector("#runcfg", state="visible", timeout=10000)
        check("首次打开弹运行设置", pg.is_visible("#runcfg"))
        pg.wait_for_function("() => document.getElementById('envbox').textContent.includes('就绪')", timeout=180000)
        label = pg.text_content("#envbox")
        check("浏览器环境就绪", "就绪" in label, label)
        print("     " + label.strip())
        check("没有解释小字", pg.locator("#runcfg .note").count() == 0)
        pg.click("#runcfg .mbtns .ok")

        # 进课程，切到实战
        pg.click(".card")
        pg.click("#seg-lab")
        pg.wait_for_selector(".ex", timeout=10000)

        # 第 0 章第一题：运行全部
        ex = pg.locator("#ex-0-0")
        ex.locator(".runall").click()
        pg.wait_for_function(
            "() => { const o=document.querySelector('#ex-0-0 .output'); return o && o.textContent && !o.textContent.startsWith('运行中'); }",
            timeout=120000)
        out = ex.locator(".output").first.text_content()
        check("运行起始代码不报错", "Traceback" not in out and "Error" not in out, out[:80])

        # 提交检查：先填参考答案
        pg.evaluate("""() => {
            const ta = document.querySelector('#ex-0-0 .cells textarea');
            ta.value = LAB[0][0].sol; onEdit(ta.id);
        }""")
        ex.locator(".submit").click()
        pg.wait_for_function(
            "() => { const j=document.getElementById('judge-ex-0-0'); return j && j.style.display!=='none' && !j.textContent.includes('正在检查'); }",
            timeout=120000)
        judge = pg.text_content("#judge-ex-0-0")
        check("提交检查判为做对", "做对了" in judge, judge[:80])

        # input() 出现时才显示输入框
        check("默认不显示输入框", not ex.locator(".stdinrow").is_visible())
        pg.evaluate("""() => {
            const ta = document.querySelector('#ex-0-0 .cells textarea');
            ta.value = 'name = input()\\nprint("你好，" + name)'; onEdit(ta.id);
        }""")
        pg.wait_for_timeout(300)
        check("写了 input 就出现输入框", ex.locator(".stdinrow").is_visible())
        ex.locator(".stdinrow textarea").fill("小王")
        ex.locator(".runall").click()
        pg.wait_for_function(
            "() => { const o=document.querySelector('#ex-0-0 .output'); return o && o.textContent.includes('小王'); }",
            timeout=120000)
        check("input 读到了输入框的内容", "小王" in ex.locator(".output").first.text_content())

        # matplotlib 画图
        pg.evaluate("""() => {
            const ta = document.querySelector('#ex-0-0 .cells textarea');
            ta.value = 'import matplotlib.pyplot as plt\\nplt.plot([1,4,9,16])\\nplt.title("test")\\nplt.show()\\nprint("画完了")';
            onEdit(ta.id);
        }""")
        ex.locator(".runall").click()
        pg.wait_for_function(
            "() => document.querySelectorAll('#ex-0-0 .figs img').length > 0", timeout=240000)
        check("画的图显示出来了", ex.locator(".figs img").count() > 0)

        # 讲义页与 PDF 链接
        pg.click("#seg-know")
        pg.wait_for_selector("#know-pages img", timeout=10000)
        base = URL.rsplit("/", 1)[0] + "/"
        srcs = pg.evaluate("() => [...document.querySelectorAll('#know-pages img')].map(i=>i.getAttribute('src'))")
        bad_img = [s for s in srcs if pg.request.get(base + s).status != 200]
        check("讲义页图都能取到", not bad_img, "%d/%d 取不到" % (len(bad_img), len(srcs)))
        pdfs = pg.evaluate("() => [...document.querySelectorAll('#know-title .dl')].map(a=>a.getAttribute('href'))")
        bad_pdf = [s for s in pdfs if pg.request.get(base + s).status != 200]
        check("PDF 下载链接可用", not bad_pdf, str(bad_pdf))

        # 切到自己的 Python
        pg.click(".gear")
        pg.wait_for_selector("#runcfg", state="visible")
        pg.check('input[name=eng][value="backend"]')
        pg.fill("#runurl", BACKEND)
        pg.click("#backrow .ok")
        try:
            pg.wait_for_function(
                "() => document.getElementById('envbox').textContent.includes('就绪')", timeout=20000)
            lb = pg.text_content("#envbox")
            check("连上自己的 Python", "就绪" in lb, lb)
            print("     " + lb.strip())
            pg.click("#runcfg .mbtns .ok")
            pg.click("#seg-lab")
            pg.wait_for_selector(".ex", timeout=10000)
            pg.evaluate("""() => {
                const ta = document.querySelector('#ex-0-0 .cells textarea');
                ta.value = LAB[0][0].sol; onEdit(ta.id);
            }""")
            pg.locator("#ex-0-0 .submit").click()
            pg.wait_for_function(
                "() => { const j=document.getElementById('judge-ex-0-0'); return j && j.style.display!=='none' && !j.textContent.includes('正在检查'); }",
                timeout=60000)
            check("后端模式也能判对", "做对了" in pg.text_content("#judge-ex-0-0"))
        except Exception as e:
            check("连上自己的 Python", False, str(e)[:120])

        pg.screenshot(path="../_build/ui.png", full_page=False)
        b.close()

    if errs:
        print("\n页面报错：")
        for e in errs[:8]:
            print("  " + e)
    print("")
    if fails:
        print("没通过：" + "，".join(fails))
        sys.exit(1)
    print("界面检查全部通过")


if __name__ == "__main__":
    main()
