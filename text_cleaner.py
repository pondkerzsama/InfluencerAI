import json
import re
from pythainlp import word_tokenize
from pythainlp.util import normalize

def clean_thai_text(text):
    if not text:
        return ""

    # 1. จัดการสระซ้อน เคลียร์เว้นวรรคผิดปกติด้วย PyThaiNLP
    text = normalize(text)

    # 2. ลดตัวอักษรที่เบิ้ลเกินความจำเป็น (เช่น โลกกกก -> โลก)
    # ลอจิก: ถ้าเจอตัวอักษรซ้ำกันตั้งแต่ 3 ตัวขึ้นไป ให้ย่อเหลือตัวเดียว
    text = re.sub(r'(.)\1{2,}', r'\1', text)

    # 3. ลบอีโมจิและเครื่องหมายแปลกๆ (เก็บไว้เฉพาะ ก-๙, a-z, A-Z, 0-9 และช่องว่าง)
    text = re.sub(r'[^\w\sก-๙]', ' ', text)

    # 4. ลบช่องว่างที่ซ้ำซ้อนให้เหลือเคาะเดียว
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# ทดสอบรันดึงข้อมูลจาก Mock Data
if __name__ == "__main__":
    print("กำลังโหลดข้อมูลจาก data/dummy_data.json...\n")
    
    try:
        with open("data/dummy_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            
        # ลองดึงข้อมูลคอมเมนต์ของคลิปแรกมาเทสต์
        first_video = data[0]
        print(f"=== ผลการทำความสะอาดคอมเมนต์ของ Influencer: {first_video['influencer_name']} ===\n")
        
        for comment in first_video["comments"]:
            original = comment["text"]
            cleaned = clean_thai_text(original)
            
            # ตัดคำด้วยเอนจิน newmm (แม่นยำที่สุดของ PyThaiNLP)
            tokens = word_tokenize(cleaned, engine="newmm")
            
            print(f"🔴 ก่อนคลีน: {original}")
            print(f"🟢 หลังคลีน: {cleaned}")
            print(f"✂️  ตัดคำ:   {tokens}\n")
            print("-" * 50)
            
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ data/dummy_data.json ครับ รบกวนเช็กโฟลเดอร์อีกทีนะ")