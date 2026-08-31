# -*- coding: utf-8 -*-
"""4.2 Agent —— 从零实现 ReAct 式工具调用循环。

智能体让 LLM 不只生成文本，还能「思考 → 调用工具 → 观察结果 → 再思考」。
这里用规则解析器模拟 LLM 输出的动作，并真正执行工具。
"""
import re


def calculator(expr):
    return eval(expr, {"__builtins__": {}}, {})     # 受限沙箱


TOOLS = {"calc": calculator, "len": len}


def parse_action(text):
    """从 'Action: tool[input]' 中解析出工具名与参数。"""
    m = re.search(r"Action:\s*(\w+)\[(.*?)\]", text)
    return (m.group(1), m.group(2)) if m else (None, None)


def run_react(steps):
    """执行一串 ReAct 动作，返回每步的观察结果（Observation）。"""
    observations = []
    for text in steps:
        tool, arg = parse_action(text)
        if tool in TOOLS:
            observations.append(TOOLS[tool](arg))
        else:
            observations.append(None)
    return observations


if __name__ == "__main__":
    # 模拟 LLM 逐步输出的动作（真实场景里由模型生成）
    trace = [
        "Thought: 先算 12*3\nAction: calc[12*3]",
        "Thought: 再加 4\nAction: calc[36+4]",
        "Thought: 数一下字符\nAction: len[hello]",
    ]
    obs = run_react(trace)
    print("各步观察结果:", obs)
    print("最终答案:", obs[1])
