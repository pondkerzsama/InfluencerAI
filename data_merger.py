import json
import re

# ไฟล์ตั้งต้น
VALID_VIDEOS_FILE = "data/valid_videos.json" # ไฟล์ที่เพิ่งรันผ่านตะกี้
COMMENT_FILE = "data/comment.json"           # ไฟล์คอมเมนต์ดิบ
OUTPUT_FILE = "data/merged_ready.json"       # ไฟล์ผลลัพธ์ที่จะส่งให้ AI

def merge_data():
    print("🔄 กำลังเริ่มประกอบร่างข้อมูล (Merge Data)...")
    
    try:
        with open(VALID_VIDEOS_FILE, 'r', encoding='utf-8') as vf:
            valid_videos = json.load(vf)
        with open(COMMENT_FILE, 'r', encoding='utf-8') as cf:
            all_comments = json.load(cf)
    except FileNotFoundError as e:
        print(f"❌ หาไฟล์ไม่พบ: {e}")
        return

    # กรองเฉพาะคอมเมนต์ภาษาไทยก่อนรวมร่าง (ลดภาระ AI)
    thai_pattern = re.compile(r'[\u0E00-\u0E7F]')
    
    # 1. จัดกลุ่มคอมเมนต์ตาม URL
    comments_by_url = {}
    for c in all_comments:
        url = c.get("videoWebUrl")
        text = c.get("text", "")
        
        if url and thai_pattern.search(text):
            if url not in comments_by_url:
                comments_by_url[url] = []
                
            # เลือกเก็บเฉพาะฟิลด์คอมเมนต์ที่ใช้จริง
            comments_by_url[url].append({
                "text": text,
                "likes": c.get("diggCount", 0),
                "username": c.get("uniqueId", "")
            })

    merged_data = []
    
    # 2. วนลูปวิดีโอเพื่อดึงฟิลด์ที่ต้องการและเสียบคอมเมนต์เข้าไป
    for v in valid_videos:
        url = v.get("webVideoUrl")
        author = v.get("authorMeta", {})
        
        merged_video = {
            "webVideoUrl": url,
            "video_id": v.get("id", ""),
            # Flatten authorMeta ให้ออกมาอยู่ชั้นนอกสุด
            "author_name": author.get("name", ""),
            "followers": author.get("fans", 0),
            "following": author.get("following", 0),
            
            # Engagement Metrics
            "playCount": v.get("playCount", 0),
            "diggCount": v.get("diggCount", 0),
            "shareCount": v.get("shareCount", 0),
            "collectCount": v.get("collectCount", 0),
            "commentCount": v.get("commentCount", 0),
            
            # ข้อมูลเสริมสำหรับ AI
            "isAd": v.get("isAd", False),
            "caption": v.get("text", ""),
            
            # 3. Join คอมเมนต์เข้าวิดีโอ
            "comments": comments_by_url.get(url, [])
        }
        merged_data.append(merged_video)

    # 4. บันทึกไฟล์
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        json.dump(merged_data, out, ensure_ascii=False, indent=2)
        
    print(f"✅ ประกอบร่างเสร็จสิ้น! ได้ข้อมูล {len(merged_data)} คลิป พร้อมคอมเมนต์")
    print(f"💾 บันทึกไฟล์ที่: {OUTPUT_FILE}")
    print("🚀 สเตปต่อไป: ทำ Pipeline วิเคราะห์อารมณ์ด้วย sentiment_analyzer.py")

if __name__ == "__main__":
    merge_data()