# RackNerd 2026 大促与补货自动监控系统 🚀

全天候自动化监控 **RackNerd 双十一（11.11）、黑色星期五（Black Friday）** 及日常超低价特惠活动，并在活动上线时第一时间通过**企业微信机器人**将 Markdown 格式卡片推送到您的手机上。

---

## 📌 核心功能

* **多源监控，万无一失**：
  * **LowEndBox RackNerd 官方专栏**：官方大促文章首发站，绝不漏发。
  * **LowEndTalk (LET) Offers 专区**：监控 RackNerd 老板 Dustin 的官方发帖（带回帖翻倍福利）。
  * **NodeSeek 社区动态**：监控国内主机玩家对 RackNerd 补货与特惠的最新爆料。
* **智能去重与防轰炸**：
  * 自动记录已抓取过的帖子链接（`history.json`），只在新活动上线时推送。
* **零服务器成本**：
  * 基于 **GitHub Actions** 免费云端巡检，每 20 分钟自动执行一次。
* **极速直达**：
  * 推送走企业微信机器人 Webhook，微信直连秒开，无需任何代理，点开即查看抢购链接。

---

## 🔒 隐私与安全说明

本仓库已做全面开源安全脱敏：
* 企业微信 Webhook 地址已通过 **GitHub Secrets (`QYWX_WEBHOOK`)** 进行加密保护；
* 仓库公开后不会泄露任何个人机器人的 Webhook Key。

---

## 🛠️ 本地运行与调试

如果需要在本地手动执行：

```bash
# 测试推送（验证企业微信机器人连通性）
python main.py --test

# 执行常规巡检
python main.py
```

---

## ⚙️ GitHub Actions 运行说明

1. 仓库已配置好每日 24 小时每 20 分钟执行一次的定时任务；
2. 可以在本仓库的 **Actions** 标签页下，找到 `RackNerd Promotion Monitor`，点击 **Run workflow** 随时手动触发立即巡检。
