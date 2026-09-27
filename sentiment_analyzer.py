import json
import re
import config
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
    วิเคราะห์อารมณ์จากรายการคอมเมนต์ (แบบ Comment-first)
    - วิเคราะห์คอมเมนต์เดี่ยวก่อน
    - ถ้าระดับความมั่นใจต่ำกว่า threshold ค่อยดึง caption มาเป็นบริบทเสริม "ลองดู"
    - เทียบ confidence ของทั้ง 2 รอบ แล้วเลือกรอบที่ AI มั่นใจกว่าจริง
      (ไม่ override ทิ้งตายตัว เพราะพบจากข้อมูลจริงว่า with_context บางครั้ง
      ทำให้คอมเมนต์สั้นๆ ที่ควรเป็นบวกชัดเจน เช่น "เสียงดีค่า" กลายเป็นลบ/กลางไปเลย)
    """
    analyzed_results = []
    pending_words = set()

    total_valid_comments = 0
    pos_count = 0
    neg_count = 0
    neu_count = 0

    for comment in comments_list:
        comment_text = comment.get("text", "")
        if not comment_text.strip():
            continue

        # 1. วิเคราะห์รอบแรก: ใช้เฉพาะข้อความคอมเมนต์
        comment_only_result = sentiment_analyzer(comment_text, truncation=True, max_length=512)[0]
        best_result = comment_only_result
        best_score = comment_only_result['score']
        analysis_source = "comment_only"

        # 2. ถ้ารอบแรก AI ไม่มั่นใจ และมีแคปชัน ให้ลองวิเคราะห์รอบสองโดยเสริมบริบทเข้าไปดู
        if best_score < confidence_threshold and caption.strip() != "":
            contextual_text = f"{caption} {comment_text}"
            context_result = sentiment_analyzer(contextual_text, truncation=True, max_length=512)[0]

            # 3. เทียบ confidence ทั้ง 2 รอบ แล้วเลือกรอบที่มั่นใจกว่าจริง
            #    ไม่ใช่ยึดรอบ context เป็นคำตอบสุดท้ายเสมอไป
            if context_result['score'] > best_score:
                best_result = context_result
                best_score = context_result['score']
                analysis_source = "with_context"
            # ถ้า context ไม่ได้ช่วยให้มั่นใจขึ้นจริง ก็ยังคงใช้ comment_only ต่อไป
            # (analysis_source ยังเป็น "comment_only" เหมือนเดิม)

        label = best_result['label'].lower()
        score = best_score

        # 4. ตัดสินผลลัพธ์อารมณ์สุดท้าย (ถ้าลองทุกทางแล้วยังต่ำกว่าเกณฑ์ ก็ให้เป็นกลาง)
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

        # 5. สกัดคำศัพท์ใหม่ (ใช้แค่ comment_text เพียวๆ เสมอ)
        unknowns = extract_unknown_words(comment_text)
        pending_words.update(unknowns)

        # เก็บผลลัพธ์ของแต่ละคอมเมนต์
        analyzed_results.append({
            "original_text": comment_text,
            "sentiment_status": status,
            "sentiment_value": sentiment_value,
            "ai_score": score,
            "analysis_source": analysis_source,
            "likes": comment.get("likes", 0)
        })

    # 6. สรุปผลภาพรวม
    summary = {
        "total_analyzed": total_valid_comments,
        "positive_percent": (pos_count / total_valid_comments * 100) if total_valid_comments > 0 else 0,
        "negative_percent": (neg_count / total_valid_comments * 100) if total_valid_comments > 0 else 0,
        "neutral_percent": (neu_count / total_valid_comments * 100) if total_valid_comments > 0 else 0,
    }

    return summary, analyzed_results, list(pending_words)


def run_sentiment_pipeline():
    INPUT_FILE = config.MERGED_READY_FILE
    OUTPUT_FILE = config.ANALYZED_VIDEOS_FILE
    PENDING_WORDS_FILE = config.PENDING_WORDS_FILE

    print(f"\n🚀 เริ่มต้นรัน Sentiment Pipeline กับข้อมูล: {INPUT_FILE}")

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    except FileNotFoundError:
        print(f"❌ หาไฟล์ {INPUT_FILE} ไม่พบ กรุณารัน data_merger.py ก่อน")
        return

    all_pending_words = set()

    try:
        with open(PENDING_WORDS_FILE, 'r', encoding='utf-8') as f:
            old_words = json.load(f)
            all_pending_words.update(old_words)
    except FileNotFoundError:
        pass

    for i, video in enumerate(videos):
        caption = video.get("caption", "")
        comments = video.get("comments", [])

        print(f"กำลังวิเคราะห์คลิปที่ {i+1}/{len(videos)}: {video.get('author_name')} ({len(comments)} คอมเมนต์)")

        summary, analyzed_comments, new_words = analyze_comments(caption, comments)

        video["sentiment_summary"] = summary
        video["comments_analyzed"] = analyzed_comments

        all_pending_words.update(new_words)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    with open(PENDING_WORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(all_pending_words), f, ensure_ascii=False, indent=2)

    print("\n✅ รัน Sentiment Pipeline เสร็จสมบูรณ์!")
    print(f"💾 ข้อมูลพร้อมใช้ถูกบันทึกไว้ที่: {OUTPUT_FILE}")
    print(f"📚 พบคำศัพท์ใหม่ที่ AI ไม่รู้จักรวม: {len(all_pending_words)} คำ (บันทึกใน {PENDING_WORDS_FILE})")

if __name__ == "__main__":
    run_sentiment_pipeline()