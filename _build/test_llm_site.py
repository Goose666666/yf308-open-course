# -*- coding: utf-8 -*-
"""把 66 道参考答案在浏览器里跑一遍，确认批改都判正确。"""
import sys, time
from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8799").rstrip("/")
URL = BASE + "/llm/index.html"
PROXY = {"server": "http://127.0.0.1:7890", "bypass": "127.0.0.1,localhost"}

BOOT = """
async () => {
  localStorage.setItem('llmRunSeen','1');
  localStorage.setItem('runMode','browser');
  await Runner.boot();
  return Runner.label();
}
"""

RUN_ONE = """
async ([sid, idx]) => {
  const s = COURSE.sections[sid], ex = s.exercises[idx];
  const r = await Runner.run(ex.solution);
  const g = grade(ex.expect, r.output);
  return {sid, idx, title: s.title, ok: r.ok, verdict: g.verdict,
          hit: g.hit, total: g.total, expect: ex.expect,
          out: (r.output||'').slice(-700)};
}
"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(proxy=PROXY)
        pg = b.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="load")
        pg.evaluate("() => { localStorage.setItem('llmRunSeen','1'); localStorage.setItem('runMode','browser'); }")
        pg.reload(wait_until="load")
        pg.wait_for_function("() => typeof COURSE !== 'undefined' && COURSE && window.Runner", timeout=60000)
        print("运行环境：%s" % pg.evaluate(BOOT))

        plan = pg.evaluate("""() => {
            const out=[];
            for(const p of COURSE.curriculum) for(const it of p.items){
                const s=COURSE.sections[it.id]; if(!s) continue;
                (s.exercises||[]).forEach((e,i)=>out.push([it.id,i]));
            }
            return out;
        }""")
        print("练习 %d 道\n" % len(plan))

        bad, last_sid = [], None
        for sid, idx in plan:
            t0 = time.time()
            r = pg.evaluate(RUN_ONE, [sid, idx])
            dt = time.time() - t0
            if sid != last_sid:
                print("  %s %s" % (sid, r["title"]))
                last_sid = sid
            mark = "正确" if r["verdict"] == "correct" else ("无判定" if r["verdict"] == "none" else "不对")
            print("    题 %d  %s  命中 %s/%s  %.1fs" % (idx + 1, mark, r["hit"], r["total"], dt))
            if r["verdict"] != "correct":
                bad.append(r)
        b.close()

    print("")
    if errs:
        print("页面报错：")
        for e in errs[:8]:
            print("  " + e)
    if bad:
        print("没判正确 %d 道：" % len(bad))
        for r in bad:
            print("--- %s 题 %d  %s  期望 %s" % (r["sid"], r["idx"] + 1, r["title"], r["expect"]))
            print("    输出：" + r["out"].replace("\n", "\n           "))
        sys.exit(1)
    print("66 道参考答案全部判正确")


if __name__ == "__main__":
    main()
