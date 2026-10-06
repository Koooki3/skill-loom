# Skill Loom launch kit

## Repository metadata

Name: **Skill Loom**

Short description: **Evidence-driven, reversible maintenance for agent skill libraries. Local CLI, Codex/Claude guides, reproducible checks.**

Suggested topics: `agent-skills`, `skill-management`, `codex`, `claude-code`, `evaluation`, `reproducibility`, `python`.

Repository: https://github.com/Koooki3/skill-loom

## Assets

- `social-card.png`: 1774×887, 2:1. Repository banner / social sharing artwork. AI-generated, with prompt and provenance noted in this folder. It contains no performance chart.
- `icon.svg`: editable original vector icon. Suitable for square avatars and documentation.
- `../figures/invariant-study.svg`, `.png`, `.pdf`: chart generated from shipped experiment results. Always retain the separate 8-case and 4-case denominators and caption.

The social card can be uploaded as a repository social preview by a repository owner through GitHub settings. Including it in README does not itself change that setting.

## 中文介绍稿

Skill Loom 开源了：一个帮助你维护 Agent Skills 的本地工作台。

它从用户需求和真实任务缺口出发，支持公开来源检索、固定版本暂存、能力重叠检查、变更计划、证据门控和回退。附带 Codex/Claude Code 适配说明、39项匿名化技能目录、论文和中文技术分享。

首版重点验证维护过程：包含12个确定性故障场景和一次真实本机回退演练。它不承诺自动覆盖全球skills，也没有把软件检查说成模型能力提升。欢迎运行demo，提交可复现的任务缺口和宿主验证结果。

## English introduction

Skill Loom is a local workbench for maintaining agent skill libraries with explicit evidence and reversible changes. Start from user needs, investigate capability gaps, review pinned sources, and keep a recovery path for each deployment.

The first release includes a Python CLI, Codex and Claude Code adapter guides, an anonymized 39-skill catalog, a technical report and reproducible fault-injection checks. It is an engineering and research prototype; the reported checks do not establish improved model-task performance.

## Release copy

Version 0.1.0 introduces inspectable profiles and capability catalogs; bounded source discovery and Git blob-verified staging; exact change plans with drift checks and rollback; task-bound evidence receipts; owned-cache cleanup; and a portable lifecycle skill. See `docs/validation.md` for actual test scope and platform limits.

These texts are publication drafts for the owner. The project does not automatically send posts, contact maintainers or submit links to external communities.
