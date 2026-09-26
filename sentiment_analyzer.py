import json
import re
from pythainlp import word_tokenize
from pythainlp.corpus import thai_stopwords, thai_words
from transformers import pipeline
from text_cleaner import clean_thai_text

print("⏳ กำลังโหลด AI Model (SandboxBhh/sentiment-thai-text-model)...")
sentiment_analyzer = pipeline("text-classification", model="SandboxBhh/sentiment-thai-text-model")
stop_words = frozenset(thai_stopwords())
thai_dict = frozenset(thai_words())

def extract_unknown_words(text):
    """ฟังก์ชันสกัดคำศัพท์ใหม่ที่ AI อาจไม่รู้จัก เพื่อเก็บลง pending words"""
    cleaned = clean_thai_text(text)
    tokens = word_tokenize(cleaned, engine="newmm")
    return [w for w in tokens if w not in stop_words and w.strip() != "" and w not in thai_dict and not re.match(r'^[a-zA-Z0-9_]+$', w)]

def analyze_comments(caption, comments_list, confidence_threshold=0.6):
    """
    วิเคราะห์อารมณ์จากรายการคอมเมนต์ของ 1 คลิป 
    - รับค่า caption ของคลิปมาเป็นบริบทเสริม
    - มี Threshold กรองความมั่นใจ ถ้าต่ำกว่าเกณฑ์ให้เป็น Neutral
    - คืนค่า: สรุปภาพรวมอารมณ์ (Aggregate), ผลวิเคราะห์รายคอมเมนต์, และคำศัพท์ใหม่
    """
    analyzed_results = []
    pending_words = set()
    
    # ตัวแปรสำหรับคำนวณค่าเฉลี่ย/สัดส่วน
    total_valid_comments = 0
    pos_count = 0
    neg_count = 0
    neu_count = 0
    
    for comment in comments_list:
        comment_text = comment.get("text", "")
        if not comment_text.strip():
            continue
            
        # 1. ประกอบร่าง Context เพื่อลดความกำกวมของ AI
        contextual_text = f"บริบท: {caption} | คอมเมนต์: {comment_text}"
        
        # 2. วิเคราะห์อารมณ์ (จำกัดความยาวป้องกัน Error)
        ai_result = sentiment_analyzer(contextual_text, truncation=True, max_length=512)[0]
        label = ai_result['label'].lower()
        score = ai_result['score']
        
        # 3. เช็ก Confidence Threshold ป้องกัน AI มั่ว
        if score < confidence_threshold:
            status = "⚪ กลางๆ (Neutral - Low Confidence)"
            sentiment_value = "NEU"
        elif 'pos' in label:
            status = "🟢 เชิงบวก (Positive)"
            sentiment_value = "POS"
        elif 'neg' in label:
            status = "🔴 เชิงลบ (Negative)"
            sentiment_value = "NEG"
        else:
            status = "⚪ กลางๆ (Neutral)"
            sentiment_value = "NEU"
            
        # นับสถิติภาพรวม
        total_valid_comments += 1
        if sentiment_value == "POS": pos_count += 1
        elif sentiment_value == "NEG": neg_count += 1
        else: neu_count += 1
            
        # 4. สกัดคำศัพท์ใหม่
        unknowns = extract_unknown_words(comment_text)
        pending_words.update(unknowns)
        
        # เก็บผลลัพธ์ของแต่ละคอมเมนต์
        analyzed_results.append({
            "original_text": comment_text,
            "sentiment_status": status,
            "sentiment_value": sentiment_value,
            "ai_score": score,
            "likes": comment.get("likes", 0) 
        })
        
    # 5. สรุปผลภาพรวม (Aggregate) สำหรับส่งให้ระบบคิด Trust Score
    summary = {
        "total_analyzed": total_valid_comments,
        "positive_percent": (pos_count / total_valid_comments * 100) if total_valid_comments > 0 else 0,
        "negative_percent": (neg_count / total_valid_comments * 100) if total_valid_comments > 0 else 0,
        "neutral_percent": (neu_count / total_valid_comments * 100) if total_valid_comments > 0 else 0,
    }
        
    return summary, analyzed_results, list(pending_words)


def run_sentiment_pipeline():
    INPUT_FILE = "data/merged_ready.json"
    OUTPUT_FILE = "data/analyzed_videos.json"
    PENDING_WORDS_FILE = "data/pending_words.json"
    
    print(f"\n🚀 เริ่มต้นรัน Sentiment Pipeline กับข้อมูล: {INPUT_FILE}")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    except FileNotFoundError:
        print(f"❌ หาไฟล์ {INPUT_FILE} ไม่พบ กรุณารัน data_merger.py ก่อน")
        return

    all_pending_words = set()
    
    # โหลด pending words เก่า (ถ้ามี) จะได้ไม่เก็บคำซ้ำ
    try:
        with open(PENDING_WORDS_FILE, 'r', encoding='utf-8') as f:
            old_words = json.load(f)
            all_pending_words.update(old_words)
    except FileNotFoundError:
        pass

    # วนลูปวิเคราะห์ทีละคลิป
    for i, video in enumerate(videos):
        caption = video.get("caption", "")
        comments = video.get("comments", [])
        
        print(f"กำลังวิเคราะห์คลิปที่ {i+1}/{len(videos)}: {video.get('author_name')} ({len(comments)} คอมเมนต์)")
        
        # ส่งเข้าฟังก์ชันวิเคราะห์อารมณ์
        summary, analyzed_comments, new_words = analyze_comments(caption, comments)
        
        # นำผลลัพธ์เสียบกลับเข้าไปในข้อมูลวิดีโอ
        video["sentiment_summary"] = summary
        video["comments_analyzed"] = analyzed_comments
        
        # อัปเดตคำศัพท์ใหม่
        all_pending_words.update(new_words)

    # บันทึกไฟล์ผลลัพธ์
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
        
    with open(PENDING_WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(all_pending_words), f, ensure_ascii=False, indent=2)

    print("\n✅ รัน Sentiment Pipeline เสร็จสมบูรณ์!")
    print(f"💾 ข้อมูลพร้อมใช้ถูกบันทึกไว้ที่: {OUTPUT_FILE}")
    print(f"📚 พบคำศัพท์ใหม่ที่ AI ไม่รู้จักรวม: {len(all_pending_words)} คำ (บันทึกใน {PENDING_WORDS_FILE})")
    print("🎉 ยินดีด้วยครับ ภารกิจ Day 1 เสร็จสิ้นตามเป้าหมายแล้ว!")

if __name__ == "__main__":
    run_sentiment_pipeline()