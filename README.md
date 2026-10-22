# 每日全球 AI 新闻简报

本仓库使用 GitHub Actions 每天北京时间 17:20（UTC 09:20）抓取公开 Google News RSS，整理 DeepSeek V4.1 Pro 发布追踪、OpenAI、Google/Gemini、Anthropic/Claude、开源模型、AI Agent、AI 芯片与全球 AI 行业新闻。

## 当前实现与免费限制

- 不需要 API 密钥、GitHub Secrets 或付费模型 API。
- 自动任务抓取新闻并生成 Markdown 报告及可复制到 ChatGPT 网页版的提示词文件。
- **重要：GitHub Actions 不能直接调用当前 ChatGPT 网页会话。** 因此在不使用 API 或其他模型的前提下，本仓库不能全自动让 ChatGPT 网页模型撰写并写回 1400 字分析稿；生成提示词后，需要人工复制到 ChatGPT 网页版并发送。
- 自动采集内容不是 AI 深度分析；RSS 结果可能遗漏、重复或误分类新闻。DeepSeek 相关搜索结果不等于官方发布确认。

## 自动运行与手动运行

- 定时：每天北京时间 17:20（UTC 09:20）。GitHub Actions 可能因平台负载延迟，不能保证精确到分钟。
- 手动：进入仓库 **Actions** → **每日 AI 新闻简报** → **Run workflow**。
- 报告保存于 `reports/YYYY-MM-DD.md`；若有新闻材料，还会生成 `reports/YYYY-MM-DD-chatgpt-prompt.md`。
- 如果任务失败，请打开 Actions 中最新一次运行查看日志。

## DeepSeek 发布核实

新闻标题和 RSS 搜索结果不是官方发布确认。请优先核对 [DeepSeek 官方新闻页](https://www.deepseek.com/en/news/) 和 [官方 API 更新日志](https://api-docs.deepseek.com/zh-cn/updates/)，并区分不同模型名称及版本。

## 权限说明

工作流使用 `contents: write` 权限提交生成的报告。如果提交失败，请在仓库 **Settings → Actions → General → Workflow permissions** 检查是否允许工作流写入仓库内容。
