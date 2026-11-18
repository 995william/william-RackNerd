# RackNerd 2026 大促与补货自动监控系统 🚀

全天候自动化监控 **RackNerd 双十一（11.11）、黑色星期五（Black Friday）** 及日常超低价特惠活动，现已统一接入集中管控中枢 **[https://checkin.wwcoder.top](https://checkin.wwcoder.top)** 调度巡检，并在新活动上线时第一时间通过**企业微信机器人**将纯文本速览提醒推送到您的手机上。

---

## 📌 核心功能

* **多源监控，万无一失**：
  * **LowEndBox RackNerd 官方专栏**：官方大促文章首发站，绝不漏发。
  * **LowEndTalk (LET) Offers 专区**：监控 RackNerd 老板 Dustin 的官方发帖（带回帖翻倍福利）。
  * **NodeSeek 社区动态**：监控国内主机玩家对 RackNerd 补货与特惠的最新爆料。
* **智能去重与防轰炸**：
  * 自动记录已抓取过的帖子链接（`history.json`），只在新活动上线时即时触发企业微信推送。
* **集中管控中枢统一巡检（`checkin.wwcoder.top`）**：
  * 已移除本地高频原生 `schedule`，统一由集中管控中枢按 `interval@60`（每小时准点）通过 `workflow_dispatch` 唤醒执行；
  * 每次巡检结束自动通过根目录 `hub_reporter.py` 回传新增优惠条数、累计追踪套餐数及巡检耗时，实现全链路可视化观测。
* **极速直达**：
  * 发现新促销时立即走企业微信机器人 Webhook，微信直连秒开，无需任何代理，点开即查看抢购链接。

---

## 📁 目录结构

```text
william-RackNerd/
├── .github/workflows/
│   └── monitor.yml      # GitHub Actions 自动巡检工作流 (由 checkin.wwcoder.top 统一唤醒)
├── .env.example         # 环境变量脱敏配置模板
├── hub_reporter.py      # 集中管控中枢 (checkin.wwcoder.top) 零依赖上报 SDK
├── history.json         # 已追踪优惠链接历史去重库
├── main.py              # 多源 RSS 抓取、智能解析、企微提醒与中枢上报主入口
└── README.md            # 项目文档
```

---

## 🔒 隐私与安全说明

本仓库已做全面开源安全脱敏，本地调试可参考 `.env.example` 配置环境变量，云端运行通过 **GitHub Secrets** 安全注入：
* `QYWX_WEBHOOK`：企业微信机器人 Webhook 地址（发现新促销即时告警）；
* `CHECKIN_HUB_TOKEN`：集中管控中枢（`https://checkin.wwcoder.top`）上报鉴权令牌。

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

## ⚙️ 集中管控与 GitHub Actions 运行说明

1. 定时巡检已统一由 **[https://checkin.wwcoder.top](https://checkin.wwcoder.top)** 按每 60 分钟准点远程触发，自动记录每次巡检流水与追踪套餐统计；
2. 也可以随时在本仓库的 **Actions** 标签页下，找到 `RackNerd 大促与补货自动巡检`，点击 **Run workflow** 手动触发立即巡检。
