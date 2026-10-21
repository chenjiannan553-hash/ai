#!/usr/bin/env python3
"""Collect AI news from public Google News RSS feeds and write a daily Markdown report."""
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import html
import re

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
        try:
            published = parsedate_to_datetime(pub)
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except Exception:
            published = datetime.now(timezone.utc) - timedelta(days=1)
        if title and link:
            items.append({"title": title, "link": link, "published": published, "source": source})
    return items

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

    # Keep a manageable report; prioritize recent stories and deduplicate links.
    report = [
        "# 全球 AI 新闻简报",
        "",
        f"> 生成时间（UTC）：{now.strftime('%Y-%m-%d %H:%M')}  |  覆盖窗口：近 30 小时",
        "",
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
        "- 本简报由公开 Google News RSS 检索结果自动整理，未调用生成式 AI；因此是新闻线索汇总，不是约 1400 字的 AI 深度分析。",
        "- 新闻标题、媒体转述或搜索结果均不等于官方确认。涉及模型发布、性能、融资或政策的消息，请打开原文并优先核对官方公告。",
        "- 部分 RSS 条目可能重复、相关性不足或无法访问；自动收集不保证完整性。",
        "",
    ]
    outdir = Path("reports")
    outdir.mkdir(parents=True, exist_ok=True)
    # Use UTC date in filename to keep the workflow deterministic.
    path = outdir / f"{now.strftime('%Y-%m-%d')}.md"
    path.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {path} with {len(all_items)} unique links")

if __name__ == "__main__":
    main()
