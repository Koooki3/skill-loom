# Skill Loom 文献矩阵与主张边界

核验日期与纳入截止：**2026-10-06**。本版纳入 15 篇高相关主来源，固定 arXiv 版本；元数据、全文入口和分角色证据位置见 [references.json](references.json)。这里报告的是文献证据，**不是 Skill Loom 的模型实验结果**。

现有研究已经覆盖技能发现、反馈修订、验证集选择、个性化、版本维护、跨模型迁移，以及由确定性宿主管理候选写入。因此，Skill Loom 目前适合定位为**借鉴已有研究的工程原型与软件故障注入实验载体**。本综述没有发现足以支持“首次提出自演化技能”“首个跨模型技能系统”或“取得 SOTA”的证据。

## 检索与阅读口径

检索从指定的 SkillsBench、EvoSkill、SkillRL、AutoSkill、CoEvoSkills、生命周期综述、GEPA 及三篇基础论文开始，再补入直接影响结论的 ACE、Rethinking、SkillCoach、SkillZip 和评价综述。优先使用 arXiv 原文；第三方摘要和搜索结果仅作定位，不作为方法、实验或局限的最终依据。这是有明确边界的专题综述，不声称穷尽全部相关工作。

全部 15 项均已打开并阅读下表列出的正文部分。**“正文已读”只指相关方法、评价与局限章节，不等于逐页读完全部附录，也不等于复现。** GEPA 的 HTML 读取失败，改读其官方 PDF；其余使用 arXiv HTML。没有把仅摘要、不可得或晚于截止日期的文献作为本版结论依据。本次没有复现这些论文的模型实验，也没有把 PDF 全文复制进仓库。

矩阵中的“作者局限”来自原文；“评读判断”是根据实验范围作出的本项目判断。论文间的模型、任务、工具、反馈可见性和计算预算不同，不能拼成跨论文排行榜。每项采用简要转述，详细定位交给来源登记表。

## 已核验版本与阅读位置

作者采用已核验首作者加 *et al.*；单作者论文保留全名。年份是初次公开年份，版本日期另列。

| ID / short id | 准确题名、作者、年份 | 固定版本与正文阅读范围 |
|---|---|---|
| R01 / `skillsbench2026` | [SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks](https://arxiv.org/abs/2602.12670v4) — Xiangyi Li et al., 2026 | v4，2026-06-14；§2–5.1、Table 2、§6.1 |
| R02 / `evoskill2026` | [EvoSkill: Automated Skill Discovery for Multi-Agent Systems](https://arxiv.org/abs/2603.02766v1) — Salaheddin Alzubi et al., 2026 | v1，2026-03-03；§2、§3.1–3.3、Table 1、§3.1.3 脚注 |
| R03 / `skillrl2026` | [SkillRL: Evolving Agents via Recursive Skill-Augmented Reinforcement Learning](https://arxiv.org/abs/2602.08234v1) — Peng Xia et al., 2026 | v1，2026-02-09；§3、Algorithm 1、§4、Tables 1–3 |
| R04 / `autoskill2026` | [AutoSkill: Experience-Driven Lifelong Learning via Skill Self-Evolution](https://arxiv.org/abs/2603.01145v2) — Yutao Yang et al., 2026 | v2，2026-03-05；§3–6、Tables 1–2 |
| R05 / `coevoskills2026` | [CoEvoSkills: Self-Evolving Agent Skills via Co-Evolutionary Verification](https://arxiv.org/abs/2604.01687v3) — Hanrong Zhang et al., 2026 | v3，2026-08-10；§3、Algorithm 1、§4.1–4.3、附录 B–C |
| R06 / `lifecycle2026` | [Dynamic Agent Skills: A Lifecycle Survey and Taxonomy of Evolving Skill Libraries](https://arxiv.org/abs/2607.10113v1) — Yubo Li, 2026 | v1，2026-07-11；§2–3、§5、§7.2、§13、附录 A |
| R07 / `gepa2025` | [GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning](https://arxiv.org/abs/2507.19457v2) — Lakshya A Agrawal et al., 2025 | v2，2026-02-14；[PDF](https://arxiv.org/pdf/2507.19457v2) 印刷页 2–5、8–10 的 §2–4、Tables 1–3 |
| R08 / `ace2025` | [Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models](https://arxiv.org/abs/2510.04618v3) — Qizheng Zhang et al., 2025 | v3，2026-03-29；§3、§4.1–4.3、§5 |
| R09 / `voyager2023` | [Voyager: An Open-Ended Embodied Agent with Large Language Models](https://arxiv.org/abs/2305.16291v2) — Guanzhi Wang et al., 2023 | v2，2023-10-19；§2、§3.3–3.4、§4、Tables 1–2 |
| R10 / `reflexion2023` | [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366v4) — Noah Shinn et al., 2023 | v4，2023-10-10；§3、§4.3、Table 3、§5 |
| R11 / `selfrefine2023` | [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651v2) — Aman Madaan et al., 2023 | v2，2023-05-25；§2–3、Algorithm 1、Table 1、§6 |
| R12 / `rethink2026` | [Rethinking Self-Evolving Agent Skills: Feedback Dynamics over Multiple Rounds](https://arxiv.org/abs/2608.02636v1) — Yuxuan Liu et al., 2026 | v1，页面列 2026-07-31；Framework Overview、Experiments、Analysis、Limitations |
| R13 / `skillcoach2026` | [SkillCoach: Self-Evolving Rubrics for Evaluating and Enhancing Agentic Skill-Use](https://arxiv.org/abs/2607.01874v1) — Jiayin Zhu et al., 2026 | v1，2026-07-02；§3、§4.1、§4.4 讨论、§6、附录 A |
| R14 / `skillzip2026` | [SkillZip: Evaluation-Free Skill Compression for Self-Evolving Agents by Discovering Reusable Structure](https://arxiv.org/abs/2608.11079v2) — Xiaofan Bai et al., 2026 | v2，2026-08-16；§III、§IV-C、§V-B、§VI、附录 A-D |
| R15 / `evaluation2026` | [Agent Skill Evaluation and Evolution: Frameworks and Benchmarks](https://arxiv.org/abs/2606.11435v1) — Kexin Ding et al., 2026 | v1，2026-06-09；§3–5、Tables 1–2 |

## WHY / HOW / WHAT 矩阵

### 技能有效性、生成、个性化与准入

| 来源 | WHY：问题与前提 | HOW：实际机制 | WHAT：报告的证据 | 局限或反证 | 对 Skill Loom 的影响 |
|---|---|---|---|---|---|
| [R01](https://arxiv.org/html/2602.12670v4) | 技能存在不等于对任务有帮助。 | 同任务、模型与 harness 做有/无技能配对，容器隔离与确定性 verifier。 | v4：87 任务、18 配置；平均通过率 33.9%→50.5%，收益不均。 | 作者：缺少充分的等长度无关文本/RAG 控制；终端任务不能直接外推 GUI 或长周期协作。 | 固定完整执行配置；静态发现成功不能替代配对任务试验。 |
| [R02](https://arxiv.org/html/2603.02766v1) | 专业能力不足需从执行失败中定位。 | Proposer/Builder 生成或修改技能；训练诊断、验证选择、测试隔离，保留候选历史。 | SealQA 26.6%→38.7%；另有跨任务迁移实验。 | 作者：各配置单次运行。OfficeQA 正文与表格存在数值冲突；迁移覆盖有限。 | 借鉴候选谱系与独立验收；不能把提案数量当作收益。 |
| [R03](https://arxiv.org/html/2602.08234v1) | 原始轨迹冗长；已有策略未必被模型有效使用。 | 成败经验蒸馏、层级 SkillBank、检索、cold-start SFT 与 GRPO，共同演化策略和技能。 | ALFWorld/WebShop 与七个 QA 数据集；移除 SFT 或动态演化均有消融。 | 评读：权重训练与库更新共同变化；结果不是冻结模型的目录安装实验。 | 将训练型路线列为独立扩展，不能声称当前 CLI 实现了 SkillRL。 |
| [R04](https://arxiv.org/html/2603.01145v2) | 稳定用户偏好与反复纠正应跨会话保留。 | 仅从用户查询抽取；混合检索；add/merge/discard 与版本化维护，个人库和共享库分离。 | WildChat 四个子集提取 1,858 个技能，报告分布和中英案例。 | 评读：提取量、版本号和案例不等于受控下游收益；未建立普遍跨模型效用。 | 个性化、去重和版本化已是先例；本项目须另外检验用户目标是否兑现。 |
| [R05](https://arxiv.org/html/2604.01687v3) | 一次生成多文件技能不可靠，自造测试也可能失真。 | 独立 surrogate verifier 提供诊断；隐藏内容的 oracle 仍以通过/失败驱动重试；双重预算。 | 85 任务；主要方法五次运行，跨模型三次；Opus 条件报告 71.1% 通过率。 | 作者附录 C：surrogate 会漏掉精度要求，也会误拒正确答案。评读：不能称完全无 oracle，也不能直接比较 R01 的 v4 汇总。 | 有界循环、验收隔离与失败退出；receipt 不能冒充可信 oracle。 |

### 生命周期、优化与知识保留

| 来源 | WHY：问题与前提 | HOW：实际机制 | WHAT：报告的证据 | 局限或反证 | 对 Skill Loom 的影响 |
|---|---|---|---|---|---|
| [R06](https://arxiv.org/html/2607.10113v1) | “skill”含义混杂，静态最终分数掩盖库变化。 | 六种语义、八阶段生命周期、可编辑记录与十种更新算子；区分证据类型。 | 124 篇审计集的综合，包含准入、维护、来源与回退。 | 作者：截止 2026-05-31，检索非穷尽，证据异质；框架是比较工具，不是新算法。 | 生命周期、lineage、gate 和 rollback 应明确引用先例。 |
| [R07](https://arxiv.org/pdf/2507.19457v2) | 标量奖励可能丢失昂贵轨迹中的诊断信息。 | 反思式 prompt mutation、候选谱系和按样例表现的 Pareto 选择；模型冻结。 | 六任务、两模型，含选择策略消融及训练/验证/测试分离。 | Table 1：Qwen3-8B 的 AIME 上 GEPA 32%、GRPO 38%；merge 也非总有益。大部分 rollout 用于验证。 | 候选选择需要实际任务分数；手填五维权重不是 GEPA，预算须含验证成本。 |
| [R08](https://arxiv.org/html/2510.04618v3) | 整段重写可能遗失细节，反复压缩会使上下文失真。 | Generator/Reflector/Curator 分工；带 ID 条目、增量 delta、确定性合并与去重。 | AppWorld 配对基线；离线训练后测试与在线先预测后更新分别评价。 | 作者：依赖强 Reflector，错误反思会带来噪声；简单任务可能更适合短规则。 | 优先可审查局部补丁；记录保留/删除的约束，不能把文档增长当积累。 |
| [R14](https://arxiv.org/html/2608.11079v2) | 累积修订造成重复规则，但罕见例外不能按频率删除。 | 类型化契约与 MDL 目标；覆盖约束；Zip-on-Write；宿主校验、事务日志与原子替换。 | 九个模型–任务设置，报告平均压缩率 31.2%；其中五项不降或上升。 | 作者：保证相对于已解析契约，不保证解析完美或所有模型行为等价；压缩后仍做任务评价。 | 内容约束保留与行为回归分开验；“模型提议、确定性宿主写入”也已有先例。 |
| [R15](https://arxiv.org/html/2606.11435v1) | 技能扩张需要效用、效率与安全评价。 | 整理四类演化机制和六类 benchmark，区分检索、生成、使用与安全。 | 汇总已有研究和 benchmark 范围，不提供新的算法对照实验。 | 评读：六月关于纵向评价不足的论断不能当作十月空白；后续 R12 已直接研究多轮变化。 | 用作覆盖检查；“文献没测过”须重新核验，不能直接据此宣称新颖性。 |

### 基础机制与关键反证

| 来源 | WHY：问题与前提 | HOW：实际机制 | WHAT：报告的证据 | 局限或反证 | 对 Skill Loom 的影响 |
|---|---|---|---|---|---|
| [R09](https://arxiv.org/html/2305.16291v2) | 开放环境中应复用已学程序，支持后续组合。 | 自动课程、可执行代码技能库、语义检索和环境反馈迭代，验证后入库。 | Minecraft 探索、技术树与新世界任务；有技能库消融。 | 作者：依赖 Mineflayer 高层 API，不能和像素控制直接比较；自验证和 API 生成会出错。 | 持久技能与验证后复用不是新概念；环境接口是迁移条件。 |
| [R10](https://arxiv.org/html/2303.11366v4) | 失败反馈需要转为后续可用的策略记忆。 | Actor/Evaluator/Self-Reflection，把诊断保存在 episodic memory。 | Rust 难题消融：基线 60%，无测试的反思 52%，完整组合 68%。 | 作者：局部最优、记忆窗口与测试表达能力受限；自造测试有假阳性。 | 无证据反思可能有害；每次修复必须对应可检验失败。 |
| [R11](https://arxiv.org/html/2303.17651v2) | 初稿可能改善，但无需每次训练模型。 | 同一 LLM 生成、反馈、修订；任务相关停止条件，实验最多四轮。 | 七类生成任务，自动指标与人类/模型偏好；数学任务增益接近零。 | 作者：需要足够的指令能力，实验仅英语；评读：单次输出改写不等于跨任务技能学习。 | 有界自修正可作候选生成手段，不能自动升级为长期知识。 |
| [R12](https://arxiv.org/html/2608.02636v1) | 更多修订是否有效，以及哪种反馈有效，不能只看前后分数。 | 控制优化器/预算，只改变成败反馈；验证筛选、回退，再冻结评估测试/稳健性/迁移。 | 42 次反馈运行、388 候选，仅 55 个不同内容的新最佳；11 个被选进化版本中 9 个改善测试。 | 作者：未覆盖 SkillsBench。结果中有验证提升而测试下降，反馈排序随模型/任务变化。 | 记录 no-op、拒绝、旧版保留和总成本；预算耗尽不等于验收成功。 |
| [R13](https://arxiv.org/html/2607.01874v1) | 最终产物通过可能掩盖选错技能、漏步骤或额外试错。 | 选择/遵循/组合/检查四维过程 rubric；独立 outcome；校准与验证隔离后接受 rubric 补丁。 | 18 训练任务族、10 测试任务族；50 个测试实例的 human-gold、judge-assisted audit。 | 作者：规模有限，训练仅离线 SFT；评读：筛选偏向技能依赖任务，不代表任意用户工作分布。 | 触发准确率与最终产物分开测；自报“读过/检查过”不能直接计分。 |

## 哪些概念已经有人做过

此表是先例对应，不是对任意论文的完整复现或优劣比较。

| 拟使用的概念 | 直接先例 | 对本项目可写的结论 |
|---|---|---|
| 从执行经验生成持久技能，供新任务复用 | R09、R02、R03 | 已有方法家族；本项目选择其中的外部文件路线。 |
| 根据稳定用户目标更新、合并并版本化技能 | R04 | 已有明确系统先例；用户 profile 是本项目的配置方式。 |
| 失败分析、候选生成、验收、旧版保留 | R02、R07、R12 | 属于有证据筛选的搜索过程；不能称为新发现的闭环。 |
| 多个角色分工生成、评价和维护 | R05、R08、R10 | 分工已有先例；是否值得并发需按实际成本和收益检验。 |
| provenance、准入、维护和 rollback 生命周期 | R06 | 属于已归纳的治理问题，不能以流程图声称首创。 |
| 模型提议，确定性宿主校验后事务写入 | R14 | 已有直接工程机制；本项目须展示自己实现与故障条件。 |
| 跨模型或跨任务迁移 | R02、R05、R07、R09 | 某些迁移已被实测；不能推出所有模型、harness 和任务通用。 |
| 将技能使用过程与最终成功分开评价 | R13 | 可借鉴评价维度；当前 receipt 声明不是过程轨迹标注。 |

目前能合理主张的是：**在明确文件系统与宿主边界下，实现一套可检查、可回退的维护流程，并用列明的故障注入检验其软件性质。** 是否比现有工具更易用、更低成本或更可靠，还需要同条件对照；是否改善 agent 任务成功率，需要另做模型任务实验。

## 从文献到设计：最小可检验模型

下面是本项目的工作性建模，不是新定理，也不表示已经实现了一个学习算法。

把一次运行环境记为 `E = (user_profile, model, harness, tools, permissions, task_distribution, evaluator, budget)`。技能库状态 `L_t` 由内容、版本与来源组成；提议器输出候选 `C_t`，准入器在证据和约束成立时产生 `L_(t+1)`。没有通过准入时，可以保持 `L_(t+1) = L_t`。该模型帮助区分三个对象：

1. **提议质量**：候选是否针对可重复的失败或用户目标。生成更多版本不等于改善。
2. **状态转换正确性**：修改的文件、哈希、来源与恢复路径是否符合审阅内容。这是软件不变量。
3. **行为效用**：在固定环境下，候选是否改善真实任务、成本或用户偏好。这是实验问题。

这个分离与 R06 的生命周期视角、R12 的候选/最佳版本区分相容。它也解释了为什么不能从“apply 成功”推导“skill 更有效”。R14 的结构保证边界提供类似提醒：契约和内容一致性可以部分机器检查，语义效用仍需任务证据。

不同用户应分别定义硬约束和软目标。权限、写入范围、必要工具与必须保持的输出条件属于硬约束；任务适配、成本与维护负担可作为软目标。**先执行硬约束过滤，再比较软目标**是本项目的保守设计选择；当前 profile 权重是用户政策，不是经学习得到的收益预测器。技能格式兼容只覆盖环境元组的一部分，不能替代能力协商、host contract tests 和模型任务测试。

## 应执行的实证计划与反例

以下是由综述推导的后续实验设计，**不是已完成结果**。实验规模应由可承受预算和预先声明的研究问题决定，不能先编造预期提升或统计显著性。

| 层次 | 固定与改变什么 | 必须记录的结果 | 能支持的结论 |
|---|---|---|---|
| 文件系统故障注入 | 固定候选与目标树；注入篡改、缺文件、陈旧状态、意外链接或中途失败 | 正确拒绝/恢复、残留、目标树差异、失败原因 | 指定威胁模型和测试条件下的软件性质 |
| 宿主 contract tests | 固定协议样例；改变能力缺失、事件 payload、重试状态 | 明确降级、终止、错误传播、状态绑定 | 已测试 host/version 的协议兼容 |
| 技能配对效用 | 同模型、harness、工具、任务、预算；比较无技能/旧技能/候选 | 任务级配对差值、负迁移、重试、token、时间 | 对测试任务分布的行为证据 |
| 过程与结果分离 | 同任务与候选；保留可观察 skill reads、工具调用、产物 | 正触发、负触发、漏步骤、输出合格率 | 是否真正使用了技能，而非仅偶然通过 |
| 多轮演化 | 固定提议器和验收集；比较反馈与预算政策 | 接受/拒绝/no-op/最佳轮、谱系、每轮成本、最终冻结测试 | 收益出现在哪里，何时停止较合理 |
| 模型/用户迁移 | 固定候选来源；更换模型版本或用户 profile，并保留独立测试集 | 能力探测、触发/输出回归、偏好冲突、迁移损失 | 明确条件下的可移植性与个性化 |

选择、调参或修订使用的数据不能同时充当最终冻结测试。模型升级后，应重新跑正触发、相邻技能干扰、明确不触发、工具缺失、输出契约、失败恢复及成本案例；host 升级则先检查事件和工具协议。需要支持自更新时，还应检验旧版保留、更新候选隔离、验收器自身变化和失败后的人工接管。这些都是本项目待验证的适配要求，不能由目录格式或版本号自动保证。

反馈比较至少要承认“保留旧版”可以是正确结果。对照中应保留无技能与当前稳定版；如主张迭代优势，再加入等计算预算的重复采样或输出修订控制。不得把 oracle 选出的最佳一次结果当成部署时可自动取得的结果。报告置信区间时应说明重复运行、任务聚类和样本选择；不把每条日志当作独立实验单位。

## 需要在论文和博客中保留的证据边界

- **版本口径**：R01 只引用 v4 汇总。不能混用旧版 86 任务、11 领域、7 配置的结果，也不能把 R05 的 85 任务设置视作同一试验。
- **内部冲突**：R02 的 OfficeQA merge-unique 在 HTML Table 1 为 68.1%，邻近正文、图注和摘要为 67.9%。本综述不替作者选择正确值，也不将该数值用作本项目目标。
- **评价信号可见性**：R05 的 oracle 内容隔离不等于不用 oracle；R13 的过程评分不等于最终 verifier；R14 的 evaluation-free 不等于无需后续行为评价。
- **综述时间窗**：R06 的审计截止是 2026-05-31。R15 的不足判断属于六月语境，不能略过后续研究后继续写作当前空白。
- **项目结果层级**：结构校验、发现列表、事务回退和 receipt 哈希检查，只能支持各自检查范围；receipt 本身不证明命令真正执行、评价器正确或任务收益存在。
- **来源角色**：论文支撑机制和实验论据；官方格式与产品文档支撑包装/API 事实；工程博客支撑实践取舍。三者不能互相替代。本目录的 [engineering-evidence.md](engineering-evidence.md) 单独维护工程来源。
- **当前主张**：Skill Loom 没有在本综述中完成上述论文的复现，没有提供跨模型真实任务提升证据，也没有建立对任意用户或任意 harness 的普遍保证。后续论文和博客应标明工程原型、已测软件性质、设计提议与尚未测的模型效果。



## Incremental review — 2026-10-09 / v0.1.1

[R16: ClaimReceipt](https://arxiv.org/html/2609.01992v1), Peiying Zhu and Sidi Chang,
2 September 2026, was reviewed at Abstract, §2.1, §3.1, §5.4 and §6.
It distinguishes claim sufficiency, experiment coverage and transport integrity.
Its evaluation uses a bounded transaction domain and designed faults; it does not
establish a universal receipt contract. We adopt the distinction as a design
constraint, not its claimed performance or full verifier. See the
[weekly regression report](weekly-2026-10-09.md). This addition does not revise the
original manuscript's fifteen-paper cutoff or imply paper replication.
