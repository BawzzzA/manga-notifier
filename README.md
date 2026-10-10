# แจ้งเตือนมังงะอัพเดทใหม่ (qimanga.com) เข้า Discord

สคริปต์นี้เช็คหน้า [qimanga.com/browse?sort=newest](https://qimanga.com/browse?sort=newest)
ผ่าน API ตรงของเว็บ (ไม่ scrape HTML) แล้วส่งแจ้งเตือนเข้า Discord ผ่าน Webhook
เฉพาะเรื่องที่ "อัพเดทใหม่" เท่านั้น (เทียบกับครั้งก่อนที่เช็ค ไม่แจ้งซ้ำ)

สคริปต์ออกแบบให้ **รันครั้งเดียวแล้วจบ** ต่อการเรียกหนึ่งครั้ง เหมาะกับการตั้งให้
ระบบข้างนอกเรียกทุก 15 นาที — แนะนำให้ใช้ **GitHub Actions** (วิธีที่ 1) เพราะรันบน
คลาวด์ของ GitHub ฟรี ไม่ต้องเปิดคอมตัวเองทิ้งไว้เลย

---

## วิธีที่ 1 (แนะนำ): รันบน GitHub Actions — ไม่ต้องเปิดคอมค้าง

### 1.1 สร้าง Discord Webhook

1. เปิด Discord เข้า server ที่ต้องการให้แจ้งเตือน
2. ไปที่ตั้งค่าช่อง (Channel) ที่ต้องการ → **Integrations** → **Webhooks** → **New Webhook**
3. ตั้งชื่อ (เช่น "Manga Notifier") แล้วกด **Copy Webhook URL** เก็บไว้

### 1.2 สร้าง repo บน GitHub (ผ่านเว็บ ไม่ต้องลง CLI)

1. เข้า https://github.com/new
2. ตั้งชื่อ repo เช่น `manga-notifier`
3. เลือก **Public** (เพื่อให้ GitHub Actions รันได้ไม่จำกัดฟรี — โค้ดเป็น public ได้
   เพราะ Webhook URL จะถูกเก็บเป็น secret แยก ไม่ได้อยู่ในโค้ด)
4. **ไม่ต้อง** ติ๊ก Add README / .gitignore / license (เดี๋ยว push จากเครื่องเราไปทับ)
5. กด Create repository แล้วจะได้ URL repo เช่น `https://github.com/<username>/manga-notifier.git`

### 1.3 Push โค้ดจากโฟลเดอร์นี้ขึ้น GitHub

เปิด terminal (WSL หรือ Git Bash ก็ได้) ที่โฟลเดอร์นี้ แล้วรัน (แก้ URL ให้เป็น repo
ของตัวเอง):

```bash
git init
git add .
git commit -m "manga notifier"
git branch -M main
git remote add origin https://github.com/<username>/manga-notifier.git
git push -u origin main
```

### 1.4 ตั้ง Secret เก็บ Webhook URL

1. ในหน้า repo บน GitHub → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
   - Name: `DISCORD_WEBHOOK_URL`
   - Secret: วาง Webhook URL ที่ copy มาจากขั้นตอน 1.1
3. กด **Add secret**

### 1.5 ทดสอบรัน

1. ไปที่แท็บ **Actions** ของ repo → เลือก workflow **Manga Notifier**
2. กด **Run workflow** (ปุ่มมุมขวา) เพื่อรันทันทีโดยไม่ต้องรอ schedule
3. **รันครั้งแรก**: จะยังไม่มีแจ้งเตือนเข้า Discord เพราะสคริปต์ต้องบันทึก
   "สถานะเริ่มต้น" ก่อน (ป้องกันไม่ให้ยิงแจ้งเตือนเก่าทั้งหมดรัวๆ) ดูได้จาก log ว่าขึ้น
   `[INIT] บันทึกสถานะเริ่มต้น ...` และจะมีไฟล์ `state.json` ถูก commit กลับเข้า repo
   อัตโนมัติ
4. ตั้งแต่รันครั้งที่สองเป็นต้นไป (ทั้งแบบกด Run workflow เองหรือรอ schedule) ถ้ามีเรื่อง
   อัพเดทใหม่จริงจะเห็น log ขึ้น `[NEW] พบอัพเดทใหม่ ...` และมีข้อความส่งเข้า Discord

จากนี้ workflow จะรันอัตโนมัติทุก 15 นาทีตลอดไป (ตราบใดที่ repo ยังอยู่) — ปิดคอม
ตัวเองได้เลย เพราะรันบนเซิร์ฟเวอร์ของ GitHub ไม่เกี่ยวกับเครื่องเรา

> หมายเหตุ: `schedule` ของ GitHub Actions ไม่ได้ตรงเวลาเป๊ะเสมอไป (อาจคลาดเคลื่อนไม่กี่
> นาทีช่วงที่ GitHub Actions คนใช้เยอะ) แต่โดยรวมยังถือว่าใกล้เรียลไทม์มากพอสำหรับงานนี้

---

## วิธีที่ 2 (ทางเลือก): รันบนเครื่องตัวเองผ่าน Windows Task Scheduler

ใช้วิธีนี้ถ้าไม่อยากพึ่ง GitHub แต่ต้อง **เปิดคอมทิ้งไว้ตลอด** (ไม่ sleep/shutdown)
งานถึงจะรันได้

### 2.1 ตั้งค่า config.json

1. คัดลอกไฟล์ `config.example.json` เป็น `config.json`
2. เปิด `config.json` แล้ววาง Webhook URL ที่ copy มาแทนค่า `discord_webhook_url`

```json
{
  "discord_webhook_url": "https://discord.com/api/webhooks/....."
}
```

### 2.2 ติดตั้ง Python และไลบรารีที่ใช้ (ฝั่ง Windows)

1. ถ้ายังไม่มี Python บน Windows ให้โหลดจาก https://www.python.org/downloads/
   (ตอนติดตั้ง ให้ติ๊ก "Add python.exe to PATH" ด้วย)
2. เปิด Command Prompt (cmd) แล้วรัน:
   ```
   cd "C:\Users\apiwa\Desktop\แจ้งเตือนมังงะ"
   pip install -r requirements.txt
   ```

### 2.3 ทดสอบรันด้วยมือก่อน

```
python manga_notifier.py
```

พฤติกรรมรันครั้งแรก/ครั้งต่อไปเหมือนวิธีที่ 1 (ครั้งแรกจะยังไม่แจ้งเตือน)

### 2.4 ตั้งให้รันอัตโนมัติทุก 15 นาทีด้วย Task Scheduler

1. เปิด **Task Scheduler** (ค้นหาจากเมนู Start)
2. คลิก **Create Task...**
3. แท็บ **General**: ตั้งชื่อ เช่น `Manga Notifier`
4. แท็บ **Triggers** → **New...** → เลือก **Daily**, ตั้งเวลาเริ่ม แล้วติ๊ก
   **Repeat task every** → `15 minutes` → **for a duration of** → `Indefinitely`
5. แท็บ **Actions** → **New...** → Action: `Start a program`
   - Program/script: `C:\Users\apiwa\Desktop\แจ้งเตือนมังงะ\run.bat`
6. กด OK แล้วทดสอบคลิกขวาที่ task → **Run**

ผลลัพธ์และ error จะถูกบันทึกไว้ในไฟล์ `notifier.log` ในโฟลเดอร์นี้

---

## การทำงานภายใน (สรุปสั้นๆ)

- ดึงรายชื่อเรื่องล่าสุดจาก API จริงของเว็บ: `GET https://api.qimanga.com/api/v1/series?sort=newest`
- เทียบกับค่า `createdAt` ที่บันทึกไว้ครั้งก่อนในไฟล์ `state.json`
- ถ้าเจอเรื่องใหม่หรือ `createdAt` เปลี่ยน (= มีอัพเดท) จะดึงเลขตอนล่าสุดจาก
  `GET https://api.qimanga.com/api/v2/series/{slug}/chapters` มาแนบในข้อความด้วย
- ส่ง embed เข้า Discord ผ่าน Webhook พร้อมปก, ชื่อเรื่อง, เลขตอน และลิงก์อ่านตอนนั้นโดยตรง
- Webhook URL อ่านจาก environment variable `DISCORD_WEBHOOK_URL` ก่อน (ใช้บน GitHub
  Actions ผ่าน secret) ถ้าไม่มีจะอ่านจาก `config.json` แทน (ใช้ตอนรันบนเครื่องตัวเอง)

## ไฟล์ในโปรเจกต์

| ไฟล์ | หน้าที่ |
|---|---|
| `manga_notifier.py` | สคริปต์หลัก |
| `.github/workflows/manga-notifier.yml` | ตั้ง GitHub Actions ให้รันทุก 15 นาที |
| `config.json` | เก็บ Discord Webhook URL ตอนรันบนเครื่องตัวเอง (ต้องสร้างเอง ไม่ commit) |
| `config.example.json` | ตัวอย่างไฟล์ config |
| `state.json` | จำสถานะเรื่องที่เคยแจ้งเตือนแล้ว (สร้าง/commit กลับอัตโนมัติ) |
| `run.bat` | ตัวช่วยให้ Task Scheduler เรียกใช้งานง่ายๆ (วิธีที่ 2) |
| `notifier.log` | log ผลการรันแต่ละครั้งตอนรันบนเครื่องตัวเอง (สร้างอัตโนมัติ) |
