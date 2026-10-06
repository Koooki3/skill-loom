# 工程理论与设计取舍

检索/核验日期：2026-10-06。以下为一手技术资料；不是本项目自己的实验结果。每个设计仍需代码与任务验证。

| 一手来源 | 阅读位置与支持内容 | 本项目的取舍 | 不支持的推断 |
|---|---|---|---|
| Zhang, Lazuka, Murag. [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), 2025-10-16 | Anatomy、Developing and evaluating skills、Security：渐进加载、从真实缺口出发、审查技能内容与依赖 | description/entry/reference分层；有缺口才加；固定来源并先暂存 | 文件格式相同不证明跨模型效果相同 |
| Anthropic. [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), 2025-09-29 | Anatomy、Context retrieval、Long-horizon tasks：上下文选择与按需获取，工具职责清楚 | 最小任务组合、重复能力候选审查、保留持久证据引用 | 更短的description不等于已经测得更少token或更高准确率 |
| Anthropic. [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 2026-01-09 | Structure、Graders、Capability vs regression、Non-determinism：任务、试验与最终环境状态分开，多类评分互补 | 静态、发现、脚本、真实任务四层证据；单元fixture不冒充agent benchmark | 自报成功或单次通过不能证明稳定性 |
| Sculley et al. [Hidden Technical Debt in Machine Learning Systems](https://papers.neurips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf), NeurIPS 2015 | §2–5，pp.2–5：隐含消费者、数据依赖、反馈环及管线复杂度 | 用户画像、候选和运行状态分开；记录调用关系；避免只增不减的规则库 | 这是跨领域工程类比，论文并未研究SKILL.md或本工具 |

这些材料共同支持将能力内容与维护基础设施分离，但不赋予本项目方法原创性。技能库生命周期、反思与验证过滤已有直接研究先例，参见[文献矩阵](literature-matrix.md)。

## 当前研究问题

RQ1：在预先定义的文件漂移、中断和错误回退场景中，显式计划与哈希约束能否保持约定的写入/恢复行为？这是可通过软件故障注入回答的问题。

RQ2：将验收记录绑定任务、候选和时效，能否拒绝形式上通过但已失效的记录？测试能覆盖指定情形，不能验证证据内容真实性。

RQ3：基于真实任务的候选准入、最小组合和退役机制，能否提高agent任务质量并控制成本？这是尚需多任务、多模型、多宿主实验的问题。本版不将RQ1/RQ2结果外推为RQ3已成立。

## 从理论到实现的反馈记录

第一轮原型提供静态盘点、固定来源暂存、事务和回退。跨宿主检查暴露“允许结束”与“任务通过”应分开，于是Stop上限保留失败状态。运行发现接口暴露GitHub仓库元数据URL尾斜杠造成错误，修正并增加契约回归。对验收设计的复核发现仅有artifact哈希会接受另一轮旧证据，于是加入run/candidate/time绑定。

这些修改来自实际论证和测试；并不是某篇论文的复现，也没有实现GEPA、SkillRL训练或EvoSkill完整搜索算法。后续研究应优先补上真实任务质量与成本评测，而不是增加没有证据价值的新门控层。
