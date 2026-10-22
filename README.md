# 每日全球 AI 新闻简报

此仓库计划每天北京时间 17:20（UTC 09:20）自动收集全球 AI 新闻，并尝试生成约 1400 字的简体中文分析稿，重点追踪 DeepSeek V4.1 Pro。

## 免费本地 AI 生成
- 新闻来源：公开 Google News RSS。
- 生成模型：Qwen2.5-0.5B-Instruct 的 GGUF 量化版，在 GitHub Actions runner 上本地运行。
- **不需要 API 密钥、不需要配置 GitHub Secrets，也不调用付费 API。**
- 首次运行需要下载约数百 MB 的模型文件；Actions 缓存会尝试复用模型，减少后续下载。
- 这是较小的本地模型，生成质量、运行时间和可用性可能受 GitHub runner 资源与外部下载状态影响。
- 如果模型安装、下载或推理失败，工作流仍会保存 RSS 新闻线索，并明确标记本次没有成功生成 AI 总结；不会把规则拼接内容冒充 AI 生成。

## 自动运行与手动运行
- 定时：每天北京时间 17:20（UTC 09:20）。
- 手动：进入仓库 **Actions** → **每日 AI 新闻简报** → **Run workflow**。
- 如果自动运行失败，请打开 Actions 中最新一次运行查看日志。

## DeepSeek 发布核实
新闻标题和 RSS 搜索结果不是官方发布确认。报告应优先核对 [DeepSeek 官方新闻页](https://www.deepseek.com/en/news/) 和 [官方 API 更新日志](https://api-docs.deepseek.com/zh-cn/updates/)，并区分 V4.1 Flash、Flash-1017、V4 Pro 与 V4.1 Pro。

## 报告
报告保存于 `reports/YYYY-MM-DD.md`。请打开原始来源核实关键消息；本地小模型的摘要也可能出错。
