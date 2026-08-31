# YF308AI实验室开放学习平台

重庆邮电大学通信与信息工程学院 AI 实验室的公开课程。每门课都带可运行的练习，代码直接在浏览器里跑，提交后自动判对错，不用装环境。

打开就能用：<https://goose666666.github.io/yf308-open-course/>

## 课程

**Python 入门 · 动手实践** — 十二章，24 道练习。从装环境到做完一个数据分析项目，每章先跑通一个小程序，再讲清背后的原理。左边是讲义，可以下载 PDF，右边是练习，给了起始代码、提示、参考答案和预期结果。

**深度学习与大模型 · 复习** — 二十二小节，66 道练习，整理中。从零手写自动求导、Transformer、GPT、LoRA、RAG、CLIP、扩散模型，全部只用 numpy。

## 代码在哪里跑

三种跑法，在网页右上角的齿轮里切换。

**浏览器**，默认这个。Python 在你自己的浏览器里执行，numpy、pandas、matplotlib 都能用，画的图会显示在输出下面。第一次打开要下载运行环境，之后有缓存就快了。

**自己电脑上的 Python**。适合想用本地已装好的库，或者想读写自己的文件。

```bash
python runner/serve.py
```

然后在运行设置里选「连自己的 Python」，地址填 `http://127.0.0.1:8760`。只依赖标准库，不用 pip 装东西。

**远程服务器**。适合练习要用 GPU 或者大内存的场景。

```bash
pip install paramiko
python runner/connect_server.py --host 服务器地址 --user 用户名
```

它把后端脚本传到服务器上启动，再用 SSH 端口转发映射到本机的 `http://127.0.0.1:8760`，网页里填的地址和本地模式一样。之所以走端口转发而不让服务器直接对外监听，一是浏览器只信任本机地址，二是这个端口能执行任意代码，不该暴露在网络上。

## 目录

```
index.html          平台首页
python/             Python 入门，讲义页图、PDF、判题规则
llm/                深度学习与大模型
assets/             logo、Pyodide 运行环境封装、共用脚本
runner/             本地与服务器的运行后端
_build/             从原始课程工程生成静态站点的脚本与测试
```

站点是从 `paper/python-hands-on` 和 `paper/深度学习大模型复习` 两个本地工程生成的。改完原工程后重新生成：

```bash
python _build/build_data.py          # 导出课程内容与判题规则
python _build/build_python_site.py   # 生成 Python 课的静态页
```

## 测试

先起一个静态服务，再跑测试。

```bash
python -m http.server 8799
python _build/test_python_site.py    # 24 道参考答案在浏览器里跑一遍，判定要全过
python _build/test_python_ui.py      # 界面走一遍：运行、判题、输入、画图、切后端
```

## 许可

代码用 MIT，见 [LICENSE](LICENSE)。讲义内容用 CC BY 4.0，见 [LICENSE-CONTENT](LICENSE-CONTENT)。
