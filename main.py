# -*- coding: utf-8 -*-
"""
RackNerd 优惠与大促自动化监控脚本 (V2 增强版)
特点：
1. 深入适配英文原站（LowEndBox、LowEndTalk），智能识别英文大促专有名词；
2. 正则自动提取价格（如 $10.99/yr）、活动类型（黑五/双十一/网一/闪购）及赠送双倍流量等专属福利；
3. 输出高可读性的中英双语企业微信 Markdown 卡片，直击重点；
4. 多源去重与状态持久化。
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# 解决 Windows 控制台 utf-8 编码问题
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 从系统环境变量读取企业微信 Webhook 地址（由 GitHub Secrets 安全注入）
WEBHOOK_URL = os.environ.get("QYWX_WEBHOOK")

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def get_beijing_time():
    """获取当前北京时间"""
    tz_bj = timezone(timedelta(hours=8))
    return datetime.now(tz_bj).strftime("%Y-%m-%d %H:%M:%S")

def parse_english_promotion(title, desc=""):
    """
    针对海外英文原站（LowEndBox / LowEndTalk）深度解析大促专有名词与核心信息
    """
    text = (title + " " + desc).lower()
    
    tags = []
    # 1. 促销类型识别
    if "black friday" in text or " bf " in text or "bf20" in text:
        tags.append("🔥 黑色星期五 (Black Friday)")
    elif "11.11" in text or "singles" in text or "11/11" in text or "双十一" in text:
        tags.append("🎉 双十一大促 (11.11 Specials)")
    elif "cyber monday" in text or " cm " in text:
        tags.append("⚡ 网络星期一 (Cyber Monday)")
    elif "giveaway" in text or "free vps" in text:
        tags.append("🎁 官方抽奖/送福利 (Giveaway)")
    elif "flash sale" in text or "special" in text:
        tags.append("🏷️ 特价闪购 (Specials)")
    else:
        tags.append("📢 优惠公告")

    # 2. 关键福利识别（如回帖送双倍流量）
    bonus = []
    if "double bandwidth" in text or "double transfer" in text or "double ram" in text:
        bonus.append("回帖送双倍流量/带宽 (Double Bandwidth)")
    if "free" in text and ("license" in text or "vps" in text):
        bonus.append("含免费授权/赠送机型")

    # 3. 价格提取（正则匹配 $xx.xx/yr 等）
    price_match = re.search(r"\$([0-9]+(?:\.[0-9]{1,2})?)\s*(?:/|\s*per\s*)?\s*(?:yr|year|annual|annually)", text)
    detected_price = f"${price_match.group(1)} / 年" if price_match else None

    # 4. 重点机房识别
    locations = []
    if "los angeles" in text or "dc-02" in text or "dc02" in text:
        locations.append("洛杉矶 (DC-02)")
    if "san jose" in text:
        locations.append("圣何塞")
    if "seattle" in text:
        locations.append("西雅图")

    return {
        "tags": tags,
        "bonus": bonus,
        "price": detected_price,
        "locations": locations
    }

def send_wechat_notification(title, source, link, pub_date, parsed_info=None, extra_summary=""):
    """发送企业微信纯文本格式通知（微信内可直接完整显示，无需点击前往企微）"""
    bj_time = get_beijing_time()
    
    lines = [
        "【🔔 RackNerd 促销监控提醒】",
        "----------------------------------------",
        f"来源渠道：{source}"
    ]
    
    if parsed_info and parsed_info.get("tags"):
        tag_str = " | ".join(parsed_info["tags"])
        lines.append(f"活动类型：{tag_str}")
        
    lines.append(f"原文标题：{title}")
    lines.append(f"检测时间：{bj_time}")
    
    if parsed_info:
        highlights = []
        if parsed_info.get("price"):
            highlights.append(f"起步价格：{parsed_info['price']} (通常续费不涨价)")
        if parsed_info.get("bonus"):
            highlights.append(f"官方专属福利：{'、'.join(parsed_info['bonus'])}")
        if parsed_info.get("locations"):
            highlights.append(f"热门美西机房：{' / '.join(parsed_info['locations'])}")
            
        if highlights:
            lines.append("\n【核心要点速读】")
            for h in highlights:
                lines.append(f"• {h}")

    if extra_summary and not parsed_info:
        clean_summary = extra_summary[:140].replace("\n", " ").strip()
        lines.append(f"\n内容摘要：{clean_summary}...")
        
    lines.append("\n【直达抢购 / 详情链接】")
    lines.append(link)
    lines.append("----------------------------------------")

    content_str = "\n".join(lines)

    if not WEBHOOK_URL:
        print("[ERROR] 缺少环境变量 QYWX_WEBHOOK，请在 GitHub Secrets 中配置！")
        return False

    payload = {
        "msgtype": "text",
        "text": {
            "content": content_str
        }
    }

    try:
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                try:
                    print(f"[SUCCESS] 纯文本推送成功: {title}")
                except Exception:
                    print("[SUCCESS] 纯文本推送成功")
                return True
            else:
                print(f"[ERROR] 纯文本推送返回错误: {result}")
                return False
    except Exception as e:
        print(f"[ERROR] 发送企业微信请求异常: {e}")
        return False

def load_history():
    """加载已推送历史记录"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] 读取历史记录失败: {e}")
    return {"seen_links": [], "last_run": None}

def save_history(history):
    """保存推送历史记录（最多保留最新 300 条）"""
    history["seen_links"] = history["seen_links"][-300:]
    history["last_run"] = get_beijing_time()
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 历史记录已更新，当前缓存记录数: {len(history['seen_links'])}")
    except Exception as e:
        print(f"[ERROR] 保存历史记录失败: {e}")

def fetch_rss(url):
    """抓取 RSS 并返回 ElementTree 根节点"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            return ET.fromstring(content)
    except Exception as e:
        print(f"[WARN] 抓取 RSS 异常 [{url}]: {e}")
        return None

def check_lowendbox():
    """监控 LowEndBox RackNerd 官方专栏 (英文站)"""
    items_found = []
    root = fetch_rss("https://lowendbox.com/tag/racknerd/feed/")
    if root is None:
        return items_found
    
    channel = root.find("channel")
    if channel is None:
        return items_found

    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        date_el = item.find("pubDate")
        desc_el = item.find("description")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        link = link_el.text.strip() if link_el is not None and link_el.text else ""
        pub_date = date_el.text.strip() if date_el is not None and date_el.text else ""
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        desc = re.sub(r"<[^>]+>", "", desc)

        if title and link:
            parsed = parse_english_promotion(title, desc)
            items_found.append({
                "source": "LowEndBox 官方专栏 (英文原站)",
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "summary": desc,
                "parsed": parsed
            })
    return items_found

def check_lowendtalk():
    """监控 LowEndTalk Offers 专区中与 RackNerd 相关的英文帖子"""
    items_found = []
    root = fetch_rss("https://lowendtalk.com/categories/offers/feed.rss")
    if root is None:
        return items_found
    
    channel = root.find("channel")
    if channel is None:
        return items_found

    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        date_el = item.find("pubDate")
        desc_el = item.find("description")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        link = link_el.text.strip() if link_el is not None and link_el.text else ""
        pub_date = date_el.text.strip() if date_el is not None and date_el.text else ""
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        desc = re.sub(r"<[^>]+>", "", desc)

        text_to_search = (title + " " + desc).lower()
        if "racknerd" in text_to_search or "dustinc" in text_to_search:
            parsed = parse_english_promotion(title, desc)
            items_found.append({
                "source": "LowEndTalk 官方发布区 (英文原站)",
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "summary": desc,
                "parsed": parsed
            })
    return items_found

def check_nodeseek():
    """监控 NodeSeek 社区中有关 RackNerd 大促/补货的讨论 (中文站)"""
    items_found = []
    root = fetch_rss("https://www.nodeseek.com/rss.xml")
    if root is None:
        return items_found
    
    channel = root.find("channel")
    if channel is None:
        return items_found

    brand_keywords = ["racknerd", "rn", "rn机房"]
    action_keywords = ["黑五", "11.11", "双十一", "双11", "促销", "大促", "特惠", "补货", "特价", "闪购", "活动", "折扣", "优惠"]

    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        date_el = item.find("pubDate")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        link = link_el.text.strip() if link_el is not None and link_el.text else ""
        pub_date = date_el.text.strip() if date_el is not None and date_el.text else ""

        title_lower = title.lower()
        has_brand = any(b in title_lower for b in brand_keywords)
        has_action = any(a in title_lower for a in action_keywords)

        if has_brand and has_action and link:
            items_found.append({
                "source": "NodeSeek 社区动态 (中文圈)",
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "summary": "",
                "parsed": {
                    "tags": ["💬 国内玩家讨论 / 补货爆料"],
                    "bonus": [],
                    "price": None,
                    "locations": []
                }
            })
    return items_found

def main():
    print(f"[{get_beijing_time()}] 开始执行 RackNerd 监控任务 (V2)...")

    # 测试模式
    if "--test" in sys.argv:
        print("[INFO] 当前处于测试模式，发送一条格式化样例推送...")
        sample_parsed = {
            "tags": ["🔥 黑色星期五 (Black Friday)", "🎉 双十一大促"],
            "bonus": ["回帖送双倍流量/带宽 (Double Bandwidth)"],
            "price": "$10.99 / 年",
            "locations": ["洛杉矶 (DC-02)", "圣何塞"]
        }
        send_wechat_notification(
            title="RackNerd - 2026 Black Friday Specials! KVM VPS from $10.99/Year + Free Double Bandwidth!",
            source="LowEndTalk 官方发布区 (英文原站)",
            link="https://lowendtalk.com/categories/offers",
            pub_date=get_beijing_time(),
            parsed_info=sample_parsed,
            extra_summary="测试推送：监控系统运行正常，英文专有名词、价格提取和中英双语速览已全面优化！"
        )
        return

    history = load_history()
    seen_links = set(history.get("seen_links", []))
    is_initial_run = (len(seen_links) == 0)

    all_items = []

    # 1. 抓取 LowEndBox
    print("[INFO] 正在检查 LowEndBox RackNerd 专栏...")
    leb_items = check_lowendbox()
    all_items.extend(leb_items)
    print(f"[INFO] LowEndBox 抓取到 {len(leb_items)} 条记录")

    # 2. 抓取 LowEndTalk
    print("[INFO] 正在检查 LowEndTalk Offers 专区...")
    let_items = check_lowendtalk()
    all_items.extend(let_items)
    print(f"[INFO] LowEndTalk 抓取到 {len(let_items)} 条相关记录")

    # 3. 抓取 NodeSeek
    print("[INFO] 正在检查 NodeSeek 社区动态...")
    ns_items = check_nodeseek()
    all_items.extend(ns_items)
    print(f"[INFO] NodeSeek 抓取到 {len(ns_items)} 条相关记录")

    new_items = []
    for item in all_items:
        link = item["link"]
        if link not in seen_links:
            new_items.append(item)
            seen_links.add(link)

    print(f"[INFO] 本次检测发现新内容共 {len(new_items)} 条")

    # 首次初始化运行
    if is_initial_run:
        print("[INFO] 首次初始化：将已有数据作为基准线，记录入库。")
        history["seen_links"] = list(seen_links)
        save_history(history)
        return

    # 非首次运行：逐条推送新促销
    for item in new_items:
        send_wechat_notification(
            title=item["title"],
            source=item["source"],
            link=item["link"],
            pub_date=item.get("pub_date", ""),
            parsed_info=item.get("parsed"),
            extra_summary=item.get("summary", "")
        )

    if new_items:
        history["seen_links"] = list(seen_links)
        save_history(history)
    else:
        print("[INFO] 暂无新大促上线，巡检完成。")

if __name__ == "__main__":
    main()
