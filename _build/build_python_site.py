# -*- coding: utf-8 -*-
"""把 python-hands-on 的本地网页改造成静态站点：代码改在浏览器里跑，也能连自己的 Python。"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = r"D:\software\claude\paper\python-hands-on\web\index.html"
DST = os.path.join(ROOT, "python", "index.html")

html = io.open(SRC, encoding="utf-8").read()
n = 0


def sub(old, new, count=1):
    global html, n
    assert html.count(old) == count, "锚点没匹配上，出现 %d 次：%s" % (html.count(old), old[:70])
    html = html.replace(old, new)
    n += 1


BRAND = "YF308AI实验室开放学习平台"

# ---------- 0. 品牌 ----------
sub('<title>Python 入门 · 动手实践</title>',
    '<title>Python 入门 · 动手实践 · %s</title>\n'
    '<link rel="icon" href="../assets/favicon.png">\n'
    '<link rel="apple-touch-icon" href="../assets/logo-180.png">' % BRAND)

sub('''.home-title{font-size:2rem;font-weight:700;margin:0 0 .5rem}''',
    '''.home-title{font-size:2rem;font-weight:700;margin:0 0 .5rem}
.plate{display:flex;flex-direction:column;align-items:center;gap:14px;margin-bottom:26px}
.plate img{width:92px;height:92px}
.plate .pname{font-size:1.05rem;font-weight:650;letter-spacing:.04em}
.brand-mini{display:flex;align-items:center;gap:9px;margin-bottom:10px}
.brand-mini img{width:26px;height:26px}
.brand-mini span{font-size:12.5px;font-weight:600;color:var(--muted);line-height:1.3}''')

sub('''  <h1 class="home-title">Python 入门 · 动手实践</h1>''',
    '''  <div class="plate"><img src="../assets/logo.png" alt="%s"><div class="pname">%s</div></div>
  <h1 class="home-title">Python 入门 · 动手实践</h1>''' % (BRAND, BRAND))

sub("""document.getElementById("brand").innerHTML='<button class="hbtn" onclick="showHome()">← 返回首页</button><div class="tname">'+TRACKS[t].name+'</div>';""",
    """document.getElementById("brand").innerHTML='<div class="brand-mini"><img src="../assets/logo.png" alt=""><span>%s</span></div><button class="hbtn" onclick="showHome()">← 返回首页</button><div class="tname">'+TRACKS[t].name+'</div>';""" % BRAND)

# ---------- 1. 引入 runner ----------
sub('<body>\n<button class="gear"',
    '<script src="../assets/runner.js"></script>\n<body>\n<button class="gear"')

# ---------- 2. 补样式 ----------
sub('.envbox.warnbox{border-color:#9a7b2f}',
    '''.envbox.warnbox{border-color:#9a7b2f}
.engines{display:flex;gap:10px;margin-bottom:14px}
.eng{flex:1;display:flex;align-items:center;gap:9px;padding:14px 16px;border:1px solid var(--line);
  border-radius:10px;cursor:pointer;font-size:14.5px;font-weight:600}
.eng:has(input:checked){border-color:var(--acc);background:var(--codebg)}
.eng input{accent-color:var(--acc);width:16px;height:16px}
.urlrow{display:flex;gap:9px;align-items:stretch;margin-bottom:14px}
.urlrow input{flex:1;min-width:0;background:var(--codebg);color:var(--fg);border:1px solid var(--line);
  border-radius:9px;padding:0 14px;height:44px;font-size:14px;font-family:inherit}
.urlrow button{height:44px;padding:0 24px;white-space:nowrap}
.stdinrow{display:none;margin:8px 0 0}
.stdinrow textarea{width:100%;min-height:54px;background:var(--codebg);color:var(--fg);border:1px solid var(--line);
  border-radius:9px;padding:10px 13px;font-size:13.5px;font-family:Consolas,monospace;resize:vertical}
.figs{display:flex;flex-wrap:wrap;gap:10px;padding:0 0 6px}
.figs img{max-width:100%;background:#fff;border-radius:8px;padding:6px;border:1px solid var(--line)}
#engtag{cursor:pointer;text-decoration:underline dotted}''')

# ---------- 3. 单元加上输出图与输入框 ----------
sub('''      <pre class="output" id="out-${cid}"></pre>
    </div>`;''',
    '''      <div style="flex:1;min-width:0"><pre class="output" id="out-${cid}"></pre><div class="figs" id="figs-${cid}"></div></div>
    </div>`;''')

sub('''        <span class="runstat" id="stat-${exId}"></span>
      </div>''',
    '''        <span class="runstat" id="stat-${exId}"></span>
      </div>
      <div class="stdinrow"><textarea spellcheck="false" placeholder="运行时输入，一行一个"></textarea></div>''')

# ---------- 4. onEdit 顺带判断要不要显示输入框 ----------
sub('function onEdit(id){', 'function onEdit(id){ setTimeout(function(){syncStdin(id);},0);')

# 输入框也是 textarea，别让高亮的初始化扫到它
sub('document.querySelectorAll("#lab-body textarea").forEach(t=>onEdit(t.id));',
    'document.querySelectorAll("#lab-body .cells textarea").forEach(t=>onEdit(t.id));')

# ---------- 5. 换掉三个后端调用 ----------
sub('''async function loadEnv(){
  const box = document.getElementById("envbox");
  try{
    const e = await (await fetch("/api/env")).json();
    box.innerHTML = `本机 Python ${e.python}，运行环境正常，可以直接开始。`;
    box.className = "envbox good";
  }catch(err){
    box.textContent = "没读到本机环境信息，后端可能没起来。";
    box.className = "envbox warnbox";
  }
}
function openRunCfg(){
  document.getElementById("runcfg").style.display = "flex";
  loadEnv();
}
function closeRunCfg(){
  localStorage.setItem("runSeen","1");
  document.getElementById("runcfg").style.display = "none";
}''',
    r'''function syncStdin(id){
  const ta=document.getElementById(id); if(!ta) return;
  const ex=ta.closest(".ex"); if(!ex) return;
  const row=ex.querySelector(".stdinrow"); if(!row) return;
  const need=[...ex.querySelectorAll(".cells textarea")].some(t=>/\binput\s*\(/.test(t.value));
  row.style.display = need ? "block" : "none";
}
function stdinOf(ex){
  const row=ex && ex.querySelector(".stdinrow");
  return (row && row.style.display!=="none") ? row.querySelector("textarea").value : "";
}
async function bootEngine(){
  const box=document.getElementById("envbox");
  box.className="envbox"; box.textContent="正在连接";
  try{
    await Runner.boot(s=>{ if(s) box.textContent=s; });
    box.className="envbox good"; box.textContent=Runner.label()+" 就绪";
  }catch(err){
    box.className="envbox warnbox";
    box.textContent = Runner.mode==="backend" ? "连不上 "+Runner.url : "运行环境没加载出来，检查网络";
  }
  const tag=document.getElementById("engtag"); if(tag) tag.textContent=Runner.label();
}
function pickEngine(m){
  Runner.mode=m;
  document.getElementById("backrow").style.display = m==="backend" ? "block" : "none";
  if(m==="browser") bootEngine(); else document.getElementById("envbox").textContent="";
}
function connectBackend(){
  Runner.url=document.getElementById("runurl").value.trim();
  bootEngine();
}
function openRunCfg(){
  document.getElementById("runcfg").style.display = "flex";
  const r=document.querySelector('input[name=eng][value="'+Runner.mode+'"]'); if(r) r.checked=true;
  document.getElementById("runurl").value = Runner.url;
  document.getElementById("backrow").style.display = Runner.mode==="backend" ? "block" : "none";
  bootEngine();
}
function closeRunCfg(){
  localStorage.setItem("runSeen","1");
  document.getElementById("runcfg").style.display = "none";
}''')

sub('''  try{
    const r=await fetch("/api/check",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({code, id})});
    const j=await r.json();
    if(j.ok===null||j.ok===undefined){''',
    '''  try{
    const j=await Runner.check(code, id);
    if(j.ok===null||j.ok===undefined){''')

sub('''  }catch(err){
    box.innerHTML="连不到后端，先确认 serve.py 还开着。";
  }finally{ btns.forEach(b=>b.disabled=false); }''',
    '''  }catch(err){
    box.innerHTML="没跑起来："+err;
  }finally{ btns.forEach(b=>b.disabled=false); }''')

sub('''  outcell.style.display="flex"; out.textContent="运行中，首次训练可能要十几秒到一分多钟，请耐心等。";
  stat.textContent=""; btns.forEach(b=>b.disabled=true);
  const t0=Date.now();
  try{
    const r=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({code})});
    if(!r.ok) throw new Error("HTTP "+r.status);
    const j=await r.json();
    out.textContent=j.output||"运行结束，无输出。别忘了 print 结果。";
  }catch(err){
    out.textContent="连不到运行后端。请先在项目目录运行 python serve.py，再用浏览器打开 http://127.0.0.1:8000（不要直接双击 html 文件）。\\n\\n错误："+err;
  }finally{''',
    '''  const figbox=document.getElementById("figs-"+cid);
  outcell.style.display="flex"; out.textContent="运行中";
  if(figbox) figbox.innerHTML="";
  stat.textContent=""; btns.forEach(b=>b.disabled=true);
  const t0=Date.now();
  try{
    const j=await Runner.run(code, stdinOf(ex));
    out.textContent=j.output||"运行结束，无输出。别忘了 print 结果。";
    if(figbox && j.figs && j.figs.length)
      figbox.innerHTML=j.figs.map(b=>'<img src="data:image/png;base64,'+b+'">').join("");
  }catch(err){
    out.textContent="没跑起来："+err;
  }finally{''')

# ---------- 6. 运行设置弹窗 ----------
sub('''    <div class="steps" id="rc-step">开始之前</div>
    <h3 id="rc-title">这个网页怎么用</h3>
    <p class="sub2" id="rc-sub">左边是讲义，右边的练习可以直接改代码并运行。</p>
    <div class="envbox" id="envbox">正在检查本机环境…</div>
    <p class="note">前五章只用 Python 自带的功能，不需要再装任何第三方库。<br>
       练习里的代码在你这台电脑上执行，改坏了也没关系，点重置就能恢复。</p>
    <div class="mbtns"><button class="ok" onclick="closeRunCfg()">开始学习</button></div>''',
    '''    <div class="steps" id="rc-step">运行设置</div>
    <h3 id="rc-title">代码在哪里跑</h3>
    <div class="engines">
      <label class="eng"><input type="radio" name="eng" value="browser" onchange="pickEngine('browser')">浏览器里跑</label>
      <label class="eng"><input type="radio" name="eng" value="backend" onchange="pickEngine('backend')">连自己的 Python</label>
    </div>
    <div id="backrow" style="display:none">
      <div class="urlrow"><input id="runurl" placeholder="http://127.0.0.1:8760" spellcheck="false"><button class="ok" onclick="connectBackend()">连接</button></div>
    </div>
    <div class="envbox" id="envbox"></div>
    <div class="mbtns"><button class="ok" onclick="closeRunCfg()">开始学习</button></div>''')

# ---------- 7. 页脚与启动 ----------
sub('''document.getElementById("foot").innerHTML =
  'Python 入门 · 动手实践　十二章，24 道练习。讲义每段代码与练习答案都实测跑过。<br>'+
  '代码在本机 Python 运行，练习可以提交检查。讲义支持下载 PDF。';
renderSummary(); showHome();
// 第一次打开先引导选运行方式；选过或跳过后就不再自动弹
if(!localStorage.getItem("runSeen")){ setTimeout(()=>openRunCfg(), 400); }''',
    '''document.getElementById("foot").innerHTML =
  'YF308AI实验室开放学习平台　Python 入门 · 动手实践　十二章，24 道练习。<br>'+
  '<span id="engtag" onclick="openRunCfg()"></span>';
Runner.configure({
  workerUrl: "../assets/pyworker.js",
  checksUrl: "data/checks.json",
  packages: [],
  timeout: 60000
});
renderSummary(); showHome();
Runner.boot().then(function(){ const t=document.getElementById("engtag"); if(t) t.textContent=Runner.label(); }).catch(function(){});
if(!localStorage.getItem("runSeen")){ setTimeout(()=>openRunCfg(), 400); }''')

os.makedirs(os.path.dirname(DST), exist_ok=True)
io.open(DST, "w", encoding="utf-8", newline="\n").write(html)
print("改了 %d 处，写出 %s  %.0f KB" % (n, DST, os.path.getsize(DST) / 1024))
