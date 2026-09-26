from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="Influencer Trust Score API")

# เปิดทางให้หน้าเว็บ HTML ของเรา (Frontend) สามารถดึงข้อมูลข้ามโดเมนได้ (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ดึงข้อมูลจาก Lightweight Storage ที่เราทำไว้ใน Day 2
STORAGE_FILE = "data/scored_videos.json"

@app.get("/api/scores")
def get_trust_scores():
    """
    Endpoint สำหรับดึงข้อมูลคะแนน Trust Score ของทุกคลิป
    """
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
            
        # สร้างชุดข้อมูลสรุปภาพรวม (Summary) เพื่อให้ Dashboard เอาไปวาดกราฟง่ายๆ
        total_videos = len(videos)
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
        
        for v in videos:
            grade = v.get("evaluation", {}).get("grade", "")
            if "A" in grade: grade_counts["A"] += 1
            elif "B" in grade: grade_counts["B"] += 1
            elif "C" in grade: grade_counts["C"] += 1
            elif "D" in grade: grade_counts["D"] += 1

        return {
            "status": "success",
            "summary": {
                "total_videos_analyzed": total_videos,
                "grade_distribution": grade_counts
            },
            "data": videos
        }
        
    except FileNotFoundError:
        return {"status": "error", "message": "ไม่พบไฟล์ข้อมูล กรุณารัน trust_score.py ก่อน"}