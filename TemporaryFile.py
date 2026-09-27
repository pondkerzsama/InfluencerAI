import json
import config

# ใช้ไฟล์ที่ผ่านการวิเคราะห์แล้วเป็นตัวตั้งต้น
INPUT_FILE = "data/analyzed_videos.json"
# บันทึกทับไฟล์เดิม หรือจะเปลี่ยนชื่อเป็นไฟล์ใหม่ก็ได้
OUTPUT_FILE = "data/analyzed_videos_test.json" 

def filter_only_scored_comments():
    print(f"🧹 กำลังกรองข้อมูล ลบคอมเมนต์ดิบออกจาก: {INPUT_FILE}")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
            
        for video in videos:
            # ตรวจสอบและลบ key 'comments' (ข้อมูลดิบที่ยังไม่มีคะแนน) ทิ้ง
            if "comments" in video:
                del video["comments"]
                
        # บันทึกไฟล์กลับเข้าไปใหม่
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
            
        print("✅ กรองข้อมูลสำเร็จ! ตอนนี้ใน JSON จะเหลือแค่ 'comments_analyzed' เท่านั้น")
        
    except FileNotFoundError:
        print(f"❌ หาไฟล์ {INPUT_FILE} ไม่พบครับ")

if __name__ == "__main__":
    filter_only_scored_comments()