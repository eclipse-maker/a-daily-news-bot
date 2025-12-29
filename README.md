# 全球新闻 AI 摘要推送机器人（Qwen + PushPlus 版）

> ✨ 利用 **GitHub Actions 的海外网络环境** 抓取全球新闻，通过 **阿里通义千问（Qwen）** 自动生成中文摘要，并用 **PushPlus 推送到个人微信** —— 无需翻墙，免费、自动化、支持群组共享！

---

## 🔧 方案架构

| 组件 | 作用 |
|------|------|
| **运行环境：GitHub Actions** | 充当“海外代理”。GitHub 服务器位于境外，可直接访问 BBC、NYT、TechCrunch 等被墙网站。 |
| **数据源：RSS Feeds** | 获取结构化、实时的新闻列表（无需爬虫解析 HTML）。 |
| **AI 引擎：Qwen（通义千问 - qwen-plus）** | 国产大模型，**中文总结能力强**，API 稳定，国内直连无延迟。 |
| **推送通道：PushPlus（推送加）** | 无需安装新 App，**直接通过微信公众号接收消息**，支持“一对多”群组推送，方便与朋友共享。 |

---

## 🛠️ 准备工作

### A. 获取 Qwen API Key（DashScope）
1. 访问 [阿里云百炼（DashScope）](https://dashscope.aliyun.com/)
2. 注册并登录，**开通“通义千问”服务**
3. 进入 **API-KEY 管理** → 创建新 Key → 复制保存

### B. 配置推送渠道（PushPlus）
1. 访问 [PushPlus 官网](https://www.pushplus.plus/)
2. **微信扫码登录**
3. 登录后点击 **“一对一推送”**，复制页面上的 **Token**
   > 💡 想推给多个朋友？使用 **“一对多推送”** 创建群组，邀请好友扫码加入，后续用 **群组编码（HUB）** 推送即可。

### C. 准备 GitHub 仓库
1. 将本项目代码上传到你的 GitHub 仓库
2. 进入仓库 **Settings → Secrets and variables → Actions**
3. 添加以下 **Repository secrets**：
   - `DASHSCOPE_API_KEY` → 填入你的阿里云 API Key
   - `PUSHPLUS_TOKEN` → 填入 PushPlus Token（或群组 HUB 编码）

---

## ⚙️ 部署自动化（GitHub Actions）

在仓库中创建文件：  
`.github/workflows/daily_news.yml`

```yaml
name: Daily News AI Summary

on:
  schedule:
    # 北京时间早上 8:00 (UTC 0:00) 自动运行
    - cron: '0 0 * * *'
  workflow_dispatch: # 允许手动触发

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
