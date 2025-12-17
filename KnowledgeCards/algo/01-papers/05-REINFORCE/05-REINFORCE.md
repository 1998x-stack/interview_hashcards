# REINFORCE 算法记忆卡片

## 第一章：基础概念

Q: REINFORCE 属于哪类强化学习算法？
A: 策略梯度方法（Policy Gradient），也称为策略优化方法

Q: REINFORCE 的三大核心技术模块是什么？
A: 监督学习、强化学习、蒙特卡洛树搜索（MCTS）

C: REINFORCE 是一种 [策略梯度] 方法，直接优化 [策略]，而不先估计 [价值函数]

C: REINFORCE 的目标是最大化 [期望回报]

Q: 为什么策略梯度适合连续动作空间？
A: 因为可以定义连续策略分布（如高斯分布），通过采样动作并计算其log概率梯度即可，不需要枚举所有动作

---

## 第二章：核心公式

Q: REINFORCE 的策略梯度公式是什么？
A: ∇_θ J(θ) = E[∇_θ log π_θ(a_t|s_t) · G_t]

C: 策略梯度公式中，[log π(a|s)] 表示策略对动作的 [信心程度]

C: 公式中 [G_t] 是从时刻t开始的 [总奖励]（回报）

Q: log-likelihood trick 的作用是什么？
A: 让梯度变得容易求解，把对期望的梯度转换为可采样估计的形式：∇E[f(x)] → E[∇log p(x)·f(x)]

Q: 对于 softmax 策略，log π(a) 的梯度是什么形式？
A: one-hot(a) - π，即选中动作的one-hot向量减去策略分布

C: REINFORCE 梯度更新的核心是：让 [带来高回报] 的动作概率 [增加]，让 [带来低回报] 的动作概率 [减少]

---

## 第三章：Baseline 技术

Q: 为什么要在 REINFORCE 中引入 baseline？
A: 降低梯度的方差，提高训练稳定性，但不引入偏差

Q: baseline 为什么不会引入偏差？
A: 因为 E[∇_θ log π(a|s) · b(s)] = 0，baseline 项的期望梯度为零

C: 引入 baseline 后的梯度公式：∇_θ J = E[∇_θ log π · ([G_t] - [b(s_t)])]

Q: 常用的 baseline 选择有哪些？
A: 常数 baseline（如平均奖励）、移动平均 baseline、状态价值函数 V(s)

---

## 第四章：Advantage 函数

Q: Advantage 函数的定义是什么？
A: A(s,a) = G_t - V(s)，表示某个动作相比平均表现好多少

C: Advantage 衡量当前动作比 [平均策略] 好多少

Q: 使用 Advantage 相比直接使用 G_t 有什么优势？
A: 更精细的学习信号，更低方差，更稳定的训练

C: Advantage 的策略梯度：∇_θ J = E[∇_θ log π(a_t|s_t) · [A_t]]

Q: Advantage 如何演化到 Actor-Critic？
A: 用一个 Critic 网络学习 V(s)，提供 baseline；Actor 网络根据 Advantage 更新策略

---

## 第五章：训练机制

Q: REINFORCE 为什么方差很大？
A: 因为 G_t 是完整回报，受未来很多随机因素影响，波动极大

C: REINFORCE 使用 [Monte Carlo] 估计回报，方差 [大]，反馈 [慢]

Q: REINFORCE 的更新频率是怎样的？
A: 每完成一个或多个完整 episode 后更新一次（on-policy，蒙特卡洛式）

Q: 如何减少 REINFORCE 的方差？
A: 引入 baseline、使用 Advantage、采用 Actor-Critic、增加批次大小、使用 GAE(λ)

---

## 第六章：实现细节

C: 策略网络输出 [动作概率分布]，价值网络输出 [状态价值]

Q: 训练 REINFORCE 时如何处理离散动作空间？
A: 使用 softmax 输出动作概率分布，根据概率采样动作

Q: 训练 REINFORCE 时如何处理连续动作空间？
A: 输出高斯分布的均值和方差，从该分布采样动作

C: 梯度裁剪（gradient clipping）用于防止 [梯度爆炸]，提高训练 [稳定性]

Q: 为什么要在代码中使用 detach()？
A: 防止不必要的梯度计算和反向传播，确保某些值只作为常数使用

---

## 第七章：REINFORCE 变体

Q: PPO 相比 REINFORCE 有什么改进？
A: 使用重要性采样和 clip 机制，限制策略更新幅度，更稳定

Q: A2C/A3C 的核心思想是什么？
A: Actor-Critic 架构，用 Critic 估计价值函数提供 baseline，降低方差

C: REINFORCE 演化路线：基础 REINFORCE → 加 [baseline] → 用 [V(s)] 做 baseline → 引出 [Advantage] → 通往 Actor-Critic

Q: GAE (Generalized Advantage Estimation) 是什么？
A: 一种计算 Advantage 的方法，通过 λ 参数平衡偏差和方差

---

## 第八章：优缺点总结

Q: REINFORCE 的主要优点是什么？
A: 1) 简单直观，易于理解和实现；2) 适用于连续动作空间；3) 不需要环境模型（model-free）

Q: REINFORCE 的主要缺点是什么？
A: 1) 方差大，训练不稳定；2) 收敛慢；3) 样本效率低（on-policy）

C: REINFORCE 是 [on-policy] 算法，每次更新后必须用 [新策略] 重新采样

Q: 什么情况下应该使用 REINFORCE？
A: 动作空间连续、不需要高样本效率、重视策略直接优化的场景

---

## 第九章：与其他算法对比

| 算法 | 类型 | 使用 baseline? | 样本效率 |
|------|------|----------------|----------|
| REINFORCE | Policy Gradient | ✗ | 低 |
| REINFORCE+baseline | Policy Gradient | ✓ | 中 |
| A2C/A3C | Actor-Critic | ✓ | 中 |
| PPO | Policy Gradient | ✓ | 高 |
| Q-learning | Value-based | N/A | 高 |

Q: Q-learning 和 REINFORCE 的核心区别是什么？
A: Q-learning 是价值迭代方法，先估计 Q(s,a) 再选动作；REINFORCE 是策略梯度，直接优化策略

---

## 第十章：调试技巧

Q: REINFORCE 训练不收敛可能的原因？
A: 1) 学习率过大；2) 方差过大；3) 奖励设计不合理；4) 没有使用 baseline

C: 调试 REINFORCE 时应该监控：[策略损失]、[回报均值]、[回报方差]、[梯度范数]

Q: 如何验证 REINFORCE 实现的正确性？
A: 在简单环境（如 CartPole）上测试，检查损失下降、回报上升、策略熵变化趋势

---

## 代码实现要点

```python
# 核心更新公式伪代码
for episode in episodes:
    states, actions, rewards = collect_trajectory()
    returns = compute_discounted_returns(rewards)  # G_t
    
    for t in range(len(states)):
        log_prob = policy.log_prob(actions[t], states[t])
        loss = -log_prob * returns[t]  # 负号因为要最大化
        loss.backward()
    
    optimizer.step()
```

C: 计算回报时使用 [折扣因子] γ，从 [后往前] 累积：G_t = r_t + γ·G_{t+1}

Q: 为什么 REINFORCE 的损失前面有负号？
A: 因为梯度下降是最小化损失，而我们要最大化期望回报，所以加负号转为最小化问题