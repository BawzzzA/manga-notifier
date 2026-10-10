"""
แจ้งเตือนอัพเดทมังงะใหม่จาก qimanga.com (หมวด newest) เข้า Discord ผ่าน Webhook

วิธีใช้:
    python3 manga_notifier.py

ตั้งใจให้รันซ้ำเป็นระยะ (เช่นทุก 15 นาที ผ่าน Windows Task Scheduler) โดยสคริปต์
จะเช็คครั้งเดียวแล้วจบการทำงาน ไม่ใช่ loop ค้างตลอดเวลา
สถานะที่เคยเห็นแล้วจะถูกจำไว้ใน state.json เพื่อไม่แจ้งเตือนซ้ำ
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / "state.json"

API_BASE = "https://api.qimanga.com/api/v1"
API_V2_BASE = "https://api.qimanga.com/api/v2"
SITE_BASE = "https://qimanga.com"
PAGES_TO_CHECK = 2  # 20 เรื่อง/หน้า รวม 40 เรื่องล่าสุด เผื่อไว้มากกว่าพอสำหรับช่วง 15 นาที

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def load_config():
    # ลำดับความสำคัญ: environment variable DISCORD_WEBHOOK_URL (ใช้บน GitHub Actions
    # ผ่าน secret) ก่อน แล้วค่อย fallback ไปที่ config.json (ใช้ตอนรันบนเครื่องตัวเอง)
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if not webhook_url and CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        webhook_url = config.get("discord_webhook_url", "")

    if not webhook_url or "discord.com/api/webhooks" not in webhook_url:
        sys.exit(
            "ไม่พบ Discord Webhook URL ที่ถูกต้อง\n"
            "ตั้งค่าได้สองทาง: environment variable DISCORD_WEBHOOK_URL "
            "หรือใส่ค่า discord_webhook_url ในไฟล์ config.json (ดู config.example.json)"
        )
    return {"discord_webhook_url": webhook_url}


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"initialized": False, "seen": {}}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_newest_series(pages=PAGES_TO_CHECK):
    items = []
    for page in range(1, pages + 1):
        resp = requests.get(
            f"{API_BASE}/series",
            params={"sort": "newest", "page": page},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
        items.extend(payload.get("data", []))
        if page >= payload.get("totalPages", page):
            break
    return items


def fetch_latest_chapter(slug):
    try:
        resp = requests.get(
            f"{API_V2_BASE}/series/{slug}/chapters",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        chapters = resp.json().get("data", [])
        return chapters[0] if chapters else None
    except requests.RequestException:
        return None


def send_discord_notification(webhook_url, series, chapter):
    series_url = f"{SITE_BASE}/series/{series['slug']}"

    if chapter:
        chapter_url = f"{series_url}/{chapter['slug']}"
        description = f"📖 อัพเดทใหม่: **ตอนที่ {chapter['number']}**\n[อ่านตอนนี้]({chapter_url})"
    else:
        chapter_url = series_url
        description = "📖 มีการอัพเดทใหม่"

    embed = {
        "title": series["title"],
        "url": chapter_url,
        "color": 0x5865F2,
        "description": description,
        "thumbnail": {"url": series.get("cover") or ""},
        "fields": [
            {"name": "ประเภท", "value": series.get("type", "-"), "inline": True},
            {"name": "สถานะ", "value": series.get("status", "-"), "inline": True},
        ],
    }

    payload = {
        "content": f"🔔 **{series['title']}** มีตอนใหม่!",
        "embeds": [embed],
    }

    resp = requests.post(webhook_url, json=payload, timeout=15)
    if resp.status_code == 429:
        retry_after = resp.json().get("retry_after", 1)
        time.sleep(retry_after + 0.5)
        resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()


def main():
    config = load_config()
    webhook_url = config["discord_webhook_url"]

    state = load_state()
    seen = state.setdefault("seen", {})

    try:
        series_list = fetch_newest_series()
    except requests.RequestException as e:
        print(f"[ERROR] ดึงข้อมูลจาก qimanga.com ไม่สำเร็จ: {e}")
        sys.exit(1)

    is_first_run = not state.get("initialized", False)
    new_updates = []

    for series in series_list:
        sid = str(series["id"])
        created_at = series["createdAt"]
        prev_created_at = seen.get(sid)
        if prev_created_at is None or created_at > prev_created_at:
            if not is_first_run:
                new_updates.append(series)
        seen[sid] = created_at

    if is_first_run:
        state["initialized"] = True
        save_state(state)
        print(
            f"[INIT] บันทึกสถานะเริ่มต้น {len(series_list)} เรื่อง "
            "(ยังไม่แจ้งเตือนย้อนหลัง) รันครั้งถัดไปจะเริ่มแจ้งเตือนอัพเดทใหม่จริง"
        )
        return

    if not new_updates:
        print("[OK] ไม่มีอัพเดทใหม่")
        save_state(state)
        return

    # เรียงให้เรื่องที่เก่ากว่าถูกส่งก่อน เพื่อให้ลำดับในแชทเป็นไปตามเวลาจริง
    new_updates.reverse()

    print(f"[NEW] พบอัพเดทใหม่ {len(new_updates)} เรื่อง กำลังส่งแจ้งเตือน...")
    for series in new_updates:
        chapter = fetch_latest_chapter(series["slug"])
        try:
            send_discord_notification(webhook_url, series, chapter)
            print(f"  -> ส่งแจ้งเตือนแล้ว: {series['title']}")
        except requests.RequestException as e:
            print(f"  -> ส่งแจ้งเตือนไม่สำเร็จสำหรับ {series['title']}: {e}")
        time.sleep(1.2)  # เว้นระยะกันโดน Discord rate limit

    save_state(state)


if __name__ == "__main__":
    main()
