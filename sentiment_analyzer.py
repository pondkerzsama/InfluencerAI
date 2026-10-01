import json
import re
import config
from pythainlp import word_tokenize
from pythainlp.corpus import thai_stopwords, thai_words
from transformers import pipeline
from text_cleaner import clean_thai_text

print("⏳ กำลังโหลด AI Model (SandboxBhh/sentiment-thai-text-model)...")
sentiment_analyzer = pipeline("text-classification", model="SandboxBhh/sentiment-thai-text-model", top_k=None)
stop_words = frozenset(thai_stopwords())
thai_dict = frozenset(thai_words())

def extract_unknown_words(text):
    cleaned = clean_thai_text(text)
    tokens = word_tokenize(cleaned, engine="newmm")
    return [w for w in tokens if w not in stop_words and w.strip() != "" and w not in thai_dict and not re.match(r'^[a-zA-Z0-9_]+$', w)]

def analyze_comments(caption, comments_list, confidence_threshold=0.6):
    analyzed_results = []
    pending_words = set()

    total_valid_comments = 0
    pos_count = 0
    neg_count = 0
    neu_count = 0
    
    positive_keywords = ["คุ้ม", "เสียงดี", "ลดเสียง", "ชัด", "ทน", "ชอบ", "ดีมาก", "เยี่ยม"]

    for comment in comments_list:
        comment_text = comment.get("text", "")
        if not comment_text.strip():
            continue

        cleaned_comment = clean_thai_text(comment_text)
        has_positive_keyword = any(keyword in cleaned_comment for keyword in positive_keywords)
        
        # ค่าเริ่มต้นสำหรับ Prob
        prob_pos = 0.0
        prob_neg = 0.0

        if has_positive_keyword:
            score = 0.99
            label = "pos"
            prob_pos = 0.99
            prob_neg = 0.01
            analysis_source = "rule_based_keyword"
        else:
            raw_comment_results = sentiment_analyzer(cleaned_comment, truncation=True, max_length=512)[0]
            best_class = max(raw_comment_results, key=lambda x: x['score'])
            best_score = best_class['score']
            active_results = raw_comment_results
            analysis_source = "comment_only"

            if best_score < confidence_threshold and caption.strip() != "":
                contextual_text = f"{caption} {cleaned_comment}"
                raw_context_results = sentiment_analyzer(contextual_text, truncation=True, max_length=512)[0]
                best_class_context = max(raw_context_results, key=lambda x: x['score'])

                if best_class_context['score'] > best_score:
                    best_class = best_class_context
                    best_score = best_class_context['score']
                    active_results = raw_context_results
                    analysis_source = "with_context"

            label = best_class['label'].lower()
            score = best_score
            
            # สกัดค่า P(POS) และ P(NEG) ออกมาส่งให้ Trust Score
            for item in active_results:
                lbl = item['label'].lower()
                if 'pos' in lbl: prob_pos = item['score']
                elif 'neg' in lbl: prob_neg = item['score']

        if score < confidence_threshold and analysis_source != "rule_based_keyword":
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

        total_valid_comments += 1
        if sentiment_value == "POS": pos_count += 1
        elif sentiment_value == "NEG": neg_count += 1
        else: neu_count += 1

        unknowns = extract_unknown_words(comment_text)
        pending_words.update(unknowns)

        analyzed_results.append({
            "original_text": comment_text,
            "sentiment_status": status,
            "sentiment_value": sentiment_value,
            "ai_score": score,
            "prob_pos": prob_pos, 
            "prob_neg": prob_neg,
            "analysis_source": analysis_source,
            "likes": comment.get("likes", 0)
        })

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

if __name__ == "__main__":
    run_sentiment_pipeline()