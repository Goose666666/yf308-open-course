# -*- coding: utf-8 -*-
"""3.7 DPO 对齐 —— 从零实现 Direct Preference Optimization 损失。

DPO 用「偏好数据」（同一提示下人更喜欢的回答 chosen vs 更差的 rejected）
直接优化策略，无需训练奖励模型或强化学习。损失鼓励策略相对参考模型，
提升 chosen 的概率、压低 rejected 的概率。
"""
import numpy as np


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def dpo_loss(logp_chosen, logp_rejected, ref_chosen, ref_rejected, beta=0.1):
    """输入为各回答的对数概率（策略模型与参考模型）。返回平均 DPO 损失。

    margin = β[(logπ_c - logπ_ref_c) - (logπ_r - logπ_ref_r)]
    loss   = -log σ(margin)
    """
    pi_logratio = logp_chosen - logp_rejected
    ref_logratio = ref_chosen - ref_rejected
    margin = beta * (pi_logratio - ref_logratio)
    return -np.log(sigmoid(margin)).mean()


if __name__ == "__main__":
    # 情形 A：策略比参考更偏好 chosen（对齐得好）→ 损失小
    good = dpo_loss(np.array([-2.0]), np.array([-5.0]),
                    np.array([-3.0]), np.array([-3.0]))
    # 情形 B：策略反而更偏好 rejected（没对齐）→ 损失大
    bad = dpo_loss(np.array([-5.0]), np.array([-2.0]),
                   np.array([-3.0]), np.array([-3.0]))
    print("对齐良好时 DPO 损失", round(float(good), 4))
    print("未对齐时   DPO 损失", round(float(bad), 4))
    print("损失更小 ⇒ 策略更偏好人类选择的回答")
