# 用户级 Skills 目录（匿名示例）

这份目录是 2026-10-06 本地用户级技能清单的去标识化示例。核对范围包括当前 39 个 SKILL.md、安装清单、维护报告和技能随附的来源/许可证文件。未复制技能正文或大型参考资料；只保留技能用途、触发边界、来源、安装状态与关键依赖，便于迁移时重新评估。

## 计数与安装模型

当前清单有 **39 项：33 项跨项目通用技能和 6 项固定项目范围技能**。 JSON 为检索和 gaps/portfolio 工具另附每项短英文 capabilities 标签。标签表示相邻任务能力，不是自动触发规则；同一能力标签可能对应不同输入、授权边界和验收目标。通用是指不绑定某个仓库或笔记库，不代表适用于所有任务。研究、课程、React、WinUI 等窄领域仍有明确触发条件，见下表。固定范围的技能单列，不能因为名字相近就套用到其他仓库。

本目录记录的是已有的用户级安装状态，不是安装器。现有 39 项由用户级 Skill 发现入口加载；适配自开源上游的项目固定到已记录提交，并保留其许可证与本地修改说明；本地工作流没有伪造上游。对旧技能，若所存文件不能确认仓库和提交，按 unknown/local 标记，不以技能名称猜源。把目录复用于另一账户前，应重新检查来源、许可证、主机能力和项目边界。

安装信息的通用规则：

- Codex 从用户级 Skills 入口发现这些本地目录；复制或迁移时按目标主机支持的用户级安装约定部署。
- 上游适配项应保留来源仓库、提交 SHA、许可证和本地改动边界。local-skills.example.json 中的 upstream 字段只在来源记录可核对时填写。
- 固定项目范围项即使当前放在用户级发现入口，也只能在 scope 指明的项目或工作区触发。不要把它们作为其他用户的通用默认技能分发。
- 本示例不包含私有磁盘路径、用户身份、账户标识、会话历史或技能原文。

source_kind 取值为 pinned_upstream_adaptation（上游和提交可追溯）、known_upstream_unpinned（仓库可知但安装提交未知）、local_authored（本地流程）或 legacy_unknown_local（旧来源无法核验）。许可证状态只陈述保留下来的许可证文本或安装记录可支持的内容；未知不等于无许可证。

## 通用技能（33）

### 研究、学术与课程

| 技能 | 触发与不触发 | 来源、安装与许可 | 依赖 |
|---|---|---|---|
| academic-research-plan | 需要用 WHY/HOW/WHAT 比较研究问题、方法与证据，并形成可执行研究计划时使用；不能把计划写成已做实验，也不适合无来源的自由脑暴。 | 固定上游 Imbad0202/academic-research-skills-codex，提交 70b412fe69d3b5bf6b16adf64a96160bdd3c2d28；CC BY-NC 4.0 已记录，属于选取并本地改编的静态文档。 | 研究问题、可读论文/公开来源；本地资料优先。 |
| nature-experiment-log | 根据实际 ML/机器人实验记录整理可追溯日志，标清计划、观察和异常；不用于编造缺失指标或把实验计划当结果。 | Yuan1z0825/nature-skills，提交 84880815fb37317b3766bff2c2abba395b8993c3；所选组件 MIT 说明与保留的 Apache-2.0 根许可证均有记录。 | 作者提供的实验记录、代码/数据版本、种子、试验单位和指标；模板为随包静态文件。 |
| nature-ref-verifier | 核对 DOI、出版社或 arXiv 记录中的书目元数据并提出 BibTeX 修正；书目身份核验不证明该论文支持正文主张。 | 同一固定 Yuan1z0825/nature-skills 提交；Apache-2.0 文本保留。 | DOI、论文题名或 BibTeX；需要可访问的出版社/DOI/arXiv 页面。 |
| nature-response | 对照评审意见、原稿和实际修改，撰写逐点回复或修订包；不得声称尚未完成的工作已完成，也不以 Nature 默认规则取代目标 venue 规则。 | 同一固定 Yuan1z0825/nature-skills 提交；Apache-2.0 文本保留。 | 审稿意见、当前稿件、真实修改或 diff；目标 venue 要求。 |
| nature-statistics | 用真实实验数据检查独立单位、重复、区间、不确定性、比较和图注；没有数据或实验单位不清楚时只说明缺口，不代算。 | 同一固定 Yuan1z0825/nature-skills 提交；Apache-2.0 文本保留。 | 原始或汇总数据、实验单位和设计；计算工具按任务选择，不要求固定软件。 |
| reference-grounded-writing | 为数字引文稿建立来源证据，核对正文引用与参考文献关系；不代替完整研究论文的论证/行文编辑，也不凭记忆补引用。 | unknown/local；当前本地目录未留下可验证上游提交或许可证来源。 | 稿件片段、引文格式和可读来源；随包检查器仅覆盖其声明支持的完整稿格式。 |
| research-paper-writing | 面向 ML/CV/NLP 稿件改进段落、章节组织和论据衔接；仅润色语言或核验书目身份时分别使用更窄的技能。 | 固定 Master-cai/Research-Paper-Writing-Skills，提交 77e7c2c1ba06f7d71844873147665437a03aac1b；MIT 已记录，属于本地选取改编。 | 真实稿件、目标范围及可支持主张的来源；细节参考按当前章节加载。 |
| scientific-visualization | 用实际数据制作或审查论文图、误差表示、配色与导出；没有数据时不造示例数值，也不把图形美化当作统计审查。 | 固定 K-Dense-AI/scientific-agent-skills，提交 92ace75ac21efe19a620434e0ca4e356081fe807；MIT 已核。 | Python、Matplotlib 和实际数据；图表风格/期刊约束按交付要求选用。 |
| source-grounded-course-notes | 为课程 PDF、讲义、转录整理有页码依据的双语笔记、复习提纲和练习；不是通用论文写作或对来源缺失内容的补写。 | 本地工作流；无上游。当前作为用户级技能安装，适用于课程资料工作区。 | 课程原件；PDF 先转换为 Markdown，再回看原页面核对公式和图；按环境选择 PDF/Markdown 工具。 |

### 文档、表达与 Skills 维护

| 技能 | 触发与不触发 | 来源、安装与许可 | 依赖 |
|---|---|---|---|
| codegen-doc | 根据实际仓库代码撰写系统论文章节、技术难点、项目汇报或简历经历；新人上手、构建和调试文档优先 project-docs。 | 固定 xstongxue/best-skills，提交 9aa4e555950da6e43e7d98c5f0c7b70264204850；Apache-2.0。 | 可读取的源代码、配置和作者给定的目标格式；仓库证据是事实来源。 |
| engineering-thesis-tone | 撰写或润色中文工程学位论文，保持定义、客观语气和作者立场；不替作者扩展事实或替代来源核验。 | local_authored；无可核验上游。 | 作者稿件、术语表与事实来源；无需额外运行时。 |
| md-report-summary | 根据作者记录和可访问项目证据写周报、进展汇报或复盘；不能用网上新闻替代个人工作事实。 | 固定 xstongxue/best-skills，提交 9aa4e555950da6e43e7d98c5f0c7b70264204850；Apache-2.0。 | 实际日志、草稿或项目记录；不依赖运行环境。 |
| project-docs | 为代码仓库写新人上手、架构、代码导读、构建和调试文档；代码到论文/简历叙述则用 codegen-doc。 | 固定 xstongxue/best-skills，提交 9aa4e555950da6e43e7d98c5f0c7b70264204850；Apache-2.0。 | 仓库 README、代码和构建入口；仅检查请求范围内的文件。 |
| shuorenhua | 用户要求“说人话”、去 AI 味、审稿或中英文语言优化时使用；保留事实、术语、数字、条件、来源和作者立场，不套用到代码、日志、配置或命令输出。 | 固定 MrGeDiao/shuorenhua，提交 9e6400d5e2cc050485c38fbf0dda682bce66c180；MIT 文本保留，按本地清单记录。 | 要编辑的文本与用户指定范围；纯文本工作，无附加运行时。 |
| skill-prompt-convert | 把已有 SKILL.md 与聊天 Prompt 做格式转换并说明约束、工具和资源依赖；不是完整技能创作、安装或技能体系维护。 | 固定 xstongxue/best-skills，提交 9aa4e555950da6e43e7d98c5f0c7b70264204850；Apache-2.0。 | 输入的 Skill 或 Prompt；输出目标格式与调用环境说明。 |
| skills-maintenance | 用户要求盘点、安装、更新或修复用户 Skills 时使用；普通技能调用不应触发维护，也不应擅自修改全局配置。 | 本地维护流程；无上游。技能安装/创作必要时依赖宿主的 skill-installer、skill-creator。 | 当前用户技能清单、版本/来源和授权的维护范围；安装或升级前核对来源及许可证。 |

### 图示与可编辑图稿

| 技能 | 触发与不触发 | 来源、安装与许可 | 依赖 |
|---|---|---|---|
| codegen-diagram | 从实际代码、配置或数据库 schema 取证绘制技术栈、架构和 E-R 图；概念教学图、自由创作图不触发。 | 固定 xstongxue/best-skills，提交 9aa4e555950da6e43e7d98c5f0c7b70264204850；Apache-2.0。 | 仓库源文件/schema；需要可编辑交付时使用 .drawio 兼容编辑器。 |
| drawio-diagram | 用户需要可编辑 Draw.io 的模型、算法、教学示意或参考图风格迁移时使用；代码或数据库驱动的系统图用 codegen-diagram。 | 固定 xstongxue/best-skills，提交 9aa4e555950da6e43e7d98c5f0c7b70264204850；Apache-2.0。 | 目标图的概念/参考；Draw.io 兼容编辑器用于打开和编辑。 |
| excalidraw-diagram | 用户明确需要 Excalidraw 或手绘风白板、架构图和流程图时使用；普通静态工程图可选 Mermaid/Draw.io。 | 固定 xstongxue/best-skills，提交 9aa4e555950da6e43e7d98c5f0c7b70264204850；Apache-2.0。 | 图意与可选参考；Excalidraw 兼容应用用于预览/编辑。 |

### 界面与媒体

| 技能 | 触发与不触发 | 来源、安装与许可 | 依赖 |
|---|---|---|---|
| imagegen-api | 只有用户明确要求 OpenAI Images API、脚本或批处理时才用；普通生图/改图走宿主图像能力，不要求额外配置 API。 | legacy_unknown_local；保留的本地 Apache-2.0 文本可读，但未记录可验证上游仓库/提交。 | 用户明确选择的 API 流程、可用 API 凭据和 Python/API 客户端；普通图像任务无此依赖。 |
| oil-motion | 有主体连续变化的网页动画，需用视频/序列帧跟随滚动、拖动或状态输入时使用；普通 CSS 过渡、独立成片剪辑或单张配图不触发。 | 可识别公开仓库 oil-oil/oil-motion；安装提交未记录，MIT 许可证文件保留。 | 本地媒体处理需 Python 3.10+ 与 FFmpeg；API/Node 配置链仅在用户选用时需要相应环境与授权。 |
| oil-ui | 用户要探索、精修或评审真实界面的视觉方向、层级和响应式画面时使用；业务逻辑/可访问性需另行验证。 | 可识别公开仓库 oil-oil/oil-ui；安装提交未记录，MIT 许可证文件保留。 | 现有界面、品牌材料或浏览器截图；无额外运行依赖。 |
| pdf-local-ops | 本地 PDF 的文本/表格提取、拆页、合并、旋转和 OCR 准备；排版新 PDF、表单和视觉交付走宿主 PDF 能力。 | legacy_unknown_local；本地 Apache-2.0 文本保留，原上游仓库/提交未知。 | 本地 PDF 与可用提取/OCR工具；不因任务自动安装工具。 |

### 工程与工具

| 技能 | 触发与不触发 | 来源、安装与许可 | 依赖 |
|---|---|---|---|
| gh-address-comments | 用户指定处理 PR 评审意见时读取评论并实现修正；不自动回复、发布评论或解决讨论线程。 | 固定 openai/skills，提交 49f948faa9258a0c61caceaf225e179651397431；该组件 Apache-2.0 文件已核。 | 有仓库权限的 GitHub 连接器或已认证 gh；仅用户授权的仓库操作。 |
| gh-fix-ci | GitHub Actions 检查失败时读取日志、定位并修复；普通本地测试失败或 CI 运行正常时不触发。 | 同一固定 openai/skills 提交；该组件 Apache-2.0 文件已核。 | 已认证 GitHub CLI gh、目标仓库和 Actions 日志。 |
| jupyter-notebook | 创建或修改实验、探索和教程 Notebook，并按项目模板检查结构；不用于普通 .py 脚本或只需阅读数据时。 | legacy_unknown_local；本地 Apache-2.0 文本存在，但旧来源/提交未确认。 | 现有 Python 与 Notebook 模板；需要执行时再确认 Jupyter/相关包是否可用。 |
| mcp-builder | 开发或修改 Python/TypeScript MCP 服务的工具 schema、传输、鉴权和错误处理；已有连接器的使用或 Site 托管不触发。 | 固定 anthropics/skills，提交 683bc88e56f3e09ba94f7055977f3d3aa499f202；Apache-2.0 已核。 | 与目标实现匹配的 Python/Node、MCP SDK 和服务项目。 |
| team-mode | 只在独立探索、实现、评审或专家判断有净收益时按 SOLO/ONE/TWO 路由；短任务、串行依赖或共享一个改动目标默认 SOLO。 | local_authored；本地团队路由流程，无上游。 | Codex 支持自定义子代理；本地使用量诊断另需 Python 3.10+ 与保留的会话日志。 |
| vercel-composition-patterns | React 组件 API、布尔属性、复合组件和共享状态重构；不用于非 React 或纯 CSS 视觉任务，React 19 专属做法先核版本。 | 固定 vercel-labs/agent-skills，提交 063bee94c3f4df8453406c830b0a7df0f2860278；MIT 声明见上游技能元数据。 | React 项目及其实际版本；仅加载命中的规则。 |
| vercel-react-best-practices | React/Next.js 请求瀑布、包体积、服务端/客户端取数、重复渲染和性能审查；不用于普通静态页面设计。 | 同一固定 vercel-labs/agent-skills 提交；MIT 声明见上游技能元数据。 | React/Next.js 项目、当前框架版本和能验证性能问题的证据。 |
| web-accessibility | 检查或修复键盘、焦点、语义、替代文本、对比度和读屏体验；不以一次检查宣称 WCAG 合规认证。 | 固定 addyosmani/web-quality-skills，提交 afa8da942115f2961fdbfa80807ea0b232ff6c00；MIT 已核。 | 页面/组件代码；键盘与屏幕尺寸检查，读屏验证按任务范围进行。 |
| winui-app | Windows App SDK / WinUI 3 的环境排查、新应用启动、现代 Windows UX、实现或评审；不适用于跨平台 .NET 或 Web UI。 | legacy_unknown_local；Apache-2.0 文件保留，来源仓库/提交未确认。 | Windows 与现有 .NET/Windows App SDK 工具链；当前 API 规则需查 Microsoft 文档。 |
| yeet | 仅在用户明确要求一并暂存、提交、推送并创建 GitHub PR 时使用；普通代码修改、review 或仅创建本地提交不触发。 | legacy_unknown_local；Apache-2.0 文件保留，来源仓库/提交未确认。 | Git 仓库、目标分支和已认证 gh；只包含任务范围文件。 |

## 固定项目范围技能（6）

以下技能有硬性工作区边界，不能安装为跨仓库默认路由。当前清单虽以用户级方式发现，但触发前必须确认项目身份。

| 技能 | 固定范围与触发 | 来源/安装 | 依赖 |
|---|---|---|---|
| dataset-from-existing-impl | 仅在复用指定目标检测实现的数据集结构、标注转换、YAML、分割校验或训练准备模式时触发；不把它当所有数据集的通用标准。 | 本地项目工作流；无可核验上游。用户级发现，触发文案限定在匹配的数据工作区。 | 目标数据及现有数据集实现；Python/标注工具依目标项目已有环境。 |
| obsidian-task-dashboard-dev | 仅在绑定的 Obsidian vault 内新增或重构任务仪表盘、Dataview 查询、日模板注入、固定任务同步和样式时触发。 | 本地特定 vault 工作流；无上游。用户级发现但 vault 范围固定。 | Obsidian 与 Dataview/DataviewJS 插件、vault 内对应笔记/脚本。 |
| obsidian-task-dashboard-maintenance | 仅在同一 vault 的仪表盘空白、格式异常、同步失败、模板任务进入统计或日常维护时触发；不维护其他 Obsidian vault。 | 本地特定 vault 工作流；无上游。用户级发现但 vault 范围固定。 | 同上；需读取本地错误与相关 Dashboard/日记数据。 |
| train-test-script-scaffold | 仅在为匹配项目新增训练/推理/测试脚本，并要求复用仓库的 train*.py / test*.py 约定时触发；不把某个项目结构推给其他代码库。 | 本地项目模板；无可核验上游。用户级发现但以当前仓库为边界。 | 目标仓库现有脚本、参数和输出布局；项目 Python 工具链。 |
| yolo-pcb-chart-palette | 仅在固定的 YOLO_PCB 工作区创建或更新训练图、对比图、热力图、图例或论文图时触发；其他仓库使用自身图表规范。 | 本地项目配色规则；无上游。用户级发现但仓库范围固定。 | 该仓库配色规则与绘图入口，通常是 Python/Matplotlib。 |
| yolo-pcb-readme-maintainer | 仅在同一 YOLO_PCB 工作区做训练、数据处理、分析、导出、修复或清理时触发；先读该项目 README，再按影响更新项目维护记录。 | 本地项目维护流程；无上游。用户级发现但仓库范围固定。 | 该工作区 README、目标源码/配置/数据和现有构建或测试入口。 |

## 宿主提供的 System 与插件能力（不属于这 39 项）

以下能力由 Codex 或已连接插件提供。目录只记录它们的路由关系，不复制其专有 SKILL.md、内部指令或实现：

| 宿主能力示例 | 路由边界 |
|---|---|
| System：imagegen、skill-creator、skill-installer、openai-docs | 普通图像生成/编辑用 imagegen；完整技能创作和安装分别使用 system skill。不要把 system 技能复制成本地用户技能。 |
| 文档插件：documents、pdf、presentations、spreadsheets | Word/PDF视觉交付、演示文稿、工作簿等需要原生格式/布局的工作，使用相应宿主能力；pdf-local-ops 只负责本地提取与页面操作。 |
| Sites、Google Drive、浏览器和安全插件 | 只有用户任务触发时使用对应已连接插件；本清单不包含插件权限、凭据或服务状态。 |
| 原生 Codex 工具与应用连接器 | 文件、Git、浏览器、GitHub/MCP 等操作取决于当前任务实际暴露的接口和登录状态；清单不保证外部服务可用。 |

生成或迁移前再次确认目标运行时、权限和插件是否存在。这个 JSON 是供讨论和路由示例使用的匿名快照，不会自行安装、更新或启用任何能力。