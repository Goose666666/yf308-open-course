# -*- coding: utf-8 -*-
"""大模型课界面走一遍：运行按钮、批改标记、提示与答案、简答题、切到自己的 Python。"""
import sys
from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8799").rstrip("/")
URL = BASE + "/llm/index.html"
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
        pg.evaluate("() => localStorage.clear()")
        pg.reload(wait_until="load")

        pg.wait_for_selector("#runcfg.on", timeout=15000)
        check("首次打开弹运行设置", True)
        pg.wait_for_function("() => document.getElementById('envbox').textContent.includes('就绪')", timeout=180000)
        print("     " + pg.text_content("#envbox").strip())
        check("浏览器环境就绪", "就绪" in pg.text_content("#envbox"))
        pg.click("#runcfg .mbtns .okb")

        # 目录、公式、示意图
        check("目录列出了七个部分", pg.locator("#side .part").count() == 7)
        check("可点的小节 22 个", pg.locator("#side .nav a:not(.disabled)").count() == 22)
        pg.evaluate("() => go('1.1')")
        pg.wait_for_timeout(1500)
        check("公式渲染出来了", pg.locator("#content mjx-container").count() > 0)
        check("先跑起来那段有图", pg.locator("#content .demo figure img").count() > 0)
        img_ok = pg.evaluate("""async () => {
            const i = document.querySelector('#content .demo figure img');
            if(!i) return false;
            if(!i.complete) await new Promise(r=>{i.onload=i.onerror=r});
            return i.naturalWidth > 0;
        }""")
        check("图片能显示", img_ok)

        # 参考答案复制进编辑器再运行
        pg.click("#content .ex .bar .mini:nth-of-type(2)")
        pg.wait_for_timeout(200)
        pg.evaluate("() => toEd(0,'ed0')")
        check("参考答案复制进编辑器", len(pg.input_value("#ed0")) > 20)
        pg.click("#content .ex .run")
        pg.wait_for_selector("#oed0", state="visible", timeout=180000)
        pg.wait_for_function("() => !document.querySelector('#content .ex .run').disabled", timeout=180000)
        head = pg.text_content("#oed0 .head")
        check("运行成功且批改正确", "运行成功" in head and "正确" in head, head)

        # 简答题
        pg.evaluate("() => go('2.1')")
        pg.wait_for_timeout(1200)
        n_qa = pg.locator("#content .qa").count()
        check("有简答题", n_qa > 0, str(n_qa))
        if n_qa:
            pg.click("#content .qa .qbar .mini:nth-of-type(2)")
            pg.wait_for_timeout(300)
            check("参考答案能展开", pg.locator("#qa0").is_visible())

        # 切到自己的 Python
        pg.evaluate("() => go('1.1')")
        pg.wait_for_timeout(800)
        pg.click(".toggle[title='运行设置']")
        pg.wait_for_selector("#runcfg.on")
        pg.check('input[name=eng][value="backend"]')
        pg.fill("#runurl", BACKEND)
        pg.click("#backrow .okb")
        try:
            pg.wait_for_function("() => document.getElementById('envbox').textContent.includes('就绪')", timeout=25000)
            print("     " + pg.text_content("#envbox").strip())
            check("连上自己的 Python", "就绪" in pg.text_content("#envbox"))
            pg.click("#runcfg .mbtns .okb")
            pg.evaluate("() => toEd(0,'ed0')")
            pg.click("#content .ex .run")
            pg.wait_for_function("() => !document.querySelector('#content .ex .run').disabled", timeout=120000)
            head = pg.text_content("#oed0 .head")
            check("后端模式也判正确", "运行成功" in head and "正确" in head, head)
        except Exception as e:
            check("连上自己的 Python", False, str(e)[:120])

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
