# 阅读榜升级说明

本分支为现有女频新书榜看板增加：

- 女频阅读榜每日抓取，入口路由为 `0_0`。
- 阅读榜独立快照：`data/fanqie_female_reading_ranks_YYYYMMDD.json`。
- 阅读榜最新接口：`api/reading/lastest/all.json`。
- 双榜交叉接口：`api/cross/lastest/all.json`。
- 阅读榜页面：`reading.html`。
- 双榜市场雷达：`cross.html`。

## 首次启用

合并到 `main` 后，在 GitHub 仓库中进入：

`Actions → Daily Fanqie Rank Scraper → Run workflow`

首次运行会抓取当天阅读榜并生成接口。之后每天北京时间 08:00 自动更新。

## 分析口径

- 新书榜用于观察作者供给和新题材风向。
- 阅读榜用于验证30万字以上成熟作品的读者需求。
- 双榜交叉分析基于标题和简介关键词，仅用于提出选题假设，不代表作品留存、收入或必然趋势。
