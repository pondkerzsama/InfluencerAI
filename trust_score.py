import json

INPUT_FILE = "data/analyzed_videos.json"
OUTPUT_FILE = "data/scored_videos.json" # ทำหน้าที่เป็น Lightweight Storage สำหรับ Day 2

def calculate_scores():
    print(f"🧮 กำลังเริ่มคำนวณ Trust & ROI Score จากไฟล์: {INPUT_FILE}")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    except FileNotFoundError:
        print(f"❌ หาไฟล์ {INPUT_FILE} ไม่พบ กรุณารัน sentiment_analyzer.py ก่อน")
        return

    scored_data = []

    for v in videos:
        # 1. คำนวณ Engagement Rate (ER)
        views = v.get("playCount", 0)
        likes = v.get("diggCount", 0)
        shares = v.get("shareCount", 0)
        saves = v.get("collectCount", 0)
        comments_count = v.get("commentCount", 0)
        
        if views > 0:
            er_percent = ((likes + shares + saves + comments_count) / views) * 100
        else:
            er_percent = 0
            
        # 2. คำนวณ Follower Ratio (เช็กสัดส่วนการแลกฟอล)
        fans = v.get("followers", 0)
        following = v.get("following", 0)
        
        if following > 0:
            follow_ratio = fans / following
        else:
            follow_ratio = fans # ถ้าไม่ฟอลใครเลย ถือว่าสัดส่วนดีมาก
            
        # 3. ดึงค่า Sentiment ที่ AI วิเคราะห์ไว้
        sentiment = v.get("sentiment_summary", {})
        pos_pct = sentiment.get("positive_percent", 0)
        neg_pct = sentiment.get("negative_percent", 0)
        
        # --- สร้างสูตรคำนวณคะแนน (เต็ม 100) ---
        
        # ก. คะแนน Engagement (เต็ม 40) - สมมติว่า ER 10% ขึ้นไปคือคลิปปัง (ได้คะแนนเต็ม)
        er_score = min((er_percent / 10.0) * 40, 40)
        
        # ข. คะแนน Sentiment (เต็ม 40) - ให้คะแนนตาม % เชิงบวก และหักคะแนนถ้ามี % เชิงลบเยอะ
        sentiment_score = max(0, min(((pos_pct - (neg_pct * 0.5)) / 100) * 40, 40))
        
        # ค. คะแนนความน่าเชื่อถือช่อง (เต็ม 20) - อิงจาก Follower Ratio
        if follow_ratio >= 10:   # ฟอลเยอะกว่าคนดูกำลังติดตาม 10 เท่าขึ้นไป
            ratio_score = 20
        elif follow_ratio >= 2:  # สัดส่วนปกติ
            ratio_score = 10
        else:                    # สัดส่วน 1:1 หรือน้อยกว่า (เสี่ยงปั๊มฟอล/แลกฟอล)
            ratio_score = 5 
            
        # รวมคะแนน Trust Score
        total_score = round(er_score + sentiment_score + ratio_score, 2)
        
        # จัดเกรดง่ายๆ สำหรับนำเสนอ
        if total_score >= 80: grade = "A (แนะนำจ้าง)"
        elif total_score >= 60: grade = "B (พอใช้ได้)"
        elif total_score >= 40: grade = "C (มีความเสี่ยง)"
        else: grade = "D (ไม่แนะนำ)"
        
        # สร้างชุดข้อมูลผลลัพธ์ (เพิ่ม metrics และ evaluation เข้าไป)
        v["metrics"] = {
            "engagement_rate_percent": round(er_percent, 2),
            "follower_ratio": round(follow_ratio, 2)
        }
        v["evaluation"] = {
            "trust_score": total_score,
            "grade": grade,
            "isAd": v.get("isAd", False), # แปะป้ายว่าเป็นโฆษณาหรือไม่
            "score_breakdown": {
                "engagement_40": round(er_score, 2),
                "sentiment_40": round(sentiment_score, 2),
                "channel_quality_20": round(ratio_score, 2)
            }
        }
        scored_data.append(v)
        
    # บันทึกไฟล์ผลลัพธ์
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(scored_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ คำนวณคะแนนเสร็จสิ้นสำหรับ {len(scored_data)} คลิป!")
    print(f"💾 บันทึกผลลัพธ์ (Storage) ไว้ที่: {OUTPUT_FILE}")
    print("🚀 สเตปต่อไป (Day 3): สร้าง API เสิร์ฟข้อมูลไปที่หน้าเว็บ Dashboard")

if __name__ == "__main__":
    calculate_scores()