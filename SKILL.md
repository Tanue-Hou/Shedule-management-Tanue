---
name: obsidian-schedule-manager
description: A tool that allows Hermes to flawlessly manage long-term 34-week plans directly within an Obsidian Markdown file. Uses native Block IDs to achieve pinpoint row updates and dynamic rollover without causing LLM hallucination or context loss.
---

# Obsidian 专属日程管理规范 (Obsidian Schedule Manager)

为了彻底解决大语言模型处理长周期（如34周）计划时产生的上下文遗忘与幻觉，并且与您的 Obsidian 知识库无缝对接，本 Skill 规定你**必须**使用专用的 Obsidian 解析脚本来处理所有日程任务。

## 工具位置与配置
`/Users/tanue/.gemini/config/skills/dynamic-schedule-manager/scripts/obsidian_schedule.py`

*(注意：脚本内当前使用 `~/.schedule.md` 作为占位符，用户可随时要求你修改该文件里的 `OBSIDIAN_FILE` 常量以指向他们真正的库路径)*

## 核心工作流（Zero Trust Memory）
1. **绝对忠于 Markdown**：用户在 Obsidian 里直接打勾或修改也是合法的，因此你每次回答之前，必须使用 `list` 查询最新的 Markdown 内容。
2. **利用 Block IDs 定位**：脚本在每次添加任务时都会自动生成类似于 `^a1b2c3` 的隐藏锚点。你后续的任何修改都必须依赖这个 `ID`。这保证了哪怕用户在文件中插入了几千字笔记，你的修改依然能精确到行。

## 场景命令指南

### 1. 添加任务 / 批量注入计划
当用户要求新增任务，或抛给你一份大纲计划表时。
如果是单条任务：
```bash
python /Users/tanue/.gemini/config/skills/dynamic-schedule-manager/scripts/obsidian_schedule.py add --title "文献第二章审稿" --week 2
```
如果是批量大纲，你需要在你的 Bash 环境中利用 `for` 循环或多次运行 `add` 命令将其录入，这会在 Obsidian 文件中自动按 `## Week X` 创建完美的 Checklist 格式。

### 2. 检索并获取状态
当用户询问进度时。
```bash
python /Users/tanue/.gemini/config/skills/dynamic-schedule-manager/scripts/obsidian_schedule.py list --week 3
```
返回的结果将包含每个任务的 **Block ID**，请在接下来的更新操作中使用它。

### 3. 精准更新任务（打勾、改字、推迟）
当用户表示某项工作已做完，或要推迟某一项时。必须先拿到其 Block ID！
```bash
# 标记为完成（这将在 Obsidian 文件里把 [ ] 变成 [x]）
python /Users/tanue/.gemini/config/skills/dynamic-schedule-manager/scripts/obsidian_schedule.py update --id ^a1b2c3 --status Done

# 将任务精准推迟到第 5 周（这会将整行内容剪切并移动到 ## Week 5 标题下）
python /Users/tanue/.gemini/config/skills/dynamic-schedule-manager/scripts/obsidian_schedule.py update --id ^a1b2c3 --week 5
```

### 4. 动态规划与顺延 (Rollover) [核心亮点]
当来到新的一周时，如果有过去没做完的事情。
```bash
# 假设现在是第 3 周
python /Users/tanue/.gemini/config/skills/dynamic-schedule-manager/scripts/obsidian_schedule.py rollover --current-week 3
```
脚本会自动扫描所有小于第3周的标题，把未打勾的 `- [ ]` 任务统一切割到 `## Week 3` 下，并附加 `#顺延` 标签供用户在 Obsidian 里追踪。你必须向用户汇报哪些任务被顺延了。

## 对话规范
处理完后，请以简洁的表格或列表形式回复用户，避免冗长废话。由于用户可以在 Obsidian 中实时看到变化，你可以直接告诉用户：“已在 Obsidian 中为您更新了以下日程：...”
