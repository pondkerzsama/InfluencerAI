import json
import re
from pythainlp import word_tokenize
from pythainlp.corpus import thai_stopwords, thai_words
from transformers import pipeline

# 🔗 ดึงฟังก์ชันทำความสะอาดข้อความมาจากไฟล์ text_cleaner.py ของเรา
from text_cleaner import clean_thai_text

print("⏳ กำลังโหลด AI Model (รันครั้งแรกจะใช้เวลาดาวน์โหลดสักครู่)...")
# โหลดโมเดลวิเคราะห์อารมณ์ภาษาไทย
sentiment_analyzer = pipeline("text-classification", model="SandboxBhh/sentiment-thai-text-model")

# โหลดข้อมูลคำไทยพื้นฐาน
stop_words = frozenset(thai_stopwords())
thai_dict = frozenset(thai_words())

def extract_unknown_words(text):
    """ฟังก์ชันดึงคำที่น่าสงสัย (ไม่มีในพจนานุกรมและไม่ใช่ภาษาอังกฤษ/ตัวเลข)"""
    # 🧹 เรียกใช้ฟังก์ชันจาก text_cleaner.py
    cleaned = clean_thai_text(text)
    tokens = word_tokenize(cleaned, engine="newmm")
    
    suspicious = []
    for word in tokens:
        if word in stop_words or word.strip() == "":
            continue
        if word not in thai_dict and not re.match(r'^[a-zA-Z0-9_]+$', word):
            suspicious.append(word)
    return suspicious

if __name__ == "__main__":
    print("กำลังเตรียมข้อมูลจาก data/dummy_data.json...\n")
    all_pending_words = set() 
    
    try:
        with open("data/dummy_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            
        for video in data:
            print(f"=== 🔍 กำลังวิเคราะห์คลิปของ: {video['influencer_name']} ===")
            
            for comment in video["comments"]:
                original = comment["text"]
                
                # 1. ให้ AI วิเคราะห์อารมณ์รวมของประโยค
                ai_result = sentiment_analyzer(original)[0]
                label = ai_result['label'].lower()
                
                if 'pos' in label:
                    status = "🟢 เชิงบวก (Positive)"
                elif 'neg' in label:
                    status = "🔴 เชิงลบ (Negative)"
                else:
                    status = "⚪ กลางๆ (Neutral)"
                    
                # 2. คัดแยกคำศัพท์ใหม่
                unknown_words = extract_unknown_words(original)
                all_pending_words.update(unknown_words)
                
                print(f"💬 {original}")
                print(f"   -> AI ประเมิน: {status} (ความมั่นใจ: {ai_result['score']:.2f})")
                
                if unknown_words:
                    print(f"   -> ❓ คำที่น่าสงสัย: {unknown_words}")
                
            print("-" * 50)
            
        # 3. บันทึกคำสงสัยแบบไม่ซ้ำลงไฟล์
        pending_list = list(all_pending_words)
        with open("data/pending_words.json", "w", encoding="utf-8") as out_file:
            json.dump(pending_list, out_file, ensure_ascii=False, indent=4)
            
        print(f"\n✅ บันทึกคำที่ต้องตรวจทานจำนวน {len(pending_list)} คำ ลงใน data/pending_words.json เรียบร้อยแล้ว")
            
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ data/dummy_data.json ครับ")