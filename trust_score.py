import json
import config

INPUT_FILE = config.ANALYZED_VIDEOS_FILE
OUTPUT_FILE = config.SCORED_VIDEOS_FILE

def calculate_scores():
    print(f"🧮 กำลังเริ่มคำนวณ ROI Score (ระดับ Influencer) จากไฟล์: {INPUT_FILE}")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    except FileNotFoundError:
        print(f"❌ หาไฟล์ {INPUT_FILE} ไม่พบ กรุณารัน sentiment_analyzer.py ก่อน")
        return

    # 1. จัดกลุ่มข้อมูลวิดีโอตามชื่อ Influencer
    influencers_data = {}

    for v in videos:
        author = v.get("author_name", "Unknown")
        
        # ถ้าเพิ่งเจอช่องนี้ครั้งแรก ให้สร้างโปรไฟล์ตั้งต้น
        if author not in influencers_data:
            influencers_data[author] = {
                "author_name": author,
                "followers": v.get("followers", 0),
                "following": v.get("following", 0),
                "total_views": 0,
                "total_likes": 0,
                "total_shares": 0,
                "total_saves": 0,
                "total_comments": 0,
                "video_count": 0,
                "sum_pos_pct": 0,
                "sum_neg_pct": 0,
                "ad_count": 0, 
                "video_urls": []
            }
            
        # สะสมยอด Engagement ทุกคลิปของช่องนี้
        influencers_data[author]["total_views"] += v.get("playCount", 0)
        influencers_data[author]["total_likes"] += v.get("diggCount", 0)
        influencers_data[author]["total_shares"] += v.get("shareCount", 0)
        influencers_data[author]["total_saves"] += v.get("collectCount", 0)
        influencers_data[author]["total_comments"] += v.get("commentCount", 0)
        
        # สะสม Sentiment 
        sentiment = v.get("sentiment_summary", {})
        influencers_data[author]["sum_pos_pct"] += sentiment.get("positive_percent", 0)
        influencers_data[author]["sum_neg_pct"] += sentiment.get("negative_percent", 0)
        
        if v.get("isAd", False):
            influencers_data[author]["ad_count"] += 1
            
        influencers_data[author]["video_count"] += 1
        influencers_data[author]["video_urls"].append(v.get("webVideoUrl", ""))

    scored_data = []

    # 2. คำนวณคะแนนรวมเป็นรายบุคคล
    for author, data in influencers_data.items():
        views = data["total_views"]
        v_count = data["video_count"]
        
        # ก. หาค่าเฉลี่ย Engagement Rate รวมทุกคลิป
        if views > 0:
            er_percent = ((data["total_likes"] + data["total_shares"] + data["total_saves"] + data["total_comments"]) / views) * 100
        else:
            er_percent = 0
            
        # ข. หาค่าเฉลี่ย Sentiment รวมทุกคลิป
        avg_pos = data["sum_pos_pct"] / v_count if v_count > 0 else 0
        avg_neg = data["sum_neg_pct"] / v_count if v_count > 0 else 0
        
        # ค. คำนวณ Follower Ratio
        fans = data["followers"]
        following = data["following"]
        follow_ratio = fans / following if following > 0 else fans
        
        # --- สร้างสูตรคำนวณคะแนน (เต็ม 100) ---
        er_score = min((er_percent / 5.0) * 40, 40)
        sentiment_score = max(0, min(((avg_pos - (avg_neg * 0.5)) / 100) * 40, 40))
        
        if follow_ratio >= 10:   
            ratio_score = 20
        elif follow_ratio >= 2:  
            ratio_score = 10
        else:                    
            ratio_score = 5 
            
        # รวมเป็น ROI Score (เปลี่ยนชื่อตามมติในไฟล์เอกสาร)
        total_score = round(er_score + sentiment_score + ratio_score, 2)
        
        if total_score >= 80: grade = "A (แนะนำจ้าง)"
        elif total_score >= 60: grade = "B (พอใช้ได้)"
        elif total_score >= 40: grade = "C (มีความเสี่ยง)"
        else: grade = "D (ไม่แนะนำ)"
        
        # จัดรูปแบบ JSON ใหม่ให้ Dashboard
        scored_data.append({
            "author_name": author,
            "followers": fans,
            "analyzed_videos_count": v_count,
            "total_views": views,
            "ad_ratio": f"{data['ad_count']}/{v_count}", # สัดส่วนคลิปที่เป็นโฆษณา
            "metrics": {
                "avg_engagement_rate_percent": round(er_percent, 2),
                "follower_ratio": round(follow_ratio, 2),
                "avg_positive_sentiment": round(avg_pos, 2)
            },
            "evaluation": {
                "roi_score": total_score,
                "grade": grade,
                "score_breakdown": {
                    "engagement_40": round(er_score, 2),
                    "sentiment_40": round(sentiment_score, 2),
                    "channel_quality_20": round(ratio_score, 2)
                }
            },
            "sample_video_url": data["video_urls"][0] if data["video_urls"] else "#"
        })
        
    # บันทึกไฟล์ผลลัพธ์
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(scored_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ คำนวณคะแนนเสร็จสิ้น! ยุบรวมเหลือ Influencer ทั้งหมด {len(scored_data)} คน")
    print(f"💾 บันทึกผลลัพธ์ (Storage) ไว้ที่: {OUTPUT_FILE}")

if __name__ == "__main__":
    calculate_scores()