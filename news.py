import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

CATEGORIES = (
    {
        "title": "🌲 森・林業ニュース",
        "query": "林業 OR 森林 OR 国産材 OR 木材",
    },
    {
        "title": "🪑 家具ニュース",
        "query": "家具 OR インテリア家具 OR オフィス家具",
    },
    {
        "title": "🏗️ 建築ニュース",
        "query": "建築 OR 建築業界 OR 建築設計",
    },
    {
        "title": "🏠 住宅内装ニュース",
        "query": "(住宅 内装) OR (住宅用壁紙) OR (壁紙 新商品) OR (壁紙 新発売) OR (内装材 新商品) OR (住宅用パネル)",
    },
)


def fetch_news(query, limit=1):
    encoded_query = urllib.parse.quote(query)

    url = (
        "https://news.google.com/rss/search?"
        f"q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Kiila-News-Bot/1.0"},
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = root.findall("./channel/item")[:limit]

    news = []

    for item in items:
        title = item.findtext("title", default="タイトルなし")
        link = item.findtext("link", default="")

        news.append(
            {
                "title": title,
                "link": link,
            }
        )

    return news


def build_message(category_title, news):
    lines = [
        category_title,
        "",
    ]

    if not news:
        lines.append("今日はニュースを取得できませんでした。")
        return "\n".join(lines)

    for index, article in enumerate(news, start=1):
        lines.append(f"{index}. *{article['title']}*")
        lines.append(article["link"])
        lines.append("")

    return "\n".join(lines).strip()


def send_to_slack(message):
    payload = json.dumps({"text": message}).encode("utf-8")

    request = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"Slack returned HTTP {response.status}")


if __name__ == "__main__":
    for category in CATEGORIES:
        news = fetch_news(category["query"])
        message = build_message(category["title"], news)
        send_to_slack(message)

    print(f"Sent {len(CATEGORIES)} category news threads to Slack")
