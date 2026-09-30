import json
import config

INPUT_FILE = config.ANALYZED_VIDEOS_FILE
OUTPUT_FILE = config.SCORED_VIDEOS_FILE

def calculate_percentile(value, data_list):
    """ฟังก์ชันคำนวณตำแหน่ง Percentile (0.0 - 1.0) ของค่า ER เมื่อเทียบกับคลิปทั้งหมด"""
    if not data_list:
        return 0.0
    less_than = sum(1 for x in data_list if x < value)
    equal_to = sum(1 for x in data_list if x == value)
    return (less_than + (0.5 * equal_to)) / len(data_list)

def calculate_scores():
    print(f"🧮 กำลังเริ่มคำนวณ ROI Score แบบใหม่ (Percentile & Prob-Sentiment) จากไฟล์: {INPUT_FILE}")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    except FileNotFoundError:
        print(f"❌ หาไฟล์ {INPUT_FILE} ไม่พบ กรุณารัน sentiment_analyzer.py ก่อน")
        return

    # 1. คำนวณ ER ต่อคลิป และเก็บค่า ER ทั้งหมดเพื่อใช้สร้าง Curve (Percentile)
    all_ers = []
    for v in videos:
        views = v.get("playCount", 0)
        if views > 0:
            er = ((v.get("diggCount", 0) + v.get("shareCount", 0) + v.get("collectCount", 0) + v.get("commentCount", 0)) / views) * 100
        else:
            er = 0
        v["_temp_er"] = er
        all_ers.append(er)

    # 2. จัดกลุ่มและคำนวณคะแนนระดับคลิปก่อนยุบรวม
    influencers_data = {}
    for v in videos:
        author = v.get("author_name", "Unknown")
        er_percent = v["_temp_er"]
        
        # --- ก. แปลง ER ของคลิปนี้เป็น Percentile Rank และคิดเป็นคะแนนเต็ม 40 ---
        percentile_rank = calculate_percentile(er_percent, all_ers)
        engagement_score_video = percentile_rank * 40
        
        if author not in influencers_data:
            influencers_data[author] = {
                "author_name": author,
                "followers": v.get("followers", 0),
                "following": v.get("following", 0),
                "total_views": 0,
                "ad_count": 0, 
                "video_urls": [],
                "video_er_scores": [], # เก็บคะแนน ER ของแต่ละคลิป
                "comment_Si_list": []  # เก็บค่า S_i ของทุกคอมเมนต์
            }
            
        influencers_data[author]["total_views"] += v.get("playCount", 0)
        if v.get("isAd", False): influencers_data[author]["ad_count"] += 1
        influencers_data[author]["video_urls"].append(v.get("webVideoUrl", ""))
        influencers_data[author]["video_er_scores"].append(engagement_score_video)
        
        # --- ข. ประมวลผลคะแนน Sentiment แต่ละคอมเมนต์ด้วยสมการ Si = prob_pos - prob_neg ---
        for comment in v.get("comments_analyzed", []):
            prob_pos = comment.get("prob_pos", 0)
            prob_neg = comment.get("prob_neg", 0)
            Si = prob_pos - prob_neg
            influencers_data[author]["comment_Si_list"].append(Si)

    scored_data = []

    # 3. คำนวณคะแนนรวมระดับ Influencer
    for author, data in influencers_data.items():
        v_count = len(data["video_er_scores"])
        
        # ก. เฉลี่ยคะแนน Engagement ของทุกคลิป
        avg_er_score = sum(data["video_er_scores"]) / v_count if v_count > 0 else 0
        
        # ข. หาค่าเฉลี่ย Sentiment รวม (S_bar) แล้วเข้าสมการ
        if data["comment_Si_list"]:
            S_bar = sum(data["comment_Si_list"]) / len(data["comment_Si_list"])
        else:
            S_bar = 0
        sentiment_score = ((S_bar + 1) / 2) * 40
        
        # ค. คำนวณ Follower Ratio (คะแนนคุณภาพช่อง คงเดิม)
        fans = data["followers"]
        following = data["following"]
        follow_ratio = fans / following if following > 0 else fans
        
        if follow_ratio >= 10:   
            ratio_score = 20
        elif follow_ratio >= 2:  
            ratio_score = 10
        else:                    
            ratio_score = 5 
            
        # รวมเป็น ROI Score
        total_score = round(avg_er_score + sentiment_score + ratio_score, 2)
        
        if total_score >= 80: grade = "A (แนะนำจ้าง)"
        elif total_score >= 60: grade = "B (พอใช้ได้)"
        elif total_score >= 40: grade = "C (มีความเสี่ยง)"
        else: grade = "D (ไม่แนะนำ)"
        
        scored_data.append({
            "author_name": author,
            "followers": fans,
            "analyzed_videos_count": v_count,
            "total_views": data["total_views"],
            "ad_ratio": f"{data['ad_count']}/{v_count}",
            "metrics": {
                "avg_percentile_engagement_score": round(avg_er_score, 2),
                "follower_ratio": round(follow_ratio, 2),
                "sentiment_S_bar": round(S_bar, 4)
            },
            "evaluation": {
                "roi_score": total_score,
                "grade": grade,
                "score_breakdown": {
                    "engagement_40": round(avg_er_score, 2),
                    "sentiment_40": round(sentiment_score, 2),
                    "channel_quality_20": round(ratio_score, 2)
                }
            },
            "sample_video_url": data["video_urls"][0] if data["video_urls"] else "#"
        })
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(scored_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ คำนวณคะแนนเสร็จสิ้น! ยุบรวมเหลือ Influencer ทั้งหมด {len(scored_data)} คน")
    print(f"💾 บันทึกผลลัพธ์ (Storage) ไว้ที่: {OUTPUT_FILE}")

if __name__ == "__main__":
    calculate_scores()