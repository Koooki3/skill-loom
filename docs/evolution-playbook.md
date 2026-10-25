# 从任务证据到可持续迭代

Skill Loom 的“自迭代”是一个由 agent 协助、由证据约束的维护闭环：观察任务，定位问题，提出小改动，用真实任务验证，应用，再观察。它不会因为一段日志出现“失败”就改写全局指令，也不会把新安装的数量当成进步。

## 先判断是不是 skill 问题

| 观察 | 首选处理 | 何时值得沉淀为 skill |
|---|---|---|
| 一次性环境依赖缺失 | 修复当前环境，记录可复现命令 | 同类任务反复需要探测与可移植降级 |
| 原始资料没有答案 | 说明证据缺口 | 反复需要相同的来源边界和核验步骤 |
| 总是错选工具或加载过多参考 | 收窄 description、拆分按需引用 | 能用相邻任务验证触发边界 |
| 重复写同一确定性转换脚本 | 提取可测试脚本 | 输入、输出和失败模式稳定 |
| 单个项目有特殊路径/图表配色 | 放项目 skill 或项目说明 | 不应直接泛化到用户级全局 |
| 模型凭空声称部署/实验成功 | 增加可观测验收证据 | 有实际失败案例，并能验证不再误报 |
| 没有观察到某个 skill | 核查样本覆盖和项目需求 | 缺少使用记录不能单独成为删除依据 |

任务过程中的可重构代码、临时 Prompt、项目 AGENTS/CLAUDE 指南、通用 skill 是不同的维护对象。频繁变化的事实属于资料；确定性工作属于脚本；需要反复作出的非显然判断才值得写进 skill。

## 日志观察与隐私

默认从当前任务的失败及验收结果开始，不扫描整台机器。先明确时间窗、项目范围和目的；本地原始会话保留在宿主目录中，公共项目只保存匿名化指标和手工整理的失败分类。

`observe-codex` 只读取显式指定的 JSONL 文件，汇总工具调用、任务事件和宿主报告的 token 总量，不导出提示词、命令、输出、路径和身份。它不把文本中出现某个技能名等同于技能被调用，也不把 `task_complete` 等同于任务质量合格。不同文件可能存在父子任务与重复记录；跨文件 token 求和不是计费审计或节省指标。

```powershell
python -m skillloom observe-codex --log '<one-local-rollout.jsonl>' --out '<private-state>/observation.json'
python -m skillloom events --input examples/events.jsonl --out '<private-state>/events-summary.json'
python -m skillloom suggest --inventory '<private-state>/inventory.json' --events '<private-state>/events-summary.json' --out '<private-state>/proposals.json'
```

`events` 使用固定字段：`skill`、`task_class`、`outcome`、`failure_code`、可选 `duration_ms` 与 `tokens`。其它字段只计数后丢弃。技能名仍可能暴露项目身份，发布前需人工复核或替换为通用名称。没有数据的指标为 `null`，不是零。CLI 不直接把原始日志变成“用户偏好”或自动写入宿主记忆。

建议为一次值得处理的事件，在私有工作目录记录：任务要求、期望产物、实际失败、可复现输入、本地证据位置、是工具/环境/skill/源材料哪一层的问题，以及最小修复。保留原始证据但只共享必要的匿名化复现输入。

`observe-claude` 同样只汇总结构：`Skill` 工具调用是宿主的结构化事件，所以每个技能的调用数是精确的；另有子 agent 派发数和观察日期窗口。`observe-codex` 额外统计工具参数中对 `skills/<name>/SKILL.md` 的语法路径引用（旧字段 `skill_md_reads`）。引用示例代码、审计文本或失败命令也会命中，不能据此证明文件读取、技能使用或任务成功。

`usage` 把宿主清单和观察报告合并，按宿主分别判断：`used`（Claude 的精确调用）、`load-signal`（Codex 的语法路径引用）、`unobserved`、`no-observation`。只有同一份观察报告同时达到 `--min-files`（默认10个输入文件）和 `--min-days`（默认7天首尾跨度）后才列出“复核停用”候选，按描述占用从大到小排序，受保护技能不入列，且只建议移出发现目录、不删除。这是人工复核政策，不是统计置信度、连续监测证明或技能无用的结论。`--min-sessions` 是保留的旧参数别名，实际计数单位仍为文件。

```bash
python -m skillloom observe-claude --log '<transcript.jsonl>' --out '<private-state>/obs-claude.json'
python -m skillloom usage --inventory claude='<private-state>/inventory-claude.json' --inventory codex='<private-state>/inventory-codex.json' \
  --observation '<private-state>/obs-claude.json' --observation '<private-state>/obs-codex.json' --protect skill-lifecycle --out '<private-state>/usage.json'
```

`usage` 会在汇总前校验报告结构、claude/codex 宿主名称、非负整数计数及成对且顺序正确的 YYYY-MM-DD 日历日期。有文件或日期证据的报告必须显式包含宿主对应的技能计数表，表内记录必须提供 calls 和 sessions。未提供日期的空窗口仍可用于展示，但不会达到停用复核门槛。格式错误会返回结构化错误并以状态码 2 退出，不创建或覆盖 `--out` 文件；请修正输入后重试。

两个观察命令会在本次显式选择的输入中，按解析后的文件系统身份跳过重复路径、路径别名和硬链接，输出 `duplicate_inputs_skipped` 与 `counting_unit`。不同文件中的复制内容、同一会话的不同快照或文件内重复事件仍可能被重复计入；`sessions` 字段只是“出现该信号的输入文件数”，不是经核实的独立会话或试验。日期首尾给出的是经过天数，不是有记录的日期数或连续覆盖。

多份报告没有来源成员信息，不能证明互不重叠。`usage` 不相加文件数、不拼接日期窗口，也不相加技能调用；`observed_files`、`span_days` 和每项 calls/sessions 分别取报告中的最大值，不能当作去重后的总量。`window_sufficient` 仍要求同一份报告同时过两项门槛，不能用两个展示最大值重算。任意报告的正向使用信号都保留，包括未达到门槛的小报告。`reports_supplied`/`qualifying_reports` 计数的是传入的汇总报告，不是独立样本。

若多个小报告确实来自不同输入，请显式选择全部文件重新生成一份观察，而不是降低阈值或相加旧报告。旧 schema 1 报告可读，但其 file_count 可能已含重复路径，应重新生成再用于复核。见[计数合同与回归研究](../research/weekly-2026-10-16.md)。

## 持续发现优质开源资源

从 [best-skills](https://github.com/xstongxue/best-skills) 和 [awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) 等索引发现候选，再回到实际维护仓库核对。索引中的链接不继承索引的许可证、可信度或兼容性。星标数和最近提交只是线索。

`catalog/sources.json` 保存本次参考过的固定来源与 commit。`discover` 只比较远端默认分支的当前 SHA，生成候选；网络失败标记 unavailable，不显示“无更新”。

```powershell
python -m skillloom discover --registry catalog/sources.json --out '<private-state>/source-check.json'
python -m skillloom stage --repo xstongxue/best-skills --commit 9aa4e555950da6e43e7d98c5f0c7b70264204850 --path skills/drawio-diagram --destination '<staging>/drawio-diagram'
```

下载工具限定公开 GitHub、完整 commit、仓库相对路径；最多 400 个 skill 文件、20 MiB 内容，单文件 2 MiB。链接、路径穿越、大小写冲突和被截断的目录树会被拒绝。较大的源码仓库可用宿主官方安装器按固定 commit 稀疏暂存，仍需审核后安装。候选的根许可证另存 `upstream-licenses/`，不自动宣布有权重新分发；必须查看子目录是否有另外的条款及归属要求。

对候选检查五类证据：

1. **必要性**：解决哪个已观察到的缺口？现有 skill、内置能力或一段项目文档能否解决？
2. **来源**：维护者、完整 commit、实际 SKILL 路径、许可证、依赖许可证、最近有效维护记录。
3. **行为**：是否改变授权范围、要求无条件联网/付费、自动发布消息、强迫安装软件、改变审批配置？这些内容不因位于 SKILL.md 而获得授权。
4. **可运行性**：工具名、路径、OS、SDK版本和命令是否存在？脚本是否真的能处理目标输入？
5. **成本**：触发描述、正文和参考加载是否必要？适用任务的质量收益是否抵得过新增上下文、等待和维护成本？

决定分为采用、适配、只作参考、延后和拒绝。拒绝记录写具体原因，比如“与内置 PDF 文档生产重叠，且固定工具不可用”，而非“质量低”。

## 自制或适配：用最小可验证修复

先写任务合同，再写 skill。合同包括正向请求、相邻但不应触发的请求、输入材料、输出要求、约束和验收方法。描述只告诉宿主“何时有用”；正文保留非显然判断；场景细节放按需 references；确定性操作放 scripts。

对于已有定制，比较三份内容：上次固定上游、本地当前版本、候选新上游。不能直接覆盖本地版本。保留名称和用户明确指定的 invocation policy、依赖声明、来源规则与作者立场。合并后保存本地补丁、上游 SHA、文件 SHA-256 和改变理由。工具没有自动三方语义合并；由维护者或 agent 评审差异。

适用的优化动作：

| 动作 | 依据 | 验收 |
|---|---|---|
| 新增 | 已有能力不能满足的重复或高价值任务 | 正向任务有效，相邻任务不误触发 |
| 收窄 | 过宽描述或多次误路由 | 触发边界清晰，原适用任务仍通过 |
| 精简 | 重复规则、无条件读取大参考 | 关键约束完整，质量不下降 |
| 合并 | 两个 skill 的输入、决策和验收基本相同 | 名称引用迁移完整，无双入口冲突 |
| 拆分 | 不同输入或授权边界被混在一起 | 使用者无需加载不相关模式 |
| 退役 | 明确不再需要或被已验证能力取代 | 先退役到可恢复记录，检查调用方 |
| 保留 | 场景独立但样本不足 | 标注未验证，避免凭频率删除 |

## 验收不是一张“通过”标签

至少区分四层：静态可读、宿主可发现、脚本/fixture 正确、真实任务产出正确。39 个技能通过静态检查，不代表 39 个服务都已鉴权或实测。

新 skill 的小型任务集应包含：典型正向案例、相邻负向案例、以前失败的回归案例，以及没有参与修改的保留案例。对有副作用的任务先在隔离工作区完成；真实外部发布另按授权范围执行。比较同一输入、同一模型/工具版本下的结果；多 agent 还记录关键路径时间、子任务费用和整合返工。不要只比较字数或单次 token，也不要把并行当作质量证明。

验收表可以包含任务通过率、来源错误数、误触发数、人工修订量、总 token、墙钟时间、重试数。样本少时展示逐例结果，不报告虚假的百分位或统计显著性。任务、模型、环境和变更同时变化时，不能把收益归因于 skill。

## 变更事务与回退

```powershell
python -m skillloom plan --candidate '<staging>/my-skill' --root '<physical-skills-root>' --journal '<private-state>/transactions' --out '<private-state>/plan.json'
# 阅读 plan.json 的变更、before/after哈希及 root，保留输出中的 review_digest。
python -m skillloom apply --plan '<private-state>/plan.json' --digest '<review_digest>'
python -m skillloom inventory --root '<host-discovery-root>' --out '<private-state>/after.json'
python -m skillloom rollback --transaction '<transaction-directory>'
```

计划与摘要必须一起评审；digest 是明确指定所评审文件的校验值，不是数字签名，也不是权限授权。工具对单个 skill 做精确文件变更：提前备份原字节，候选和安装状态改变就停止，安装后复核全文件哈希。中途失败保留 interrupted 事务，`rollback` 可恢复已经发生的部分变更。回退拒绝覆盖后续用户修改或新增文件。每个 skill 独立事务，多技能变更不声称整体原子性；需要跨技能一致性时停用并协调宿主或分阶段发布。

同一用户的恶意进程仍可改写文件；本工具不是沙箱。操作时暂停该目录的其它写入者，保留宿主审批，不解除文件系统保护。发现 `.skillloom.lock` 时核对关联进程与 journal，确定没有运行中的维护后再人工处理，不能自动当“过期锁”删除。

退役使用 `plan --retire <name>`，保留原始文件在 journal；验证引用和可发现目录变化后再决定长期留存。不要清空整个 skills 根目录或插件缓存。对于 junction/symlink，发现检查可读取入口，变更应明确选择其物理根目录。

## 有节奏地维护

维护由证据触发：重复故障、明确新任务、上游相关修复、宿主版本改变、项目结束或已证明能力被替代。可按周查看事件、按月评审来源，但这只是建议；本项目不会创建定时任务。

一次每周迭代的顺序：`observe-claude` / `observe-codex` → `inventory` → `usage`（窗口够再看停用候选）→ `recommend`（新增项目标记带来的缺口）→ 人工复核 → `stage` / `plan` / `apply`。人工判断必须以这些输出为依据：一次“这些技能与项目无关”的手工移除，曾被 `recommend` 发现的 `react`、`next`、`mcp` 依赖推翻。

每轮维护以以下三种结果之一结束：有证据支持的变更并完成验收；没有必要变更；存在明确阻塞和下一步。达到重试/成本上限时记录未完成，不积累无限 hook 循环。没有变化时保持安静，不制造“更新报告”来替代进展。

推荐结果中的 `stage_argv` 是参数数组；调用方替换目标目录占位符后，应直接作为进程参数传入，不要拼接成 shell 字符串。仓库名和固定路径先按 stage 的约束校验。对空格、引号或 shell 元字符等仍合法的目录名，只提供数组并标记 `stage-argv-only`；简单路径另给含带引号占位符的 `stage_command` 模板。模板需要复核并替换占位符后才可执行。普通 Git 目录和 linked worktree 的 gitdir/commondir 可只读提取远端标记；不会启动 Git 或执行配置 includes。

Codex 的 `skill_md_reads` 和 `load-signal` 是兼容旧版的名称：它们只表示工具参数中的语法路径引用，引用示例代码、审计文本或失败命令也可能命中。`skill_signal_basis` 明确标识该来源。不能据此证明文件已读取、技能已执行或任务已通过；真实任务缺口仍需带来源的结果与验收记录。
