# -*- coding: utf-8 -*-
"""把 24 道参考答案在浏览器里跑一遍，确认判定都能通过。"""
import json
import sys
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8799/python/index.html"
PROXY = {"server": "http://127.0.0.1:7890", "bypass": "127.0.0.1,localhost"}

BOOT = """
async () => {
  localStorage.setItem('runSeen','1');
  localStorage.setItem('runMode','browser');
  await Runner.boot();
  return Runner.label();
}
"""

CHECK_ONE = """
async ([part, k]) => {
  const e = LAB[part][k];
  const id = e.tag.replace('练习 ','');
  const r = await Runner.check(e.sol, id);
  return {id, title: e.title, ok: r.ok, msg: r.msg,
          fail: (r.items||[]).filter(it=>!it.pass).map(it=>it.desc),
          out: (r.output||'').slice(0,600)};
}
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(proxy=PROXY)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL, wait_until="load")
        page.evaluate("() => { localStorage.setItem('runSeen','1'); localStorage.setItem('runMode','browser'); }")
        page.reload(wait_until="load")
        label = page.evaluate(BOOT)
        print("运行环境：%s" % label)

        lab = page.evaluate("() => Object.fromEntries(Object.entries(LAB).map(([k,v])=>[k, v.length]))")
        total = sum(lab.values())
        print("练习 %d 道\n" % total)

        bad = []
        for part in sorted(lab, key=int):
            for k in range(lab[part]):
                r = page.evaluate(CHECK_ONE, [int(part), k])
                mark = "通过" if r["ok"] else "不通过"
                print("  %-5s %-24s %s  %s" % (r["id"], r["title"], mark, r["msg"]))
                if not r["ok"]:
                    bad.append(r)
        browser.close()

    print("")
    if errors:
        print("页面报错：")
        for e in errors[:10]:
            print("  " + e)
    if bad:
        print("没通过 %d 道：" % len(bad))
        for r in bad:
            print("--- %s %s" % (r["id"], r["title"]))
            print("    缺：" + "，".join(r["fail"]))
            print("    输出：" + r["out"].replace("\n", "\n           "))
        sys.exit(1)
    print("24 道参考答案全部通过")


if __name__ == "__main__":
    main()
