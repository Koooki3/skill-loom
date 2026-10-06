# 来源与核验范围

核验日期：**2026-10-06**。这些链接均为官方一手资料；访问时已经打开相关页面正文。OpenAI 的若干 `developers.openai.com/codex/...` 地址现跳转至 `learn.chatgpt.com/docs/...`，表中优先保留实际文档地址，app-server 与插件文档保留官方开发者站地址。

“官网存在某功能”与“某台机器已成功运行”分别记录。官方网页会更新；复现报告应另存宿主版本、项目 commit 和本地输出摘要。本文不是对未安装版本的认证。

新增 [compatibility-contract.md](compatibility-contract.md) 的三层架构、能力状态、用户目标、降级矩阵、contract tests、模型案例和更新流程是**本项目设计**。它们依据已核验的宿主差异制定，不是官方统一配置、现成的能力协商API或已完成的兼容认证。本轮扩展沿用以下来源，没有把其他项目的实现当作本项目已具备的能力。

## 可移植格式

| 编号 | 来源 | 本项目引用的事实 | 不支持的推断 |
| --- | --- | --- | --- |
| S1 | [Agent Skills Specification](https://agentskills.io/specification) | `SKILL.md`、YAML 元数据、目录约定、相对引用和实验性 `allowed-tools` | 每个宿主的发现路径、权限、hooks 或代理配置相同 |

## OpenAI / Codex

| 编号 | 来源 | 本项目引用的事实 | 适用边界 |
| --- | --- | --- | --- |
| O1 | [Build skills](https://learn.chatgpt.com/docs/build-skills) | 当前公开本地发现根、同名不合并、symlink 支持、显式技能使用及可选元数据 | 不证明 `.codex/skills` 已在本机失效；不规定本机所有兼容根的碰撞顺序 |
| O2 | [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) | CLI 启动、独立安装入口和交互使用 | 文档示意界面版本不等于本机版本 |
| O3 | [Using Goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex) | npm 安装示例 `npm install -g @openai/codex@latest` 与版本检查 | 仅用作官方安装命令来源；Skill Loom 不依赖 Goals，也不把该文章的功能起始版本当当前安装版本 |
| O4 | [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | 当前委派触发规则、自定义 TOML 角色、`agents` 设置与旧别名 | 不证明并发必然省 token；不表示示例角色已在本机加载或执行 |
| O5 | [Hooks](https://learn.chatgpt.com/docs/hooks) | 配置位置、信任审核、受支持事件/handlers、输入输出、Stop 继续与终止语义、工具覆盖限制 | 不完整等同于 Claude hooks；也不是全部工具行为的强制安全边界 |
| O6 | [Codex app-server — Skills](https://developers.openai.com/codex/app-server/#skills) | `skills/list`、`forceReload`、按 cwd 扫描和技能输入项 | JSON-RPC 请求不等于 CLI 子命令；需要遵循 app-server 初始化协议 |
| O7 | [Package your plugin](https://developers.openai.com/plugins/build/plugins) | 插件结构、OpenAI 扩展、hooks 资源和信任规则 | 本项目尚未因文档中出现该链接而完成插件打包、提交或上架 |
| O8 | [Submit your Claude Code plugin to OpenAI](https://developers.openai.com/plugins/guides/submit-claude-plugin) | Claude 资源需要按 OpenAI 支持范围适配；命令/代理行为可抽成 skills | 不能把 Claude 配置文件原样当作 Codex 配置 |

OpenAI 页面 O5 自身提醒：主分支 schema 可能领先于当前发行行为。适配优先引用发行文档，再结合本机版本和实际测试；不要只凭最新 schema 宣称旧版本支持。

## Anthropic / Claude Code

| 编号 | 来源 | 本项目引用的事实 | 适用边界 |
| --- | --- | --- | --- |
| A1 | [Advanced setup](https://code.claude.com/docs/en/setup) | 当前系统安装方式、WinGet 包和版本检查 | 本机未执行安装；文档中示例版本不作为本机版本 |
| A2 | [Extend Claude with skills](https://code.claude.com/docs/en/skills) | `.claude/skills` 范围、调用、symlink、同名和插件命名空间规则 | Claude 的扩展 frontmatter 与动态内容行为不自动适用于 Codex |
| A3 | [Create custom subagents](https://code.claude.com/docs/en/sub-agents) | Markdown 代理格式、scope、工具限制、skills 预载、`maxTurns` 和插件限制 | 未在本机运行；单次 `maxTurns` 不保证整个维护流程有限 |
| A4 | [Orchestrate teams](https://code.claude.com/docs/en/agent-teams) | agent teams 为单独的实验机制、启用变量、交互/非交互差异 | 项目不要求开启 teams，也不把面板有多个 agent 等同于已形成 team |
| A5 | [Hooks reference](https://code.claude.com/docs/en/hooks) | 事件、处理器类型、配置范围、退出码/JSON、Stop 防循环及版本说明 | 按事件解读，不能写成“任何非零退出都会阻断” |

## 本机证据

以下记录属于本机样例，不是发布包要求的固定磁盘布局。开源使用者不需要相同用户名、D 盘或已有技能集。

| 检查 | 2026-10-06 所见结果 | 证据边界 |
| --- | --- | --- |
| `Get-Command codex` | 已找到桌面应用管理目录中的 `codex.exe` | 没有再次安装或切换 CLI |
| `codex --version` | `codex-cli 0.160.1` | 本次命令读取 |
| `codex --help`、`codex app-server --help` | 有 app-server、agents、hooks trust 等当前参数 | help 列出不等于每项已做运行测试 |
| `codex features list` | `hooks stable true`、`multi_agent stable true`；`multi_agent_v2 stable false` | 未更改开关 |
| `~/.codex/skills` 直接子目录 | 41 个目录，39 个含直接 `SKILL.md`，其中 24 个为 Junction | 检查了链接目标可读，没有递归迁移 |
| `~/.agents/skills` | 当时不存在 | 不据此否定官方新路径支持 |
| `Get-Command claude` | 当前 PATH 未返回可执行文件 | 不能推出整台机器从未装过 Claude；仅说明未建立可运行的本机测试环境 |
| 既有同日 `skills/list` | 两个 cwd 各 52 项，0 errors、0同名重复；含39自维护、8插件、5 system | 39 个自维护技能均启用；不等于39个真实任务都通过 |

可复查的发现快照：`D:/codex/management/skills-refresh-2026-10-06/discovery-after.json`。该文件为本次项目开始前同日技能维护的已有记录，本次只读解析，没有重新运行其中的发现请求。文件 SHA-256：

```text
BDD6BC24AEC0B67EBADD5780B52E49B99F97E4512468F71AC56CFFFDD53D0D99
```

快照中两个 cwd 分别是本次 Codex 无关联项目的任务目录和 `D:/codex`。原始 `scope=user` 共47项，包含8项插件，故39是按实际自维护目录归类后的数量。Junction 技能条目的 `path` 返回 `D:/codex/skills/.../SKILL.md`。该证据确认当前兼容安装可被发现，但没有测试 `.agents/skills` 与 `.codex/skills` 中同名技能的覆盖顺序。

本次也读取了本地 `openai-docs/SKILL.md` 以采用官方资料工作流。历史维护说明仅用于确定要复查哪些位置，当前事实以以上命令、快照和官方正文为准。

## 尚未完成的宿主验收

以下项目不能由本文的来源检查替代：

- 在新机器安装 Skill Loom，并让两种宿主完成显式触发、隐式触发、负例和真实任务。
- 在本机实际启用 hooks，验证信任、stdout/stderr、返回码、超时、持续失败、用户中断和并发行为。
- 在两种宿主分别运行自定义代理，验证实际工具范围、上下文继承、模型和预算行为。
- 比较 `.agents/skills`、`.codex/skills`、插件及额外扫描根的同名碰撞行为。
- 验证云端/远程环境、旧版宿主及 Windows 之外的端到端安装流程。
- 对每个宿主/harness/模型/用户目标组合运行兼容契约中的C01–C13、T01–T10及代表性任务，并保存实际版本、工具、权限和结果。
- 完成receipt run/candidate/profile与时效约束的完整契约验收；当前已读代码含expected参数和时效校验，但代码存在不等于原生宿主触发已通过。
- 部署并实测持续版本观察、受控promotion及程序自身升级恢复；现有技能文件事务不能替代程序更新器的验收。

项目脚本的离线单测、文件事务演练和本机后续补丁应记录在各自测试报告；没有报告时仍视为未验证。本文没有建立统一 hooks 配置标准，也没有给任何候选技能自动授予安装、发布或扩大权限的资格。

## 项目实现对照

本轮扩展直接对照仓库 `skillloom/cli.py`、`skillloom/gates.py`、`skillloom/strategy.py` 和 `scripts/stop_gate.py`，没有把这些项目选择归为官方宿主能力。已确认：gate的expected run/candidate和时效参数、Stop失败警告、用户profile结构验证，以及doctor仅做环境/PATH初筛。没有在本文工作中执行原生hook或完整模型矩阵；最终测试状态以主流程报告为准。
