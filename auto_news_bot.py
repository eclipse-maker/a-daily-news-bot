import os
import requests
import feedparser
from datetime import datetime
from openai import OpenAI

# --- 配置区域 ---

# 💡 提示: RSSHub (https://rsshub.app) 是一个神器，能把微博、知乎等变成 RSS。
# GitHub Actions 在海外，访问 RSSHub 官方实例非常稳定。

RSS_SOURCES = [
    # --- 🕵️‍♂️ 科技 & 极客 (硬核小道消息) ---
    {
        "name": "Hacker News (高分热贴)",
        "url": "https://hnrss.org/newest?points=100" # 只看超过100分的热贴
    },
    {
        "name": "Reddit LocalLLaMA (AI模型泄露/讨论)",
        "url": "https://www.reddit.com/r/LocalLLaMA/hot/.rss"
    },

    # --- 🍉 大陆八卦 & 民生 (微博/知乎/热搜) ---
    {
        "name": "微博热搜 (实时)",
        "url": "https://rsshub.app/weibo/search/hot"
    },
    {
        "name": "知乎热榜",
        "url": "https://rsshub.app/zhihu/hotlist"
    },
    {
        "name": "36Kr (科技商业八卦)",
        "url": "https://36kr.com/feed"
    },
    
    # --- 💰 金融 & 宏观 (搞钱必看) ---
    {
        "name": "华尔街见闻 (全球资讯)",
        "url": "https://rsshub.app/wallstreetcn/news/global"
    },
    
    # --- 🌏 国际政治 & 局势 ---
    {
        "name": "联合早报 (中国/国际)",
        "url": "https://rsshub.app/zaobao/realtime/china" 
    }
]

# 每个源只取前 N 条 (避免内容过多撑爆 AI 上下文)
LIMIT_PER_SOURCE = 3

# Qwen 模型选择
QWEN_MODEL = "qwen-plus"

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
            # 设置超时，防止某个 RSS 源卡死
            feed = feedparser.parse(source['url'])
            
            if not feed.entries:
                print(f"   ❌ 读取失败或无内容: {source['url']}")
                continue
                
            entries = feed.entries[:LIMIT_PER_SOURCE]
            
            for entry in entries:
                title = entry.get('title', 'No Title')
                link = entry.get('link', '')
                
                # 清洗摘要：RSSHub生成的摘要通常包含图片HTML，我们只取前300字文本
                raw_summary = entry.get('summary', '')
                # 简单去除HTML标签 (也可以引入 BeautifulSoup，但为了轻量化先这样处理)
                summary = raw_summary.replace('<p>', '').replace('</p>', '\n').replace('<br>', '\n')[:300]
                
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
    
    system_prompt = "你是一个全知全能的情报官。你的目标是从纷繁复杂的全球信息中，为用户提炼出一份高价值的“内部参考”日报。"
    user_prompt = f"""
    请分析以下抓取到的原始信息（包含科技、金融、民生、八卦等）：
    
    {articles_text}
    
    请执行以下任务：
    1. **去噪与聚合**：
       - 微博/知乎热搜通常有很多娱乐明星琐事，**请过滤掉无意义的明星绯闻**。
       - **重点保留**：突发社会事件、政策变动、金融异动、科技突破、行业内幕。
    2. **风格化总结**：
       - 使用“人话”，带一点幽默和犀利，不要像新闻联播。
       - 如果是负面新闻（如股市大跌、裁员），请用客观但警示的语气。
    3. **分类输出 (HTML格式)**：
       - 🍉 **吃瓜 & 民生** (社会热点、知乎高赞、大V观点)
       - 💰 **搞钱 & 宏观** (股市、金融、房产)
       - 🤖 **硬核 & 科技** (AI、极客新闻)
    4. **排版要求**：
       - 标题加粗 `<b>...</b>`。
       - 必须包含链接 `<a href="...">[传送门]</a>`。
       - 每条新闻结束后加 `<br><br>`。
    
    直接输出内容。
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
    token = get_env_variable("PUSHPLUS_TOKEN")
    if not token:
        print("⚠️ PushPlus Token 缺失，跳过推送。")
        return

    print("🚀 正在推送到 PushPlus...")
    url = "http://www.pushplus.plus/send"
    today = datetime.now().strftime("%Y-%m-%d")
    title = f"🌍 全球情报内参 ({today})"
    
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "html"
    }
    
    try:
        resp = requests.post(url, json=data)
        print(f"✅ 推送结果: {resp.json()}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    articles = fetch_rss_data(RSS_SOURCES)
    if articles:
        summary = summarize_with_qwen(articles)
        print("\n" + "="*20 + " 内容预览 " + "="*20)
        print(summary)
        print("="*50 + "\n")
        push_pushplus(summary)
    else:
        print("📭 未获取到任何新闻。")

if __name__ == "__main__":
    main()