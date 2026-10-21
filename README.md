# 每日全球 AI 新闻简报

此仓库通过 GitHub Actions 每天北京时间 17:20 自动收集 DeepSeek V4.1 Pro 发布追踪及全球 AI 新闻，并将 Markdown 简报提交到 `reports/`。

## 自动运行
- 定时：每天北京时间 17:20（UTC 09:20）
- 不需要 API 密钥；使用公开 Google News RSS 源。
- 这是 RSS 新闻收集与摘要整理版，不调用大语言模型，因此不能保证生成真正的 AI 深度分析，也不能保证 DeepSeek V4.1 Pro 已发布。

## 手动运行
进入 GitHub 仓库的 **Actions**，选择 **每日 AI 新闻简报**，点击 **Run workflow**。

## 权限
仓库 Settings → Actions → General → Workflow permissions，选择 **Read and write permissions**，保存。否则工作流可能无法提交报告。

## 报告
生成文件位于 `reports/YYYY-MM-DD.md`。请核实原始来源，RSS 标题不等于已验证的事实。
