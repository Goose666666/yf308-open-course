# -*- coding: utf-8 -*-
"""把深度学习与大模型复习的本地网页改造成静态站点。

内容来自 build_data.py 导出的 course.json，代码在浏览器里跑，也能连自己的 Python。
"""
import io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = r"D:\software\claude\paper\深度学习大模型复习\webapp\app.py"
DST = os.path.join(ROOT, "llm", "index.html")
BRAND = "YF308AI实验室开放学习平台"

src = io.open(SRC, encoding="utf-8").read()
m = re.search(r'HTML_PAGE = r"""(.*)"""\s*$', src, re.S)
assert m, "没找到 HTML_PAGE"
html = m.group(1)
n = 0


def sub(old, new, count=1):
    global html, n
    assert html.count(old) == count, "锚点没匹配上，出现 %d 次：%s" % (html.count(old), old[:70])
    html = html.replace(old, new)
    n += 1


# ---------- 头部：标题、图标、MathJax、runner ----------
sub('<title>深度学习 & 大模型 · 任务先行复习</title>',
    '<title>深度学习与大模型 · 复习 · %s</title>\n'
    '<link rel="icon" href="../assets/favicon.png">\n'
    '<link rel="apple-touch-icon" href="../assets/logo-180.png">' % BRAND)

sub('<script src="/static/mathjax-tex-svg.js" async></script>',
    '<script src="../assets/mathjax-tex-svg.js" async></script>\n'
    '<script src="../assets/runner.js"></script>')

# ---------- 补样式：例子、示意图、简答题、运行设置 ----------
sub('.hint-n{margin-left:auto;font-size:11.5px;color:var(--faint)}',
    '''.hint-n{margin-left:auto;font-size:11.5px;color:var(--faint);cursor:pointer}
.eg{margin-top:16px;padding:14px 18px 12px;border-radius:12px;border:1px solid var(--line);
  background:color-mix(in oklab,var(--accent2) 7%,transparent)}
.eg .eglab{display:inline-block;font-size:11px;font-weight:800;color:var(--accent);letter-spacing:.5px}
.eg p{margin:7px 0}.eg p:first-of-type{margin-top:2px}
figure svg.dfig{max-width:100%;height:auto;background:#fff;border-radius:10px;padding:8px;border:1px solid var(--line)}
.qa{margin-bottom:14px}
.qa .q{background:var(--bg3);border:1px solid var(--line);border-radius:12px;padding:14px 18px;font-size:15px;font-weight:600}
.qa .qbar{display:flex;gap:9px;padding:10px 0 0}
.brandbar{display:flex;align-items:center;gap:10px;padding:0 24px 14px}
.brandbar img{width:34px;height:34px;flex:none}
.brandbar span{font-size:12px;font-weight:600;color:var(--muted);line-height:1.35}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;display:none;
  align-items:center;justify-content:center;padding:20px}
.modal.on{display:flex}
.modal-box{background:var(--bg2);border:1px solid var(--line);border-radius:16px;padding:26px 28px;max-width:520px;width:100%}
.modal-box h3{margin:0 0 18px;font-size:19px;font-weight:700}
.engines{display:flex;gap:10px;margin-bottom:14px}
.engx{flex:1;display:flex;align-items:center;gap:9px;padding:14px 16px;border:1px solid var(--line);
  border-radius:10px;cursor:pointer;font-size:14.5px;font-weight:600}
.engx:has(input:checked){border-color:var(--accent);background:var(--bg3)}
.engx input{accent-color:var(--accent);width:16px;height:16px}
.urlrow{display:flex;gap:9px;margin-bottom:14px}
.urlrow input{flex:1;min-width:0;background:var(--bg3);color:var(--fg);border:1px solid var(--line);
  border-radius:9px;padding:0 14px;height:44px;font-size:14px;font-family:inherit}
.envbox{font-size:13.5px;padding:12px 15px;border-radius:9px;border:1px solid var(--line);
  background:var(--bg3);margin-bottom:16px;min-height:44px}
.envbox.good{border-color:var(--ok)}.envbox.bad{border-color:var(--err)}
.mbtns{display:flex;justify-content:flex-end;gap:9px}
.mbtns .okb,.urlrow .okb{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border:none;
  border-radius:9px;padding:0 24px;height:44px;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit}''')

# ---------- 侧栏与顶栏 ----------
sub('<aside id="side"><div class="brand"><h1>深度学习 &amp; 大模型 · 复习</h1><p>任务先行 · 边跑边学</p></div><nav id="nav"></nav></aside>',
    '<aside id="side"><div class="brandbar"><img src="../assets/logo.png" alt=""><span>%s</span></div>'
    '<div class="brand"><h1>深度学习与大模型 · 复习</h1></div><nav id="nav"></nav></aside>' % BRAND)

sub('<button class="toggle" id="themeBtn">🌙</button>',
    '<div style="display:flex;gap:9px">'
    '<button class="toggle" onclick="openRunCfg()" title="运行设置">⚙</button>'
    '<button class="toggle" id="themeBtn">🌙</button></div>')

sub('  <div id="content"></div>\n</div>',
    '''  <div id="content"></div>
</div>
<div class="modal" id="runcfg">
  <div class="modal-box">
    <h3>代码在哪里跑</h3>
    <div class="engines">
      <label class="engx"><input type="radio" name="eng" value="browser" onchange="pickEngine('browser')">浏览器里跑</label>
      <label class="engx"><input type="radio" name="eng" value="backend" onchange="pickEngine('backend')">连自己的 Python</label>
    </div>
    <div id="backrow" style="display:none">
      <div class="urlrow"><input id="runurl" placeholder="http://127.0.0.1:8760" spellcheck="false"><button class="okb" onclick="connectBackend()">连接</button></div>
    </div>
    <div class="envbox" id="envbox"></div>
    <div class="mbtns"><button class="okb" onclick="closeRunCfg()">开始学习</button></div>
  </div>
</div>''')

# ---------- 图片路径与示意图 ----------
sub("""function figs(list){return (list||[]).map(f=>`<figure>${f.svg?f.svg:`<img src="${f.src}" loading="lazy">`}<figcaption>${inline(f.cap||'')}</figcaption></figure>`).join('');}""",
    """const asset=s=>String(s||'').replace(/^\\//,'');
function figs(list){return (list||[]).map(f=>`<figure>${f.svg?f.svg:`<img src="${asset(f.src||f.img)}" loading="lazy">`}<figcaption>${inline(f.cap||'')}</figcaption></figure>`).join('');}""")

# ---------- 目录与小节改成读本地 JSON ----------
sub("""async function loadNav(){TREE=await(await fetch('/api/curriculum')).json();let h='';""",
    """let COURSE=null;
async function loadNav(){COURSE=await(await fetch('data/course.json')).json();TREE=COURSE.curriculum;let h='';""")

sub("""  SEC=await(await fetch('/api/section/'+id)).json();location.hash=id;draw();window.scrollTo({top:0});""",
    """  SEC=COURSE.sections[id];location.hash=id;draw();window.scrollTo({top:0});""")

# ---------- 知识点里补上例子和示意图 ----------
sub("""    for(const n of SEC.notes){h+=`<div class="card"><h3>${esc(n.h)}</h3>${rich(n.body)}`;
      if(n.fig)h+=figs([n.fig]);""",
    """    for(const n of SEC.notes){h+=`<div class="card"><h3>${esc(n.h)}</h3>${rich(n.body)}`;
      if(n.eg)h+=`<div class="eg"><span class="eglab">例</span>${rich(n.eg)}</div>`;
      if(n.fig)h+=figs([n.fig]);""")

# ---------- 简答题 ----------
sub("""  if(SEC.exercises&&SEC.exercises.length){h+=`<div class="step"><span class="k">🛠️ 动手改</span></div>`;""",
    """  if(SEC.qa&&SEC.qa.length){h+=`<div class="step"><span class="k">💭 自测</span></div>`;
    SEC.qa.forEach((q,i)=>{h+=`<div class="qa">
      <div class="q">${inline(q.q)}</div>
      <div class="qbar"><button class="mini" onclick="tog('qh${i}',this)">💡 提示</button>
        <button class="mini" onclick="tog('qa${i}',this)">✅ 参考答案</button></div>
      <div class="reveal hint" id="qh${i}">${inline(q.hint||'')}</div>
      <div class="reveal hint" id="qa${i}" style="background:color-mix(in oklab,var(--ok) 10%,transparent);border-color:color-mix(in oklab,var(--ok) 28%,transparent)">${rich(q.a||'')}</div>
    </div>`;});}
  if(SEC.exercises&&SEC.exercises.length){h+=`<div class="step"><span class="k">🛠️ 动手改</span></div>`;""")

# ---------- 运行与批改改到前端 ----------
sub("""        <span class="hint-n">本机 CPU · 40s</span></div>""",
    """        <span class="hint-n" id="engtag" onclick="openRunCfg()"></span></div>""")

sub("""async function runCode(e,idx,btn){const code=document.getElementById(e).value.trim();const out=document.getElementById('o'+e);
  const head=out.querySelector('.head'),pre=out.querySelector('pre');
  if(!code){out.className='out err';head.innerHTML='✗ 编辑器是空的';pre.textContent='先写点代码，或用参考答案复制到编辑器。';out.style.display='block';return;}
  btn.disabled=true;btn.innerHTML='<span class="spin"></span> 运行中';
  try{const r=await(await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,sid:SEC.id,idx})})).json();
    out.className='out '+(r.ok?'ok':'err');let hh=r.ok?'✓ 运行成功':'✗ 运行出错';
    if(r.grade&&r.grade.verdict==='correct')hh+='<span class="verdict v-ok">🎉 批改：正确</span>';
    else if(r.grade&&r.grade.verdict==='wrong')hh+=`<span class="verdict v-no">✗ 结果不对 · 命中 ${r.grade.hit}/${r.grade.total}</span>`;
    head.innerHTML=hh;pre.textContent=r.output;out.style.display='block';
  }catch(x){out.className='out err';head.innerHTML='✗ 请求失败';pre.textContent=String(x);out.style.display='block';}
  finally{btn.disabled=false;btn.innerHTML='▶ 运行并批改';}}""",
    """const NUMRE=/-?\\d[\\d,]*(?:\\.\\d+)?/g;
function extractNums(t){const out=[];for(const tok of String(t).match(NUMRE)||[]){
  const v=parseFloat(tok.replace(/,/g,''));if(!isNaN(v))out.push(Math.round(v*100)/100);}return out;}
function grade(expect,output){
  if(!expect||!expect.length)return{verdict:'none'};
  const rest=extractNums(output);let hit=0;
  for(const e of expect){const tol=Math.max(0.05,Math.abs(e)*0.001);
    for(let j=0;j<rest.length;j++){if(Math.abs(rest[j]-e)<=tol){rest.splice(j,1);hit++;break;}}}
  return{verdict:hit===expect.length?'correct':'wrong',hit,total:expect.length};}

async function runCode(e,idx,btn){const code=document.getElementById(e).value.trim();const out=document.getElementById('o'+e);
  const head=out.querySelector('.head'),pre=out.querySelector('pre');
  if(!code){out.className='out err';head.innerHTML='✗ 编辑器是空的';pre.textContent='先写点代码，或用参考答案复制到编辑器。';out.style.display='block';return;}
  btn.disabled=true;btn.innerHTML='<span class="spin"></span> 运行中';
  try{const r=await Runner.run(code);
    out.className='out '+(r.ok?'ok':'err');let hh=r.ok?'✓ 运行成功':'✗ 运行出错';
    const ex=(SEC.exercises||[])[idx];
    const g=r.ok&&ex?grade(ex.expect,r.output):null;
    if(g&&g.verdict==='correct')hh+='<span class="verdict v-ok">🎉 批改：正确</span>';
    else if(g&&g.verdict==='wrong')hh+=`<span class="verdict v-no">✗ 结果不对 · 命中 ${g.hit}/${g.total}</span>`;
    head.innerHTML=hh;pre.textContent=r.output;out.style.display='block';
  }catch(x){out.className='out err';head.innerHTML='✗ 没跑起来';pre.textContent=String(x);out.style.display='block';}
  finally{btn.disabled=false;btn.innerHTML='▶ 运行并批改';}}

async function bootEngine(){
  const box=document.getElementById('envbox');
  box.className='envbox';box.textContent='正在连接';
  try{
    await Runner.boot(s=>{if(s)box.textContent=s;});
    box.className='envbox good';box.textContent=Runner.label()+' 就绪';
  }catch(err){
    box.className='envbox bad';
    box.textContent=Runner.mode==='backend'?'连不上 '+Runner.url:'运行环境没加载出来，检查网络';
  }
  document.querySelectorAll('#engtag').forEach(t=>t.textContent=Runner.label());
}
function pickEngine(m){Runner.mode=m;
  document.getElementById('backrow').style.display=m==='backend'?'block':'none';
  if(m==='browser')bootEngine();else document.getElementById('envbox').textContent='';}
function connectBackend(){Runner.url=document.getElementById('runurl').value.trim();bootEngine();}
function openRunCfg(){document.getElementById('runcfg').classList.add('on');
  const r=document.querySelector('input[name=eng][value="'+Runner.mode+'"]');if(r)r.checked=true;
  document.getElementById('runurl').value=Runner.url;
  document.getElementById('backrow').style.display=Runner.mode==='backend'?'block':'none';
  bootEngine();}
function closeRunCfg(){localStorage.setItem('llmRunSeen','1');document.getElementById('runcfg').classList.remove('on');}""")

sub("""initTheme();loadNav().then(()=>{const h=location.hash.slice(1);
  const ok=h&&TREE.some(p=>p.items.some(it=>it.ready&&it.id===h));go(ok?h:NAV_FIRST);});""",
    """Runner.configure({
  workerUrl:'../assets/pyworker.js',
  modulesUrl:'pysrc/modules.json',
  packages:['numpy'],
  timeout:180000
});
initTheme();loadNav().then(()=>{const h=location.hash.slice(1);
  const ok=h&&TREE.some(p=>p.items.some(it=>it.ready&&it.id===h));go(ok?h:NAV_FIRST);
  Runner.boot().then(bootEngine).catch(bootEngine);
  if(!localStorage.getItem('llmRunSeen'))setTimeout(openRunCfg,400);});""")

os.makedirs(os.path.dirname(DST), exist_ok=True)
io.open(DST, "w", encoding="utf-8", newline="\n").write(html)
print("改了 %d 处，写出 %s  %.0f KB" % (n, DST, os.path.getsize(DST) / 1024))
