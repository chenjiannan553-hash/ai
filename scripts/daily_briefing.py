#!/usr/bin/env python3
"""Collect AI news from public Google News RSS feeds and write a daily Markdown report."""
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
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


def generate_ai_summary(items):
    """Generate a Chinese briefing with a small local open-weight model; no API key."""
    try:
        from huggingface_hub import hf_hub_download
        from llama_cpp import Llama
        model_path = hf_hub_download(
            repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
            filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
        )
        # Keep prompt compact enough for the small model and runner memory.
        selected = sorted(items, key=lambda x: x["published"], reverse=True)[:24]
        facts = []
        for n, item in enumerate(selected, 1):
            stamp = item["published"].astimezone(timezone.utc).strftime("%m-%d %H:%M UTC")
            desc = item.get("description", "")[:380]
            facts.append(
                f"{n}. 标题：{item['title']}\n来源：{item['source'] or '未标注'}；时间：{stamp}\n"
                f"摘要线索：{desc}\n链接：{item['link']}"
            )
        prompt = """请根据下面提供的新闻标题、来源、摘要线索和链接，写一篇约1400个汉字的简体中文《全球AI新闻简报》。
必须遵守：
1. 只能把给定材料作为事实依据；标题或搜索结果不是官方确认，不要编造细节、数字、引语或未提供的事件。
2. 开头先写“今日要点”，然后分为“DeepSeek V4.1 Pro发布追踪”“全球重要动态”“趋势观察”“核实与局限”几个部分。
3. DeepSeek 部分必须区分 V4.1 Flash/Flash-1017、V4 Pro 与 V4.1 Pro；若材料没有官方确认 V4.1 Pro 已发布，就明确写“本期材料不足以确认官方发布”，不得把 Flash 的更新说成 Pro 发布。
4. 解释新闻可能意味着什么时，明确标注为“分析”，不要伪装成已证实事实。
5. 尽量覆盖 OpenAI、Google/Gemini、Anthropic/Claude、开源模型、AI智能体、芯片算力和产业应用；只写材料实际涉及的主题。
6. 中文自然、信息密度高，不要逐条机械翻译标题。结尾说明 RSS 材料的限制。
7. 总长度约1200—1600个汉字（不含链接列表）。"""
        llm = Llama(model_path=model_path, n_ctx=4096, n_threads=2, verbose=False)
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "你是严谨的科技新闻编辑。优先准确、可追溯和区分事实与推断；材料不足时明确承认不确定。"},
                {"role": "user", "content": prompt + "\n\n新闻材料：\n" + "\n\n".join(facts)},
            ],
            temperature=0.25,
            top_p=0.85,
            max_tokens=1800,
        )
        text = response["choices"][0]["message"]["content"].strip()
        if len(text) < 500:
            raise RuntimeError(f"模型输出过短：{len(text)} 字符")
        return text, "Qwen2.5-0.5B-Instruct 本地模型"
    except Exception as exc:
        print(f"Local AI summary unavailable; using transparent RSS-only fallback: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return None, "未生成 AI 总结（模型下载、安装或推理失败）"

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

    # Build a unique, recent news set for local-model summarization.
    unique_items = list({x["link"]: x for x in all_items.values()}.values())
    ai_summary, summary_engine = generate_ai_summary(unique_items) if unique_items else (None, "没有可用新闻材料")

    # Keep a manageable report; prioritize recent stories and deduplicate links.
    report = [
        "# 全球 AI 新闻简报",
        "",
        f"> 生成时间（UTC）：{now.strftime('%Y-%m-%d %H:%M')}  |  覆盖窗口：近 30 小时",
        f"> 中文简报引擎：{summary_engine}",
        "",
    ]
    if ai_summary:
        report += ["## AI 生成的中文深度简报", "", ai_summary, "", "---", ""]
    else:
        report += ["## 中文简报生成状态", "", "本次没有成功调用本地模型，因此不会把规则拼接内容冒充为 AI 生成。下方保留新闻线索，供阅读和核实。", "", "---", ""]
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
        "- 新闻材料来自公开 Google News RSS；若本地 Qwen 模型成功运行，中文分析由 GitHub Actions 上的本地开源模型生成，不使用 API 密钥。",
        "- 本地模型规模较小，分析质量可能有限；模型生成内容仍需通过原始链接核实。",
        "- 新闻标题、媒体转述或搜索结果均不等于官方确认。涉及模型发布、性能、融资或政策的消息，请打开原文并优先核对官方公告。",
        "- 部分 RSS 条目可能重复、相关性不足或无法访问；自动收集不保证完整性。",
        "",
    ]
    outdir = Path("reports")
    outdir.mkdir(parents=True, exist_ok=True)
    # Use UTC date in filename to keep the workflow deterministic.
    path = outdir / f"{now.strftime('%Y-%m-%d')}.md"
    path.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {path} with {len(all_items)} unique links; AI summary: {bool(ai_summary)} ({summary_engine})")

if __name__ == "__main__":
    main()
