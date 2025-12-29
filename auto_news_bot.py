import os
import requests
import feedparser
from datetime import datetime
from openai import OpenAI

# --- 配置区域 ---

RSS_SOURCES = [
    {
        "name": "TechCrunch (科技)",
        "url": "https://techcrunch.com/feed/"
    },
    {
        "name": "New York Times (世界)",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
    },
    {
        "name": "Hacker News (极客)",
        "url": "https://news.ycombinator.com/rss"
    },
]

LIMIT_PER_SOURCE = 5
QWEN_MODEL = "qwen3-max"

# --- 核心代码 ---

def get_env_variable(var_name):
    value = os.getenv(var_name)
    if not value:
        print(f"⚠️ 警告: 环境变量 {var_name} 未设置。")
        return None
    return value

def fetch_rss_data(sources):
    print("📡 开始抓取 RSS 新闻源...")
    all_articles = []
    
    for source in sources:
        try:
            print(f"   正在读取: {source['name']}...")
            feed = feedparser.parse(source['url'])
            
            if not feed.entries:
                print(f"   ❌ 读取失败或无内容: {source['url']}")
                continue
                
            entries = feed.entries[:LIMIT_PER_SOURCE]
            
            for entry in entries:
                title = entry.get('title', 'No Title')
                link = entry.get('link', '')
                summary = entry.get('summary', '')[:300] 
                
                article_text = f"来源: {source['name']}\n标题: {title}\n链接: {link}\n摘要: {summary}\n"
                all_articles.append(article_text)
                
        except Exception as e:
            print(f"   ❌ 发生异常: {e}")
            
    print(f"✅ 共获取到 {len(all_articles)} 条新闻。")
    return all_articles

def summarize_with_qwen(articles_list):
    api_key = get_env_variable("DASHSCOPE_API_KEY")
    if not api_key:
        return "❌ 错误：未配置 DASHSCOPE_API_KEY"

    if not articles_list:
        return "📭 今日暂无新闻更新。"

    print(f"🤖 正在调用 Qwen ({QWEN_MODEL}) 进行总结...")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    articles_text = "\n---\n".join(articles_list)
    
    system_prompt = "你是一个专业的国际新闻主编。你的目标是为中国读者提供一份简明扼要、高价值的全球新闻简报。"
    user_prompt = f"""
    请阅读以下抓取到的原始新闻数据：
    
    {articles_text}
    
    请执行以下任务：
    1. **筛选与去重**：剔除广告、重复内容及琐碎信息。
    2. **中文总结**：用流畅的中文总结每条重要新闻。
    3. **格式化输出**：
       - 使用 HTML 标签进行简单的排版（因为 PushPlus 对 Markdown 支持有时不如 HTML 稳定，特别是换行）。
       - 标题加粗，使用 `<br>` 换行。
       - 每条新闻格式：`emoji <b>标题</b>` + `<br>` + `简短总结` + `<br>` + `<a href="link">阅读原文</a>`。
    4. **每日点评**：在末尾增加一个“小编毒舌”环节。
    
    直接输出内容，不要包含开场白。
    """
    
    try:
        completion = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Qwen 调用失败: {e}")
        return f"AI 接口调用出错: {e}"

def push_pushplus(content):
    """推送到 PushPlus"""
    token = get_env_variable("PUSHPLUS_TOKEN")
    
    if not token:
        print("⚠️ PushPlus Token 缺失，跳过推送。")
        return

    print("🚀 正在推送到 PushPlus...")
    
    url = "http://www.pushplus.plus/send"
    
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    title = f"🌍 全球新闻日报 ({today})"
    
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "html"  # 使用 HTML 模板以获得更好的排版
    }
    
    try:
        resp = requests.post(url, json=data)
        result = resp.json()
        if result.get('code') == 200:
            print(f"✅ 推送成功: {result}")
        else:
            print(f"❌ 推送失败: {result}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    # 1. 抓取
    articles = fetch_rss_data(RSS_SOURCES)
    
    # 2. 总结
    if articles:
        summary = summarize_with_qwen(articles)
        
        # 本地打印预览
        print("\n" + "="*20 + " 内容预览 " + "="*20)
        print(summary)
        print("="*50 + "\n")
        
        # 3. 推送
        push_pushplus(summary)
    else:
        print("📭 未获取到任何新闻，即将跳过后续步骤。")

if __name__ == "__main__":
    main()
