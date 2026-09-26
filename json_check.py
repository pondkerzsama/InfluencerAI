import json
import re  # <- 1. เพิ่ม import re สำหรับใช้ Regular Expression

VIDEO_FILE = "dataset/data-set-with-comment.json"
COMMENT_FILE = "data/comment.json"
OUTPUT_FILE = "data/valid_videos.json"  
MIN_COMMENTS_REQUIRED = 5               

def check_data_quality():
    print("🔍 กำลังเริ่มตรวจสอบคุณภาพข้อมูล...\n")

    try:
        with open(VIDEO_FILE, 'r', encoding='utf-8') as vf:
            videos = json.load(vf)
        with open(COMMENT_FILE, 'r', encoding='utf-8') as cf:
            comments = json.load(cf)
    except FileNotFoundError as e:
        print(f"❌ หาไฟล์ไม่พบ: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ ไฟล์ JSON ผิดรูปแบบ อ่านไม่ได้: {e}")
        return

    # 2. ปรับปรุงการนับคอมเมนต์: นับเฉพาะคอมเมนต์ที่มี "ภาษาไทย" ตามคำแนะนำ
    comment_counts = {}
    thai_pattern = re.compile(r'[\u0E00-\u0E7F]') # รูปแบบเช็กตัวอักษรไทย ก-ฮ สระ วรรณยุกต์[cite: 4]

    for c in comments:
        url = c.get("videoWebUrl")
        text = c.get("text", "")
        
        if url:
            # เช็กว่าข้อความคอมเมนต์มีตัวอักษรไทยปนอยู่หรือไม่[cite: 4]
            if thai_pattern.search(text):
                comment_counts[url] = comment_counts.get(url, 0) + 1

    valid_videos = []
    seen_urls = set()  
    issues_summary = {
        "missing_fields": 0,
        "duplicate": 0,
        "low_thai_comments": 0, # เปลี่ยนชื่อให้ชัดเจนว่าคอมเมนต์ไทยน้อย
        "scrape_incomplete": 0,  
    }
    scrape_gap_notes = []

    for v in videos:
        url = v.get("webVideoUrl")

        # เช็ก 1: ฟิลด์ที่จำเป็น
        if not url or "authorMeta" not in v or "playCount" not in v:
            issues_summary["missing_fields"] += 1
            continue

        # เช็ก 2: คลิปซ้ำ
        if url in seen_urls:
            issues_summary["duplicate"] += 1
            continue
        seen_urls.add(url)

        # เช็ก 3: จำนวน "คอมเมนต์ภาษาไทย" ที่สแครปได้จริง
        c_count = comment_counts.get(url, 0)
        if c_count < MIN_COMMENTS_REQUIRED:
            issues_summary["low_thai_comments"] += 1
            continue

        # เช็กเสริม: แจ้งเตือน scrape gap
        declared_count = v.get("commentCount", 0)
        if declared_count > 0 and c_count < declared_count * 0.5:
            issues_summary["scrape_incomplete"] += 1
            scrape_gap_notes.append(
                f"  - {url} : ระบุไว้ {declared_count} คอมเมนต์ แต่มีคอมเมนต์ไทยแค่ {c_count}"
            )

        valid_videos.append(v)

    # สรุปผล
    print("📊 สถิติจากข้อมูลทั้งหมด:")
    print(f"คลิปวิดีโอตั้งต้น: {len(videos)} คลิป")
    print(f"คอมเมนต์ตั้งต้น: {len(comments)} ข้อความ\n")

    print("⚠️ คลิปที่ถูกคัดออก:")
    print(f"- ข้อมูลฟิลด์สำคัญขาดหาย: {issues_summary['missing_fields']} คลิป")
    print(f"- คลิปซ้ำ (URL ซ้ำ): {issues_summary['duplicate']} คลิป")
    print(f"- คอมเมนต์ภาษาไทยน้อยกว่า {MIN_COMMENTS_REQUIRED} ข้อความ: {issues_summary['low_thai_comments']} คลิป\n")

    print(f"🟡 คลิปที่ผ่านเกณฑ์ แต่จำนวนคอมเมนต์น้อยกว่าที่ระบบ TikTok ระบุเกิน 50%: "
          f"{issues_summary['scrape_incomplete']} คลิป")
    if scrape_gap_notes:
        for note in scrape_gap_notes[:5]:  
            print(note)
        if len(scrape_gap_notes) > 5:
            print(f"  ... และอีก {len(scrape_gap_notes) - 5} คลิป")
    print()

    print(f"✅ คลิปที่ผ่านเกณฑ์พร้อมใช้งานจริง: {len(valid_videos)} คลิป")
    print("--------------------------------------------------")

    if valid_videos:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
            json.dump(valid_videos, out, ensure_ascii=False, indent=2)
        print(f"💾 บันทึกรายชื่อคลิปที่ผ่านเกณฑ์ไว้ที่ {OUTPUT_FILE}")
        print("สเตปถัดไป: นำไฟล์นี้ไป Join กับคอมเมนต์ด้วย data_merger.py")
    else:
        print("⚠️ ไม่มีคลิปผ่านเกณฑ์เลย ลองลด MIN_COMMENTS_REQUIRED หรือตรวจสอบไฟล์ต้นทาง")

if __name__ == "__main__":
    check_data_quality()