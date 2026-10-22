# 每日全球 AI 新闻简报

目标：每天北京时间 17:20 收集全球 AI 新闻，由 OpenAI Codex CLI（使用已登录的 ChatGPT 账号额度）生成约 1,400 字的简体中文简报，并自动提交到本 GitHub 仓库。

## 运行方式和边界

- **主自动化运行在你自己的 Mac 上**，使用 macOS LaunchAgent 定时执行；生成完成后通过本机已授权的 Git 凭据推送到 `main`。
- AI 文本由官方 Codex CLI 调用 OpenAI 托管模型生成，不调用 Qwen、Gemini、DeepSeek 等第三方模型，也不使用 OpenAI API Key。
- ChatGPT Free 计划中的 Codex 使用额度有限。达到限额、登录过期、网络故障或 RSS 没有足够材料时，本次任务可能失败；不会用 RSS 标题拼接冒充 AI 总结。
- Mac 需要开机、联网、登录到 macOS 用户会话。若错过 17:20，但当天稍后恢复运行，调度器会尝试补跑。
- 首次启用前必须由你本人完成 Codex 的 ChatGPT 登录，以及对 GitHub 仓库的写入授权。这是一次性授权，不是 OpenAI API Key。
- 若 Codex 登录要求手机号验证，官方要求使用可验证的受支持手机号码；不能用脚本绕过。没有完成登录前，自动生成部分不能运行。
- 仓库是公开的，因此**不要把 `~/.codex/auth.json`、浏览器 Cookie 或其他登录凭据提交到仓库或 GitHub Actions Secrets**。

## Mac 首次设置

1. 在 Mac 上安装并登录官方 Codex CLI：官方说明见 https://learn.chatgpt.com/docs/codex/cli 。登录后可在终端运行 `codex exec --ephemeral --sandbox read-only "只输出 AUTH_OK"` 测试模型访问。
2. 在仓库本地目录确认 `git push origin main` 已有写入授权。可以使用你本机已有的 GitHub 登录凭据；不需要 OpenAI API Key。
3. 在仓库根目录运行：

   ```bash
   bash mac-automation/install.sh
   ```

4. 检查日志：

   ```bash
   tail -f "$HOME/Library/Logs/ai-daily-briefing.log"
   ```

调度器目标为 **北京时间每天 17:20**，会按北京时间判断日期；如果失败，当天最多自动重试三次，以避免反复消耗额度。

## GitHub Actions 的作用

GitHub Actions 目前只保留手动触发的 RSS 素材采集，不会声称自己调用了 ChatGPT。因为本仓库是公开仓库，不应把个人 Codex/ChatGPT 登录凭据嵌入托管 CI。使用免费 ChatGPT 额度的受支持路径是在你自己的 Mac 上，通过已登录的 Codex CLI 运行非交互式任务。

手动采集：进入仓库 **Actions → 每日 AI 新闻简报（RSS 素材准备）→ Run workflow**。该手动工作流只生成来源线索和提示词，不会单独生成最终 AI 总结。

## 新闻范围与核实

- 跟踪 DeepSeek V4.1 Pro 的官方发布情况，并覆盖 OpenAI、Google/Gemini、Anthropic/Claude、开源模型、AI Agent、AI 芯片与全球产业动态。
- 必须区分 DeepSeek V4.1 Flash、V4 Pro 与 V4.1 Pro；RSS 标题和媒体报道本身不代表官方确认。
- 输出保存为 `reports/YYYY-MM-DD.md`；原始 RSS 线索和生成输入保存为 `reports/YYYY-MM-DD-chatgpt-prompt.md`。
- 新闻素材由公开 Google News RSS 提供。摘要必须标注来源链接和证据局限；RSS 获取失败或模型用量耗尽时，不得伪造成功报告。
