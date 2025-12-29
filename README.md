全球新闻 AI 摘要推送机器人 (Qwen + PushPlus 版)

这个方案利用 GitHub Actions 的海外网络环境抓取全球新闻（解决墙外新闻获取问题），利用阿里 Qwen (通义千问) 进行中文总结，并通过 PushPlus 直接推送到你和朋友的个人微信上。

1. 架构设计

运行环境: GitHub Actions。

作用: 充当“海外代理”。GitHub 服务器在海外，可以直接访问 BBC, NYT, TechCrunch 等被墙网站抓取 RSS 数据。

数据源: RSS Feeds。

作用: 获取结构化的新闻列表。

AI 引擎: Qwen (通义千问 - qwen-plus)。

作用: 国产大模型，中文总结能力极强，API 稳定且国内直连。

推送通道: PushPlus (推送加)。

作用: 无需安装新APP，直接通过微信公众号接收消息。支持群组推送（方便你和朋友一起看）。

2. 准备工作

A. 获取 Qwen API Key (DashScope)

注册并登录 阿里云百炼 (DashScope)。

开通“通义千问”服务。

在“API-KEY管理”中创建一个新的 API Key。

B. 配置推送渠道 (PushPlus)

访问 PushPlus 官网 (pushplus.plus)。

点击“登录”，使用微信扫码登录。

登录成功后，点击“一对一推送”，你会看到一个 Token。复制它。

注: 如果想推给多个朋友，可以使用“一对多推送”功能，创建一个群组，让朋友扫码加入群组，然后使用群组编码进行推送。

C. 准备 GitHub 仓库

将本项目代码上传到 GitHub。

在仓库的 Settings -> Secrets and variables -> Actions 中添加以下 Repository secrets:

DASHSCOPE_API_KEY (填入你的阿里云 API Key)

PUSHPLUS_TOKEN (填入刚才获取的 PushPlus Token)

3. 部署自动化 (GitHub Actions)

在你的仓库中创建 .github/workflows/daily_news.yml 文件，内容如下：

name: Daily News AI Summary

on:
  schedule:
    # 北京时间早上 8:00 (UTC 0:00) 自动运行
    - cron: '0 0 * * *'
  workflow_dispatch: # 允许手动点击按钮触发

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install requests feedparser openai

      - name: Run News Bot
        env:
          DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}
          PUSHPLUS_TOKEN: ${{ secrets.PUSHPLUS_TOKEN }}
        run: python auto_news_bot.py


4. 常见 RSS 源推荐

科技类:

TechCrunch: https://techcrunch.com/feed/

Hacker News: https://news.ycombinator.com/rss

综合/世界 (GitHub Actions 可直接访问):

NYT World: https://rss.nytimes.com/services/xml/rss/nyt/World.xml

BBC World: http://feeds.bbci.co.uk/news/world/rss.xml

Reuters: https://www.reutersagency.com/feed/?best-topics=political-general&post_kind=best

5. 成本分析

服务器: 免费 (GitHub Actions)

AI API: 极低 (Qwen Token 价格便宜，且有免费额度)

推送: 免费 (PushPlus 个人版免费)
