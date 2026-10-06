# Codex 与 Claude Code 宿主适配

核验日期：**2026-10-06**。本文面向本地 Codex 和 Claude Code；云端执行环境需另行验证文件、依赖和策略是否可用。官方网页是随版本更新的文档，不是对所有旧版本的兼容承诺。来源及本机证据见 [sources.md](sources.md)。

本文区分三种陈述：**官方能力**指已读取的官方文档；**本项目约定**指 Skill Loom 的工程选择；**本机证据**指本次只读检查或已有可复查记录。没有执行的安装、hook 和 Claude Code 流程明确列为未实测。

## 1. 可移植的部分

**官方能力。** Agent Skills 的共同单元是一个含 `SKILL.md` 的目录。可移植版本使用 YAML `name`、`description`，正文用 Markdown；脚本、引用和资源保留在技能目录内，以相对路径引用。`name` 应与目录名一致；`allowed-tools` 在标准中仍属实验字段，不能假定不同宿主会给它相同的权限效果。[Agent Skills 规范](https://agentskills.io/specification)

**本项目约定。** Skill Loom 将内容维护与宿主控制分开：

- `skills/skill-lifecycle/`：共同的维护流程和证据要求。
- Python CLI：盘点、生成计划、核对摘要、应用和回退；不需要模型参与文件事务。
- 宿主适配：负责发现位置、显式调用写法、代理定义及可选 hooks。
- 运行证据：说明检查对象、版本、结果和未测项；“发现成功”不能替代真实任务验证。

不要在共同技能中要求某个宿主专有的工具名、`$ARGUMENTS` 展开、动态命令注入、`context: fork` 或具体模型名。确需使用时，在独立宿主说明中设置，并给共同技能保留普通文本输入和串行执行路径。`SKILL.md` 可移植不代表 hooks、subagents 或配置文件也具有统一标准。

### 1.1 通用性需要分层验证

**本项目设计。** 跨宿主支持分为三层：最小公共内核负责维护状态和证据；宿主适配层处理发现、工具调用、权限、事件和代理；模型任务测试检查真实触发、约束遵循和输出质量。只有某个“宿主版本 + harness版本 + 模型标识 + 本地策略 + 技能版本”组合通过对应测试，才可在该范围内声明支持。复制目录、frontmatter 解析成功或一次回答正确都不构成通用性证明。

启动时先读取宿主公开的版本、当前工具清单和实际允许范围，再选择执行路径。工具名出现在官方文档中、CLI 中存在相应参数、当前会话能调用它、调用达到预期效果，是四个不同层次的证据。未知能力保持 unknown；没有 hooks 就用显式 CLI gate，没有 subagents 就串行执行，没有可写事务目录就只生成报告，不自动扩大权限。当前 `doctor --profile <USER_PROFILE> --out <REPORT>` 只验证用户profile结构、读取OS/Python版本并检查 `codex`、`claude`、`git`、`node` 是否在PATH；它不启动宿主、不探测特性，也不证明这些工具能成功执行任务。

具体能力清单、降级矩阵、contract tests、模型升级测试和上线更新流程见 [compatibility-contract.md](compatibility-contract.md)。该文档的能力记录格式是项目设计，不是 Codex、Claude Code 或 Agent Skills 的官方配置，也不是当前 CLI 已自动实现的探测协议。

## 2. 快速差异表

| 项目 | Codex | Claude Code |
| --- | --- | --- |
| 新项目技能入口 | 从工作目录向仓库根扫描 `.agents/skills/` | 对应范围的 `.claude/skills/`；子目录还具有按访问发现的行为 |
| 当前官方个人技能位置 | `~/.agents/skills/` | `~/.claude/skills/` |
| 本机已有 Codex 入口 | `~/.codex/skills/` 当前仍被发现，含实体目录和 Junction；不据此推断所有版本 | 本机 PATH 未找到 `claude`，未验证其发现行为 |
| 显式调用 | `$skill-lifecycle` | `/skill-lifecycle`；插件技能通常有插件命名空间 |
| 同名技能 | 官方说明不会合并，多个定义可出现在选择器中；不要依赖未验证的路径覆盖顺序 | enterprise 高于 personal，高于 project；插件命名空间及嵌套目录另有规则 |
| 项目规则 | `AGENTS.md` | `CLAUDE.md` |
| 自定义代理 | `.codex/agents/*.toml` 或 `~/.codex/agents/*.toml` | `.claude/agents/*.md` 或 `~/.claude/agents/*.md`，YAML frontmatter 加 Markdown |
| 项目 hooks | `.codex/hooks.json` 或 `.codex/config.toml` 的 `[hooks]` | `.claude/settings.json` / `.claude/settings.local.json` 的 `hooks` |
| 本地 hook 处理器 | `command`、`mcp_tool`；`prompt`、`agent` 当前解析后跳过 | 按事件支持 `command`、`http`、`mcp_tool`、`prompt`、`agent`，并非每种事件都支持全部类型 |

路径、调用和同名行为依据 [Codex Skills](https://learn.chatgpt.com/docs/build-skills)、[Claude Code Skills](https://code.claude.com/docs/en/skills)；代理及 hooks 分别依据下文链接。表中 `~/.codex/skills` 是本机兼容行为，不是“唯一正确位置”，也不与 `~/.agents/skills` 声称具有相同优先级。

## 3. 最小安装与发现检查

### 3.1 宿主与工具运行时

先检查已有安装，避免在桌面应用已管理 CLI 的机器上重复安装：

```powershell
Get-Command codex -ErrorAction SilentlyContinue
codex --version
Get-Command claude -ErrorAction SilentlyContinue
python --version
```

**官方安装入口。** 已有 npm 环境的新机器可以使用以下 Codex 安装命令；正式记录应保存实际版本，后续升级明确选择版本，而不是每次复现时重新取 `latest`。[OpenAI 官方安装示例](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)

```powershell
npm install -g @openai/codex@latest
codex --version
codex
```

Claude Code 的 Windows 包管理器示例：

```powershell
winget install Anthropic.ClaudeCode
claude --version
claude
```

macOS/Linux 的官方独立安装入口分别为 `https://chatgpt.com/codex/install.sh` 和 `https://claude.ai/install.sh`，具体执行方式及当前平台要求见 [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) 和 [Claude Code setup](https://code.claude.com/docs/en/setup)。登录按宿主自己的界面进行；Skill Loom 不读取或复制凭据。本项目未执行以上宿主安装命令。

在已经取得的 Skill Loom 仓库根目录安装项目依赖；不假设项目已经发布到 PyPI 或某个 GitHub 地址：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m skillloom --help
```

Linux/macOS 将解释器路径替换为 `.venv/bin/python`。CLI 的 Python 版本和依赖以仓库 `pyproject.toml` 为准。`pip install -e .` 是开发安装；部署记录还应保存仓库 commit、依赖版本和候选技能文件摘要。

### 3.2 先选实体安装根目录

**本项目约定。** 选择一个实体、专用的技能根目录。新 Codex 用户可选官方个人路径；Claude Code 用户改为 `.claude/skills`。如果该路径或待修改技能是 symlink/Junction，先识别实体位置，不能直接按下面的示例写入链接入口。

```powershell
$loomPython = Join-Path (Get-Location) '.venv\Scripts\python.exe'
$hostSkills = Join-Path $env:USERPROFILE '.agents\skills'
# Claude Code 改为：
# $hostSkills = Join-Path $env:USERPROFILE '.claude\skills'
$loomState = 'D:\codex\state\skill-loom\first-install'
New-Item -ItemType Directory -Path $hostSkills -Force | Out-Null
New-Item -ItemType Directory -Path $loomState -Force | Out-Null

& $loomPython -m skillloom inventory --root $hostSkills --out "$loomState\inventory.json"
& $loomPython -m skillloom plan --candidate skills/skill-lifecycle --root $hostSkills --journal "$loomState\journal" --out "$loomState\plan.json"
Get-Content -LiteralPath "$loomState\plan.json"
```

如果创建或 inventory 失败，先修正路径和写入权限，再继续生成计划。候选、安装根和 journal 必须彼此分离。状态目录可替换为自己可写的本地目录；不要把 journal 放入被宿主扫描的技能目录。

检查计划中的目标、文件差异和摘要后，把 `plan` 输出的 `review_digest` 原样传给 `apply`：

```powershell
# 将占位内容替换为刚审阅计划对应的实际摘要。
& $loomPython -m skillloom apply --plan "$loomState\plan.json" --digest '<PLAN_DIGEST>'
```

回退时使用 `apply` 返回的事务目录：

```powershell
& $loomPython -m skillloom rollback --transaction '<TRANSACTION_DIRECTORY>'
```

这些是本项目 CLI，不是 Codex 或 Claude Code 的原生命令。摘要用于绑定审阅过的计划；它不等于人工审批，也不扩大宿主权限。若计划后文件已改变，应重新生成计划；不能把不匹配的当前状态强行覆盖。执行前以本版本 `--help` 和测试结果核对参数。

### 3.3 确认宿主加载了哪个文件

Codex 中显式输入 `$skill-lifecycle` 并要求先报告加载的 `SKILL.md` 路径。自定义客户端可在已完成 app-server 初始化后发送：

```json
{
  "id": 25,
  "method": "skills/list",
  "params": {
    "cwds": ["D:/codex/projects/example"],
    "forceReload": true
  }
}
```

检查 `errors`、技能 `path`、`enabled` 和重复名称。它是 app-server 请求，不是 shell 中可直接执行的 `codex skills/list` 子命令。官方还提供按 cwd 传入额外用户根的 `perCwdExtraUserRoots`；客户端的一次额外扫描不等于永久安装。[Codex app-server Skills](https://developers.openai.com/codex/app-server/#skills)

Claude Code 中输入 `/skill-lifecycle`，确认加载路径；也可用自然语言触发并核对是否选中预期技能。未知版本和刚创建的目录统一用新会话验收，不把“可能自动热更新”作为成功证据。至少保留一个应触发场景和一个相邻但不应触发的场景，检查后者没有开始维护其他技能。

## 4. 代理调度是宿主适配层

**官方能力。** 当前 Codex 默认提供 subagents；在用户或适用的 `AGENTS.md` / skill 指令请求时进行委派。自定义角色使用 TOML，核心字段为 `name`、`description`、`developer_instructions`。并发上限使用 `agents.max_concurrent_threads_per_session`；旧 `max_threads` 仍是别名。没有指定时模型配置可继承父代理。[Codex Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

以下是可审阅的项目示例，不是安装脚本，也不会由 Skill Loom 自动写入全局配置。已有 `[agents]` 表时合并字段，不能再追加第二个同名表。

```toml
# .codex/config.toml
[agents]
enabled = true
max_concurrent_threads_per_session = 1
```

```toml
# .codex/agents/skill-auditor.toml
name = "skill-auditor"
description = "用户要求技能审计时，独立检查来源和触发边界。"
sandbox_mode = "read-only"
developer_instructions = """
只读审查指定候选技能。返回证据路径、明确问题和未验证项。
不得修改安装目录，不得安装依赖，不得应用或回退事务。
"""
```

Claude Code 对应角色用 Markdown 文件：

```markdown
---
name: skill-auditor
description: 用户要求技能审计时，独立检查来源和触发边界。
tools: Read, Glob, Grep
model: inherit
maxTurns: 6
---

只读审查指定候选技能。返回证据路径、明确问题和未验证项。
不得修改安装目录，不得安装依赖，不得应用或回退事务。
```

保存为 `.claude/agents/skill-auditor.md`。Claude Code 会按 `description` 选择代理，也可显式要求委派。其 `skills` 字段可以预载技能正文；这不同于把技能名简单列进 `tools`。`maxTurns` 是单次代理轮次限制，达到限制后的结果可能不完整，不能把它当作总预算保证。插件内代理还会忽略 `hooks`、`mcpServers`、`permissionMode` 等部分字段。[Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)

**本项目约定。** 用同一个轻量调度门描述任务，不使用统一的虚构代理配置：

- `SOLO`：短任务、顺序依赖、只有一个可变技能目标时采用。
- `ONE`：一个独立审计者可以工作，主代理同时有实质工作时采用。
- `TWO`：两个互不重叠的交付物都能满足 `ONE` 条件时采用。

每个子任务必须写清输入、交付物、文件所有权和禁写范围。主代理独占 `plan/apply/rollback` 和最终验收；审计者不碰同一安装根。若宿主提供历史继承选项，优先传最少所需上下文；没有该选项时在任务提示中显式给出证据和约束，不能假设子代理已读完父对话。宿主不支持多代理时按同样清单串行检查。

Claude Code 的 **agent teams** 与单会话 subagents 是不同机制：当前仍标为实验，需显式启用 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`，且交互会话与 `-p` 的行为不同。Skill Loom 不要求、也不默认打开 agent teams。[Claude Code Agent teams](https://code.claude.com/docs/en/agent-teams)

## 5. Hooks 与 gates

### 5.1 官方能力与边界

Codex 官方当前列出的本地事件包括 `SessionStart`、`SessionEnd`、`SubagentStart`、`PreToolUse`、`PermissionRequest`、`PostToolUse`、`PreCompact`、`PostCompact`、`UserPromptSubmit`、`SubagentStop`、`Stop` 和 `Interrupt`。hooks 会合并而非按高优先级层覆盖；匹配处理器可并发运行。非托管 hooks 需审核并信任当前定义，改变后可能重新待审。[Codex Hooks](https://learn.chatgpt.com/docs/hooks)

Claude Code 除常见事件外还有 `PostToolUseFailure`、`StopFailure`、`TeammateIdle`、`TaskCreated`、`TaskCompleted`、`ConfigChange`、worktree 及其他事件。不要把这些名称直接写入 Codex 配置，也不要把五种 Claude hook 类型全部移植过去。最新事件及字段应按 [Claude Code Hooks reference](https://code.claude.com/docs/en/hooks) 核对。

| 意图 | 需要的契约 | 不能据此推断的结论 |
| --- | --- | --- |
| 阻止尚未执行的受支持工具 | 在 `PreToolUse` 使用宿主支持的 deny JSON；简单命令 gate 可用退出码 `2` 和 stderr | 退出码 `1`、超时、错误 JSON 会自动安全阻断 |
| 检查已经执行的操作 | `PostToolUse` 反馈检查结果 | 返回 block 能撤销已发生的写入 |
| 要求再做一次修复 | `Stop` 输出 `decision: "block"` 和 `reason` | block 表示结束任务，或者宿主会无限安全重试 |
| 完成或失败升级后结束 | 成功时退出 `0`、不请求继续；失败上限采用明确终止输出 | 允许停止等于验证通过 |
| 异步记录 | 使用宿主支持的 async 形式 | 异步 hook 能及时决定原工具是否执行 |

当前 Codex `PreToolUse` 不支持 `permissionDecision: "ask"`，也不能用 `continue: false` 充当该事件的阻断返回；不支持的字段可能导致 hook 失败后工具继续。Claude Code 的 `PermissionRequest` 也不能一概用退出码 `2` 拒绝，需其事件专用 decision 对象。**gate 实现必须逐事件映射，不能只比较退出码。** 上述契约来源仍是两家的 hooks reference，项目仅选择其中最小的同步命令子集。

### 5.2 只连接已有的检查结果

**本项目约定。** `Stop` hook 读取显式指定的本地 receipt，检查任务所要求的验证是否完成。它不自安装依赖、不访问凭据、不修改宿主设置，也不自动发布或应用技能候选。

以下为“生成后供审阅”的可选配置；本文未将它们写入任何宿主目录。绝对路径必须替换为本机已验证的解释器、脚本和 receipt，不能把示例路径原样用于另一台机器。

Codex：项目 `.codex/hooks.json` 示例。

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /opt/skill-loom/scripts/stop_gate.py --receipt /var/tmp/skill-loom/run-001/receipt.json --profile skill-change --expected-run-id run-001 --expected-candidate-digest REPLACE_WITH_CANDIDATE_DIGEST --max-age-hours 24",
            "commandWindows": "powershell.exe -NoProfile -Command \"& 'D:/codex/projects/skill-loom/.venv/Scripts/python.exe' 'D:/codex/projects/skill-loom/scripts/stop_gate.py' --receipt 'D:/codex/state/skill-loom/run-001/receipt.json' --profile skill-change --expected-run-id 'run-001' --expected-candidate-digest 'REPLACE_WITH_CANDIDATE_DIGEST' --max-age-hours 24\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

Claude Code：将以下内容**合并**到项目 `.claude/settings.local.json`，不要覆盖该文件的其他设置。这里显式启动 PowerShell；不依赖 hook 运行时恰好选中了哪种 shell。

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -NoProfile -Command \"& 'D:/codex/projects/skill-loom/.venv/Scripts/python.exe' 'D:/codex/projects/skill-loom/scripts/stop_gate.py' --receipt 'D:/codex/state/skill-loom/run-001/receipt.json' --profile skill-change --expected-run-id 'run-001' --expected-candidate-digest 'REPLACE_WITH_CANDIDATE_DIGEST' --max-age-hours 24\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

先将 `run-001` 和 `REPLACE_WITH_CANDIDATE_DIGEST` 替换为本次维护流程独立确定的run ID及候选摘要，再写入配置。`review_digest` 是整个计划的摘要，不能未经定义就当作候选内容摘要使用。更新候选或开始新的run后，expected值也应经核对后更新。

Claude Code 的 Linux/macOS 示例可把 `command` 换为 Codex 示例中的 POSIX 命令，但保留 Claude 自己的配置位置。Codex 的 `commandWindows` 是本宿主字段，不假定 Claude 支持。插件分发时路径还需改成插件安装根；仅安装插件并不意味着脚本依赖已经部署或 hooks 已获信任。[OpenAI 插件打包](https://developers.openai.com/plugins/build/plugins)

### 5.3 有界继续与失败升级

**实现状态。** 已对照当前 `gates.py`、CLI参数和 `scripts/stop_gate.py` 同步。本节是实现说明；原生宿主触发、信任与完整测试结果仍需独立验收。

**本项目约定，非宿主保证。** 最小策略只允许一次自动修复继续：

| 检查结果 | receipt 状态 | Stop 返回 |
| --- | --- | --- |
| 所有必要检查确实通过 | 保留检查证据及通过状态 | 退出 `0`，不请求继续 |
| 首次失败，仍在已授权范围内可修复 | 保留失败项 | `{"decision":"block","reason":"…具体待修复项…"}` |
| `stop_hook_active` 为 true，仍未通过 | 保留失败，主代理负责说明未完成 | 返回含未验证警告的 `systemMessage`，无 `decision`，不再请求继续 |
| receipt 缺失或无法解析 | 检查不可用，绝不补造通过结果 | 退出 `1`，输出未验证 `systemMessage` 和 stderr 诊断，不再请求继续 |
| 用户中断 | 保留中间状态 | 不重新启动任务 |

这里的“保留失败”指不把原 receipt 改成通过，不代表脚本已写入一份新的失败日志。`systemMessage`用于宿主可见警告，stderr的展示仍取决于宿主和事件；应检查实际日志，并用CLI验收结果作为最终报告依据。不返回 `decision` 只表示本hook允许停止；若还有其他Stop hooks，它们仍可能请求继续。

当前gate校验必要check ID、声明状态和证据文件SHA-256。CLI可选参数 `--expected-run-id`、`--expected-candidate-digest` 会分别比较receipt的 `run_id`、`candidate_digest`；`--max-age-hours` 会要求带时区的 `created_at`，拒绝未来时间、过期或无效时间。声明了不同的 `profile` 会失败；为兼容早期receipt，当前实现允许该字段缺失，生产流程应显式写入它。

`scripts/stop_gate.py` 将前两个expected参数设为必填，时效上限默认24小时。CLI不传这些参数则不执行相应绑定/时效检查，不能据此声称已验证当前run。调用端必须独立确定预期run和候选摘要，不能从待验证receipt复制expected值；否则只是文件自证一致。摘要应由维护流程从固定候选计算，算法和输入需写入本地运行记录。

这些校验不执行任意验收命令，不判断报告中的结论是否真实或测试是否充分，也不自动验证模型/harness版本。维护流程仍要确认候选、命令、实际结果和运行组合，再生成receipt。

对更复杂的维护循环，应用层还需按稳定的维护 run ID 保存修复次数、总时长/调用预算、候选摘要和检查摘要，更新状态时加锁。不能只按宿主 `turn_id` 计数：继续运行可能新建 turn。不要仅凭最后一句“完成了”或者文件存在判断验收成功。多个 hooks 同时匹配时，应分别计数或由单一入口协调，避免它们互相触发。

Codex 的 `Stop` block 会生成继续输入；`continue: false` 可优先终止该事件的继续请求。Claude Code 当前文档还说明有连续继续上限，但工具调用会重置该计数；它不能替代项目自己的修复预算。两者均提供 `stop_hook_active`，适合作为最小防循环信号。[Codex Stop](https://learn.chatgpt.com/docs/hooks#stop)、[Claude Stop](https://code.claude.com/docs/en/hooks#stop)

真正的发布gate应在 `apply` 之前显式运行下列命令，读取验收结果并在非零退出时停止应用步骤：

```powershell
python -m skillloom gate --receipt '<RECEIPT_PATH>' --profile skill-change --expected-run-id '<RUN_ID>' --expected-candidate-digest '<CANDIDATE_DIGEST>' --max-age-hours 24
```

聊天结束hook是辅助提醒层。当前 `apply` 的摘要校验不会自动替调用者执行receipt gate。格式检查通过、宿主静态发现、真实任务成功和可以发布是不同状态。

### 5.4 启用前的最小验收

先在临时项目测试脚本 stdin/stdout，再由用户在宿主内查看实际 hook 来源、事件和命令。Codex 使用 `/hooks` 审核信任；Claude Code 当前 `/hooks` 是配置查看入口，其交互细节可能与旧版本不同。不要以绕过 hooks trust 的参数代替正常验收。

至少覆盖：通过结果不继续；首次失败只继续一次；持续失败能够结束；错误/缺失 receipt 不变成通过；从子目录启动仍能找到脚本；Windows 路径含空格；用户中断不会被自动重启；同一事件有多个匹配 hooks 时没有额外写入。验证输出要区分“脚本单测通过”和“宿主实际触发通过”。

## 6. 现有 Junction 安装的迁移注意

**本机证据，2026-10-06。** `~/.codex/skills` 有 41 个直接子目录，其中 39 个直接包含 `SKILL.md`；这 39 个自维护技能有 24 个目录 Junction 指向 `D:/codex/skills`，均能读取目标文件。`~/.agents/skills` 当时不存在。

已有同日 `skills/list` 记录在两个 cwd 下各返回 52 项：39 个自维护技能、8 个插件技能、5 个 system 技能；39 个自维护技能全部启用，无发现错误或同名重复。原始 `scope=user` 总数为 47，因为其中还包含 8 个插件技能；不能简单把该字段数量当作自维护技能数量。Junction 对应条目返回了 `D:/codex/skills/.../SKILL.md` 实体路径。证据文件和摘要见 [sources.md](sources.md#本机证据)。

**本项目约定。** 保持发现入口不动：

1. inventory 可读取入口并记录 link type 与 target。apply/rollback 只选择实体技能根和实体技能目标，不透过 Junction 修改。
2. 要改 `skills-maintenance` 时，候选、备份和 journal 与 `D:/codex/skills` 分离；计划指向 `D:/codex/skills` 中对应实体。`~/.codex/skills/skills-maintenance` 仍作为发现入口保留。
3. 不把 39 个技能全部复制到 `.agents/skills`。这可能制造双入口、同名歧义、旧副本或版本分叉；当前记录没有做两条根目录的同名碰撞试验。
4. 不移动 Codex home、`.system`、插件缓存、账户文件或其他平台管理状态。维护安装记录不应把它们纳入普通用户技能发布目标。
5. 若确需迁移发现路径，先在独立测试配置核验新路径，记录修改前后 `skills/list`；再逐个迁移并验证真实触发。旧入口何时删除是独立迁移动作，不由内容更新隐式完成。

当前机器已有同用途 `skills-maintenance`。本次集成可让该既有技能调用 Skill Loom；不要再装一个触发范围重叠的 `skill-lifecycle`。开源发行中的 `skill-lifecycle` 是给尚无同类入口的使用者准备的。

## 7. 已知版本边界与未实测项

- 本机 `codex-cli 0.160.1`；`codex features list` 显示 `hooks`、`multi_agent` 为 stable/true，`multi_agent_v2` 为 stable/false。功能开关可用不等于具体 hook、角色或工具拦截已经执行成功。
- Codex 当前文档以 `hooks` 为功能键，`codex_hooks` 为弃用别名；`max_threads` 也仅保留为代理并发设置的旧别名。不要通过抄旧配置判断兼容性。
- Claude Code 当前文档明确一些行为有版本门槛，例如 v2.1.248 起标准 hook 决策的 JSON 解析处理更严格。不要沿用“退出非零一定忽略 JSON”或“退出 1 一定阻断”的泛化说法。
- 本机未找到 Claude Code 可执行文件；没有做 Claude 安装、登录、真实代理任务或原生 hooks 触发。本文的 Claude 示例是官方文档支持的配置草案。
- 本次文档工作没有安装 hooks、修改全局配置、移动 Junction、读取凭据或发布插件。项目后续测试结果应另行记录，不能回填成本文已实测。
- 官方网页已通过 web 工具读取；直接从本地 shell 请求网页被网络沙箱拒绝。Markdown 网页接口在 web 工具中不受支持时，改读官方 HTML 正文，不以搜索摘要代替最终依据。

升级宿主后重新记录版本、发现路径、显式调用、一个代理样例和一组有界 gate 样例，再更新“支持”状态。保留上一次成功记录以便比较，不把官网已描述的能力自动提升为本机已验证能力。

模型升级还必须重跑 [模型任务测试](compatibility-contract.md#5-模型升级后的任务测试)，包括显式/隐式触发、相邻负例、权限边界、工具缺失、失败诚实报告和输出结构。用户目标或授权范围变化时，重建本地验收条件；不能把上一用户“可自动安装”的选择继承给下一用户。项目上线后的自动观察和受控更新流程见 [上线后的更新](compatibility-contract.md#6-上线后的自我更新)。
