# AlphaGo 底层原理记忆卡片

## 第一章：核心架构

Q: AlphaGo 的三大核心技术模块是什么？
A: 监督学习（Policy Network）、强化学习（自我对弈）、蒙特卡洛树搜索（MCTS）

C: AlphaGo 使用 [策略网络] 预测人类会下哪一步，使用 [价值网络] 判断当前局面对谁更有利

Q: Policy Network 的作用是什么？
A: 给每个可能的落子位置打分，作为搜索的起点，输出一个概率分布表示"高手会下哪"

Q: Value Network 的作用是什么？
A: 输出当前棋盘状态下白方赢的概率（或价值），范围在 [0,1] 或 [-1,1]

C: AlphaGo = [监督学习] + [强化学习] + [MCTS]

---

## 第二章：监督学习阶段

Q: Policy Network 是如何训练的？
A: 通过监督学习，用上千万盘人类高手的棋谱，模仿"在这个局面下，人类选择了哪个点"

C: Policy Network 使用 [卷积神经网络]（CNN），输入是 [棋盘状态]，输出是 [19×19] 的概率分布

Q: 为什么 Policy Network 能处理围棋？
A: 因为 CNN 能捕捉局部模式（如征子、打劫），适合处理棋盘的二维空间特征

Q: Policy Network 训练用的损失函数是什么？
A: 交叉熵损失（Cross-Entropy），目标是让预测的动作概率分布接近人类实际选择

---

## 第三章：强化学习阶段

Q: AlphaGo 如何通过强化学习提升？
A: 通过自我对弈（Self-Play）生成新棋谱，用策略梯度方法强化"赢棋中的动作"

C: 强化学习阶段使用 [自我对弈] 产生数据，更新 [策略网络]，让模型 [超越] 人类棋手

Q: 自我对弈的训练目标是什么？
A: 最大化期望回报，让赢棋中的动作概率增加，输棋中的动作概率减少

Q: Value Network 是如何训练的？
A: 用自我对弈产生的 (状态, 胜负结果) 对，通过监督回归学习：V(s) ≈ z（z=±1）

C: Value Network 的训练标签是 [最终胜负结果]，损失函数是 [均方误差]（MSE）

---

## 第四章：MCTS（蒙特卡洛树搜索）

Q: MCTS 在 AlphaGo 中的作用是什么？
A: 模拟未来多种走法分支，然后选最优一步，结合 Policy 和 Value 指导搜索

Q: MCTS 的四个步骤是什么？
A: 1) Selection（选择）；2) Expansion（扩展）；3) Simulation/Evaluation（模拟）；4) Backpropagation（回传）

C: MCTS 的 Selection 阶段使用 [UCB]（上置信界）或 [PUCT] 公式选择最优分支

Q: AlphaGo 的 MCTS 如何结合神经网络？
A: Policy Net 提供先验概率指导扩展，Value Net 直接估值叶子节点，替代随机 rollout

C: AlphaGo Zero 不再使用 [随机模拟]（rollout），完全依赖 [Value Network] 估值

---

## 第五章：PUCT 算法

Q: PUCT 选择公式是什么？
A: 选择使 Q(s,a) + U(s,a) 最大的动作，其中 U = c_puct · P(s,a) · √N(s) / (1+N(s,a))

C: PUCT 公式中，[Q(s,a)] 是平均价值，[U(s,a)] 是探索奖励

Q: PUCT 中的 c_puct 参数作用是什么？
A: 控制探索与利用的平衡，越大越倾向于探索未访问的节点

C: 访问次数 [N(s,a)] 越少，探索项 U(s,a) 越 [大]，鼓励探索

---

## 第六章：根节点策略

Q: 为什么要在根节点注入 Dirichlet 噪声？
A: 增强探索性，避免过度依赖网络预测，促进发现新变化

C: 根节点策略 = (1-ε)·[网络先验] + ε·[Dirichlet噪声]

Q: 温度参数在 MCTS 中的作用是什么？
A: 控制选择动作时的随机性，温度=1时按访问次数比例采样，温度→0时选访问次数最多的

---

## 第七章：AlphaGo 版本演进

Q: AlphaGo 和 AlphaGo Zero 的主要区别是什么？
A: AlphaGo Zero 不使用人类棋谱，完全从零自我对弈学习；合并 Policy 和 Value 为单一网络

C: AlphaGo Zero 使用 [单一网络] 输出 [策略] 和 [价值] 两个头

Q: AlphaGo Master 的特点是什么？
A: 在线对弈中战胜人类顶尖棋手，包括柯洁，展示了强大的实力

Q: AlphaZero 相比 AlphaGo Zero 的泛化性如何？
A: 泛化到国际象棋、将棋等其他棋类游戏，展示了通用性

---

## 第八章：网络架构细节

Q: AlphaGo 的神经网络输入是什么？
A: 多个通道的棋盘特征，如当前玩家的棋子、对手的棋子、历史几步的棋盘状态

C: 棋盘特征编码为 [19×19×C] 的张量，C 是 [通道数]

Q: Policy Head 的输出维度是多少？
A: 19×19+1（额外1维表示 PASS 动作）

Q: Value Head 的输出是什么？
A: 单一标量，经过 tanh 激活限制在 [-1, 1]

C: 网络主干使用 [ResNet] 结构，包含多个 [残差块]

---

## 第九章：训练流程

Q: AlphaGo 的完整训练流程是什么？
A: 1) 监督学习训练 Policy Net；2) 自我对弈训练 RL Policy；3) 训练 Value Net；4) 组合 MCTS 迭代提升

C: 自我对弈循环：[生成对局] → [收集数据] → [训练网络] → [更新模型] → 重复

Q: 为什么要保存历史对局数据？
A: 作为经验回放池，避免过拟合到最新策略，增加训练稳定性

Q: 如何平衡探索与利用？
A: 通过 PUCT 公式、温度参数、Dirichlet 噪声来控制

---

## 第十章：围棋规则与计算

Q: Tromp-Taylor 计分规则是什么？
A: 己方棋子数 + 被己方完全包围的空点数，分数高者获胜

C: 围棋规则包括：[打劫]（不能立即复现上一局面）、[提子]（无气棋子被移除）、[禁止自杀]

Q: 如何检测打劫？
A: 简单打劫：比较当前棋盘与上一步棋盘，相同则非法；超级打劫需要更多历史信息

---

## 第十一章：实现细节

Q: 为什么 AlphaGo 需要大量算力？
A: MCTS 需要模拟数千次，每次都要调用神经网络评估，计算密集

C: AlphaGo 使用 [TPU]（Tensor Processing Unit）加速神经网络推理

Q: 如何加速 MCTS？
A: 批量评估多个叶子节点、使用更快的网络、虚拟损失（Virtual Loss）实现并行

Q: 虚拟损失的作用是什么？
A: 多线程并行 MCTS 时，临时降低正在评估节点的价值，避免重复选择

---

## 第十二章：关键创新点

Q: AlphaGo 相比传统围棋 AI 的突破是什么？
A: 结合深度学习和 MCTS，用神经网络替代手工特征和随机模拟，大幅提升棋力

C: 传统围棋 AI 依赖 [手工特征] 和 [暴力搜索]，AlphaGo 用 [深度学习] 学习特征

Q: 为什么围棋难以用传统方法解决？
A: 状态空间巨大（10^170）、分支因子高（每步约250种选择）、局面评估困难

---

## 第十三章：局限与未来

Q: AlphaGo 的局限性有哪些？
A: 1) 计算资源需求大；2) 训练时间长；3) 泛化能力有限（仅围棋）；4) 不可解释性

Q: AlphaGo 对 AI 研究的启示是什么？
A: 强化学习 + 蒙特卡洛搜索 + 深度学习的组合可以解决复杂决策问题

C: AlphaGo 的成功推动了 [强化学习] 和 [自我对弈] 在其他领域的应用

---

## 第十四章：数学公式总结

C: 策略梯度：∇J = E[∇log π(a|s) · [z]]，z 是 [胜负标签]

C: PUCT 公式：argmax_a [Q(s,a)] + [c_puct·P(s,a)·√N(s)/(1+N(s,a))]

C: 价值网络损失：L = ([V(s)] - [z])²

Q: 折扣因子在围棋中的作用？
A: 围棋是确定性游戏，通常使用 γ=1（不折扣），因为只有最终胜负

---

## 第十五章：对比其他棋类 AI

| AI 系统 | 游戏 | 关键技术 | 成就 |
|---------|------|----------|------|
| Deep Blue | 国际象棋 | Alpha-Beta 剪枝 | 1997 击败卡斯帕罗夫 |
| AlphaGo | 围棋 | DL + MCTS | 2016 击败李世石 |
| AlphaZero | 多棋类 | 自我对弈 + MCTS | 超越所有专业引擎 |

Q: 为什么围棋比国际象棋更难？
A: 1) 分支因子更大；2) 局面评估更难；3) 没有明确的"吃子价值"；4) 状态空间更大

---

## 代码实现要点

```python
# MCTS 核心循环伪代码
def mcts_search(root_state, num_simulations):
    for _ in range(num_simulations):
        node = root
        # 1. Selection
        while not node.is_leaf():
            node = select_child(node)  # PUCT
        
        # 2. Expansion
        if not terminal(node):
            expand(node)  # 用 Policy Net 先验
        
        # 3. Evaluation
        value = evaluate(node)  # Value Net 或 rollout
        
        # 4. Backup
        backpropagate(node, value)
    
    return best_action(root)
```

C: 每次 MCTS 模拟包括：[选择] → [扩展] → [评估] → [回传]

Q: 如何从 MCTS 树中选择最终动作？
A: 温度采样（前期）或选访问次数最多的动作（后期）