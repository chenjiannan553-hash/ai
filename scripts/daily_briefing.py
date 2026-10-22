#!/usr/bin/env python3
"""Collect AI news from public Google News RSS feeds and write a daily Markdown report."""
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import quote
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
import html
import re
import traceback

QUERIES = [
    ("DeepSeek V4.1 Pro 发布追踪", '"DeepSeek" ("V4.1 Pro" OR "V4.1" OR "V4 Pro")'),
    ("OpenAI", "OpenAI AI"),
    ("Google 与 Gemini", "Google Gemini AI"),
    ("Anthropic 与 Claude", "Anthropic Claude AI"),
    ("开源模型", "open source AI models"),
    ("AI Agent", "AI agents"),
    ("AI 芯片与算力", "AI chips semiconductors"),
    ("全球 AI 行业", "artificial intelligence industry"),
]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DailyAINewsBrief/1.0)"}

def fetch(query):
    url = "https://news.google.com/rss/search?q=" + quote(query) + "&hl=zh-CN&gl=US&ceid=US:zh-Hans"
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=25) as response:
        root = ET.fromstring(response.read())
    items = []
    for item in root.findall("./channel/item"):
        title = html.unescape(item.findtext("title", default="").strip())
        link = item.findtext("link", default="").strip()
        pub = item.findtext("pubDate", default="").strip()
        source = item.findtext("source", default="").strip()
        description = item.findtext("description", default="").strip()
        description = re.sub(r"<[^>]+>", " ", html.unescape(description))
        description = re.sub(r"\s+", " ", description).strip()[:900]
        try:
            published = parsedate_to_datetime(pub)
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except Exception:
            published = datetime.now(timezone.utc) - timedelta(days=1)
        if title and link:
            items.append({"title": title, "link": link, "published": published, "source": source, "description": description})
    return items


def build_chatgpt_prompt(items, now):
    """Prepare source-grounded task material for ChatGPT/Codex; no API key or third-party model."""
    selected = sorted(items, key=lambda x: x["published"], reverse=True)[:35]
    facts = []
    for n, item in enumerate(selected, 1):
        stamp = item["published"].astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        facts.append(
            f"{n}. 标题：{item['title']}\n来源：{item['source'] or '未标注'}；时间：{stamp}\n"
            f"摘要线索：{item.get('description', '')[:700]}\n链接：{item['link']}"
        )
    instructions = """请根据以下公开 RSS 新闻材料，撰写约 1200—1600 个汉字的简体中文《全球 AI 新闻简报》。
要求：
1. 只依据给定材料，不得编造事件、数字、引语或未提供的细节；明确区分事实与分析。
2. 开头列出 5 条以内的“今日要点”，然后分为“DeepSeek V4.1 Pro 发布追踪”“全球重要动态”“趋势观察”“核实与局限”。
3. 严格区分 DeepSeek V4.1 Flash、V4 Pro 与 V4.1 Pro。若材料没有可靠的官方确认，必须明确说“本期材料不足以确认官方发布”，不得推断已发布。
4. 尽量覆盖 OpenAI、Google/Gemini、Anthropic/Claude、开源模型、AI 智能体、芯片算力与产业应用，但只写材料确实涉及的内容。
5. 合并重复报道；对重要事实附上来源链接。标题和 RSS 摘要不是官方确认。
6. 如果证据不足，请明确指出，不要用空泛重复的段落填充篇幅。
7. 用自然、准确、信息密度高的中文写作。"""
    return (
        "# 全球 AI 新闻简报：生成任务与新闻材料\n\n"
        + f"> 新闻采集时间（UTC）：{now.strftime('%Y-%m-%d %H:%M')}\n\n"
        + "以下内容包含完整写作任务和 RSS 新闻线索。请直接生成最终简报，不要要求用户再次复制、确认或提供额外信息。\n\n"
        + "## 写作任务\n\n" + instructions
        + "\n\n## 新闻材料（RSS 线索，需核实）\n\n" + "\n\n".join(facts) + "\n"
    )

def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=30)
    sections = []
    all_items = {}
    deepseek_items = []
    for section, query in QUERIES:
        try:
            results = [x for x in fetch(query) if x["published"] >= cutoff]
        except Exception as exc:
            sections.append((section, [], str(exc)))
            continue
        for item in results:
            all_items[item["link"]] = item
            if section.startswith("DeepSeek"):
                deepseek_items.append(item)
        sections.append((section, results, None))

    # Build a unique recent source set and prepare a ChatGPT-web prompt pack.
    unique_items = list({x["link"]: x for x in all_items.values()}.values())
    prompt_text = build_chatgpt_prompt(unique_items, now) if unique_items else None
    report_date = now.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    prompt_path = Path("reports") / (report_date + "-chatgpt-prompt.md")
    if prompt_text:
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8")

    # Keep a manageable report; prioritize recent stories and deduplicate links.
    report = [
        "# 全球 AI 新闻简报",
        "",
        f"> 生成时间（UTC）：{now.strftime('%Y-%m-%d %H:%M')}  |  覆盖窗口：近 30 小时",
        "> 中文分析：未自动调用 ChatGPT；本仓库不使用 API 密钥，也不模拟网页登录.",
        "",
    ]
    report += ["## 中文简报生成方式", "", "GitHub Actions 不能直接使用 ChatGPT 网页会话。为满足不使用 API 密钥、完全免费的要求，本次只自动采集新闻，并生成可复制到 ChatGPT 网页版的提示词文件；需要人工粘贴提示词并提交，才会得到 ChatGPT 云端总结。", "", f"[打开本日 ChatGPT 提示词文件]({prompt_path.name})" if prompt_text else "本次没有收集到可用于生成提示词的新闻材料。", "", "---", ""]
    report += [
        "## DeepSeek V4.1 Pro 发布追踪",
    ]
    if deepseek_items:
        report.append("RSS 检索到以下相关报道线索；标题本身不能作为官方发布确认，请打开来源核实：")
        for item in sorted({x["link"]: x for x in deepseek_items}.values(), key=lambda x: x["published"], reverse=True)[:10]:
            report.append(f"- [{item['title']}]({item['link']})（{item['source'] or '来源未标注'}；{item['published'].astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}）")
    else:
        report.append("在当前 RSS 检索结果中，近 30 小时未找到明确匹配的报道。此结果不代表产品一定未发布；请以 DeepSeek 官方公告为准。")
    report += ["", "## 全球 AI 动态"]
    total = 0
    for section, results, error in sections[1:]:
        report += ["", f"### {section}"]
        if error:
            report.append(f"- 本类别 RSS 获取失败：{error}")
            continue
        if not results:
            report.append("- 近 30 小时未检索到匹配的 RSS 条目。")
            continue
        for item in sorted({x["link"]: x for x in results}.values(), key=lambda x: x["published"], reverse=True)[:8]:
            if total >= 60:
                break
            stamp = item["published"].astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            report.append(f"- [{item['title']}]({item['link']})（{item['source'] or '来源未标注'}；{stamp}）")
            total += 1
    report += [
        "",
        "## 阅读说明",
        "- 新闻材料来自公开 Google News RSS；本工作流不会自动生成或冒充 ChatGPT 云端分析。",
        "- 如需 ChatGPT 云端总结，请打开同目录的 chatgpt-prompt 文件，将全文复制到 ChatGPT 网页版发送。",
        "- 新闻标题、媒体转述或搜索结果均不等于官方确认。涉及模型发布、性能、融资或政策的消息，请打开原文并优先核对官方公告。",
        "- 部分 RSS 条目可能重复、相关性不足或无法访问；自动收集不保证完整性。",
        "",
    ]
    outdir = Path("reports")
    outdir.mkdir(parents=True, exist_ok=True)
    # Name reports by Beijing calendar date, regardless of the Mac's local timezone.
    path = outdir / f"{now.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d')}.md"
    path.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {path} with {len(all_items)} unique links; ChatGPT prompt prepared: {bool(prompt_text)}; no API or local model used.")

if __name__ == "__main__":
    main()
