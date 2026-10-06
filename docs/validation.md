# 验证记录

记录日期：2026-10-06。本文件将实际完成的软件检查与未测能力分开；它不是所有 skills、模型或宿主都有效的证明。

## 本地软件验证

| 检查 | 已观察结果 | 范围 |
|---|---|---|
| Python 单元测试 | 43项：41通过，2跳过 | Windows / Python 3.12.8；POSIX执行位不适用，创建符号链接需要额外权限 |
| 全新虚拟环境安装 | editable install、`pip check`、CLI版本、demo、43项测试通过相应检查 | Python 3.12.8 / PyYAML 6.0.3；测试仍有上述2项跳过 |
| 故障注入 | 8个变更场景、4个证据场景 | 每场景使用新临时目录；共32次场景×方法执行 |
| 文件合同参考实现 | unchecked-copy 1/8；static-only 3/8；guarded 8/8 | 弱参考基线，不是现有产品对比 |
| 证据合同参考实现 | declared-pass 1/4；bound-receipt 4/4 | 检查声明、绑定、文件哈希和时间，不验证语义真实性 |
| 公开来源变化查询 | 7/7登记来源成功读取完整commit，当时均无变化 | 一次实际网络观察，不代表全球覆盖或永不过时 |
| 公开仓库检索 | 一条公开查询返回5个未评审仓库 | 不将结果自动视为可安装skill |
| 固定来源暂存 | 实际下载drawio-diagram，共14文件，Git blob身份和长度核验通过 | 指定完整commit，含许可/溯源；未执行或安装下载内容 |

原始逐例结果：[invariants.json](../research/results/invariants.json)。这是开发期间选取的确定性故障场景，不是保留集，不估计置信区间，也不推断LLM任务准确率或token节省。

复现命令（在项目根、已安装依赖的Python环境）：

```bash
python -m unittest discover -s tests -v
python scripts/check_release.py
python scripts/benchmark_invariants.py
python -m skillloom demo --workdir ../loom-demo-validation-001
```

benchmark 会重写公开的 `research/results/invariants.json`；demo 目录必须尚不存在。仅制作图片时另外安装 `matplotlib` 并运行 `scripts/render_assets.py`，它不是CLI运行依赖。

## 一次真实本机维护闭环

本机：Windows，Python 3.12.8，Codex CLI 0.160.1。用户维护目录静态盘点为39项。现有 `skills-maintenance` 的两个文件加入按需自迭代参考，没有再安装同用途的新入口。

| 阶段 | 观察结果 |
|---|---|
| 固定候选与计划 | 两个文件变化，候选/运行根/journal分别存放 |
| 应用 | 完成；后续盘点39项、0错误、0警告 |
| 回退 | 文件快照与变更前完全一致 |
| 重新应用 | 完成 |
| 再次计划/应用 | `no_change` |
| 全局配置与指令 | 受保护文件哈希前后相同 |
| 明确归属的技能字节码缓存 | 0文件、0字节；没有执行全局删除 |

私有计划、备份、真实路径、宿主发现结果和原始日志不随公开仓库发布。匿名摘要支持本次案例叙述，不能替代独立用户的复现。本轮公开目录提供33项通用与6项项目范围技能说明；样例description是编辑后的目录简介，不能拿其字符数与真实运行metadata比较而声称压缩收益。

[匿名本机证据](../research/results/local-cycle.anonymized.json)包含计划前后文件SHA-256、最终观察快照和回退状态摘要。前态摘要为 `1c757a506db156844cec2b1f69e6179a28bcc85fcc94514b15c777ccd4df27b6`，计划后态与最终观察摘要均为 `00859549587dc4996ee838e3406ef7d0a0201ec019655ece9bab690d13ac0d6d`。计算规则写在JSON中；这些摘要支持记录一致性核对，不能代替原始私有事务的外部复现。

最终使用原生Codex app-server的 `skills/list`、`forceReload:true` 在两个工作目录只读核验：每处发现52项（39项用户维护、8项插件、5项系统），错误0、重复名称0。`scope=user`还包含插件技能，不能直接当39项用户目录的计数。没有启动新的模型任务；发现成功也不表示每个技能都完成了真实行为测试。

## 独立评审形成的修复

第一轮修复执行权限丢失、无变化计划漏查漂移、清理中断缺少删除意图记录、宽松输入类型。第二轮补上固定Git blob身份/长度验证，以及拒绝NaN/Infinity时效参数。随后补上Windows大小写不敏感的溯源文件保留名检查。对应故障加入单元测试；评审本身不等于形式化证明。

## CI 与集成边界

GitHub Actions配置：Windows/Linux × Python 3.10/3.12。远端结果以[实际运行记录](https://github.com/Koooki3/skill-loom/actions)为准；首次推送前仅是待执行配置。发布说明会记录对应commit和成功run。

当前未验证：原生Codex/Claude Code Stop-hook运行、Claude Code本地发现、多用户托管、macOS运行、任意模型任务提升、长期并发与存储故障恢复。适配指南区分官方能力、项目约定和本机观察。CLI的hook脚本、单元fixture通过不等于宿主实际调用已通过。

论文是系统技术报告，非同行评审论文。19条引用采用连续数字编号，15篇论文的固定版本、阅读章节和反证见[研究来源](../research/references.json)与[工程来源](../research/engineering-evidence.md)。
