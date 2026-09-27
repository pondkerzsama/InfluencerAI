# ไฟล์ศูนย์รวม Path - เมื่อได้ Dataset ใหม่ ให้แก้แค่ส่วนที่ 1

# 1. ไฟล์ต้นฉบับ (เปลี่ยนตรงนี้เมื่อได้ชุดข้อมูลใหม่มา)
RAW_VIDEO_FILE = "dataset/data-set-3-influ-with-comment-1.json"
RAW_COMMENT_FILE = "data/comment2.json"

# 2. ไฟล์ที่เกิดจาก Pipeline (ปกติไม่ต้องแก้ ปล่อยให้ระบบสร้างเอง)
VALID_VIDEOS_FILE = "data/valid_videos.json"
MERGED_READY_FILE = "data/merged_ready.json"
ANALYZED_VIDEOS_FILE = "data/analyzed_videos.json"
SCORED_VIDEOS_FILE = "data/scored_videos.json"
PENDING_WORDS_FILE = "data/pending_words.json"