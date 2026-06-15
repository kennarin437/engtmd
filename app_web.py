import sqlite3
import streamlit as st

# ตั้งค่าหน้าเว็บให้แสดงผลแบบกว้าง (Wide Mode)
st.set_page_config(page_title="MD Smart Classroom Web App", layout="wide", page_icon="🏫")

# --- ฟังก์ชันจัดการฐานข้อมูล (SQLite) ---
def init_db():
    conn = sqlite3.connect("classroom_web.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
        (nfc_uid TEXT PRIMARY KEY, student_id TEXT, name TEXT, points INTEGER DEFAULT 0, level TEXT DEFAULT 'Beginner 🌱')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS assignments 
        (assignment_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, max_points INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS student_assignments 
        (nfc_uid TEXT, assignment_id INTEGER, status TEXT DEFAULT 'ยังไม่ส่ง', PRIMARY KEY(nfc_uid, assignment_id))''')
    
    # เพิ่มข้อมูลงานตัวอย่างถ้ายังไม่มี
    cursor.execute("SELECT COUNT(*) FROM assignments")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO assignments (title, max_points) VALUES ('ใบงานที่ 1: การคัดแยกขยะ', 10)")
        cursor.execute("INSERT INTO assignments (title, max_points) VALUES ('Project: MD Green Rangers', 20)")
        conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

def calculate_level(points):
    if points >= 30: return "Master 🏆"
    elif points >= 15: return "Explorer 🌟"
    return "Beginner 🌱"

# --- ส่วนติดต่อผู้ใช้บนหน้าเว็บ (UI) ---
st.title("🏫 ระบบจัดการห้องเรียนอัจฉริยะด้วย NFC (Web App)")
st.write("ยินดีต้อนรับสู่ระบบยกระดับการเรียนรู้ด้วยรูปแบบเกม (Gamification)")

# สร้างเมนูแท็บด้านบนของหน้าเว็บ
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 เช็กชื่อ & รับแต้มพฤติกรรม", 
    "📝 ส่งงาน & ตรวจงานค้าง", 
    "➕ ลงทะเบียนบัตรใหม่",
    "📊 แดชบอร์ดคะแนนรวมรวม"
])

# ==================== TAB 1: เช็กชื่อ & รับแต้มพฤติกรรม ====================
with tab1:
    st.header("โหมดแตะรับแต้มด่วน")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        action = st.selectbox("เลือกกิจกรรมเพื่อมอบคะแนน:", [
            "เช็กชื่อเข้าเรียน (+2 แต้ม)", 
            "ตอบคำถามถูกต้อง (+5 แต้ม)", 
            "ช่วยงานสิ่งแวดล้อม/ทิ้งขยะถูกประเภท (+5 แต้ม)"
        ])
        
        # ช่องรับรหัสจากเครื่องสแกน NFC
        uid_input = st.text_input("สแกนการ์ด / แตะบัตร NFC ตรงนี้", key="point_uid", placeholder="คลิกที่นี่แล้วแตะบัตร...")
        
    with col2:
        if uid_input:
            cursor.execute("SELECT name, points, level FROM students WHERE nfc_uid = ?", (uid_input.strip(),))
            student = cursor.fetchone()
            
            if student:
                name, current_points, old_level = student
                added_points = 2 if "เช็กชื่อ" in action else 5
                new_points = current_points + added_points
                new_level = calculate_level(new_points)
                
                # อัปเดตข้อมูล
                cursor.execute("UPDATE students SET points = ?, level = ? WHERE nfc_uid = ?", (new_points, new_level, uid_input.strip()))
                conn.commit()
                
                # แสดงผลเอฟเฟกต์สีสันบนหน้าเว็บ
                st.balloons() # แสดงเอฟเฟกต์ลูกโป่งลอยบนหน้าจอเพื่อความตื่นเต้นของเด็กๆ
                st.success(f"✨ บันทึกสำเร็จ! คุณ **{name}** ได้รับ {added_points} แต้ม จากกิจกรรม '{action}'")
                
                # ตรวจสอบเลเวลอัป
                if new_level != old_level:
                    st.toast(f"🎉 LEVEL UP! คุณ {name} เลเวลอัปเป็น {new_level} แล้ว!", icon="🔥")
                
                # แสดงผลการ์ดข้อมูลส่วนตัวย่อๆ
                st.metric(label="คะแนนรวมปัจจุบัน", value=f"{new_points} แต้ม", delta=f"+{added_points} แต้ม")
                st.info(f"ระดับปัจจุบัน: **{new_level}**")
            else:
                st.error("❌ ไม่พบข้อมูลบัตรนี้ในระบบ กรุณาลงทะเบียนก่อนครับ")

# ==================== TAB 2: ส่งงาน & ตรวจงานค้าง ====================
with tab2:
    st.header("โหมดส่งงานและแจ้งเตือนงานค้าง")
    
    col_w1, col_w2 = st.columns([1, 2])
    with col_w1:
        cursor.execute("SELECT title FROM assignments")
        jobs_list = [row[0] for row in cursor.fetchall()]
        selected_job = st.selectbox("เลือกชิ้นงานที่ต้องการบันทึกส่ง:", jobs_list)
        
        work_uid = st.text_input("นักเรียนแตะบัตรเพื่อส่งงาน/ตรวจสถานะ", key="work_uid", placeholder="คลิกที่นี่แล้วแตะบัตร...")
        
    with col_w2:
        if work_uid:
            cursor.execute("SELECT name, points, level FROM students WHERE nfc_uid = ?", (work_uid.strip(),))
            student = cursor.fetchone()
            
            if student:
                name, points, level = student
                
                # ดึงรหัสงาน
                cursor.execute("SELECT assignment_id FROM assignments WHERE title = ?", (selected_job,))
                assignment_id = cursor.fetchone()[0]
                
                # บันทึกสถานะส่งงาน
                cursor.execute("UPDATE student_assignments SET status = 'ส่งแล้ว' WHERE nfc_uid = ? AND assignment_id = ?", (work_uid.strip(), assignment_id))
                conn.commit()
                
                # ค้นหางานค้าง
                cursor.execute('''
                    SELECT assignments.title FROM student_assignments 
                    JOIN assignments ON student_assignments.assignment_id = assignments.assignment_id
                    WHERE student_assignments.nfc_uid = ? AND student_assignments.status = 'ยังไม่ส่ง'
                ''', (work_uid.strip(),))
                pending_jobs = cursor.fetchall()
                
                st.subheader(f"👤 ข้อมูลของ: {name}")
                st.write(f"ระดับ: **{level}** | แต้มสะสม: **{points} แต้ม**")
                st.success(f"✅ บันทึกการส่งงานสำเร็จ: ชิ้นงาน **[{selected_job}]**")
                
                st.markdown("---")
                st.markdown("### ⚠️ รายการงานค้างสะสม (Pending Assignments)")
                if pending_jobs:
                    for i, job in enumerate(pending_jobs, 1):
                        st.warning(f"{i}. {job[0]}")
                else:
                    st.success("🎉 ยอดเยี่ยมมาก! นักเรียนคนนี้ไม่มีงานค้างเลยครับ ครูปรบมือให้! 👏")
            else:
                st.error("❌ ไม่พบข้อมูลบัตรนี้ในระบบ")

# ==================== TAB 3: ลงทะเบียนบัตรใหม่ ====================
with tab3:
    st.header("ผูกบัตร NFC ใบใหม่เข้ากับข้อมูลนักเรียน")
    
    with st.form("reg_form", clear_on_submit=True):
        new_uid = st.text_input("รหัส UID ของบัตร NFC (คลิกช่องนี้แล้วเอาบัตรแตะเครื่องอ่าน)")
        new_sid = st.text_input("รหัสนักเรียน (เช่น 0045)")
        new_name = st.text_input("ชื่อ - นามสกุล นักเรียน")
        
        submitted = st.form_submit_button("บันทึกข้อมูลลงฐานข้อมูลระบบเว็บ")
        if submitted:
            if new_uid and new_sid and new_name:
                try:
                    cursor.execute("INSERT INTO students (nfc_uid, student_id, name) VALUES (?, ?, ?)", 
                                   (new_uid.strip(), new_sid.strip(), new_name.strip()))
                    
                    # ผูกงานค้างเริ่มต้นให้เด็กใหม่
                    cursor.execute("SELECT assignment_id FROM assignments")
                    for job in cursor.fetchall():
                        cursor.execute("INSERT OR IGNORE INTO student_assignments (nfc_uid, assignment_id, status) VALUES (?, ?, 'ยังไม่ส่ง')", (new_uid.strip(), job[0]))
                    
                    conn.commit()
                    st.success(f"🎉 ลงทะเบียนคุณ {new_name} สำเร็จเรียบร้อย!")
                except sqlite3.IntegrityError:
                    st.error("❌ ข้อผิดพลาด: รหัสการ์ดใบนี้หรือรหัสนักเรียนนี้มีอยู่ในระบบแล้ว")
            else:
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วนทุกช่อง")

# ==================== TAB 4: แดชบอร์ดคะแนนรวมรวม ====================
with tab4:
    st.header("📊 ตารางอันดับคะแนนพฤติกรรมในห้องเรียน (Leaderboard)")
    
    # ดึงข้อมูลมาแสดงตารางเรียงตามแต้มที่มากที่สุด
    cursor.execute("SELECT student_id AS 'รหัสนักเรียน', name AS 'ชื่อ-นามสกุล', points AS 'แต้มสะสม', level AS 'ระดับปัจจุบัน' FROM students ORDER BY points DESC")
    data = cursor.fetchall()
    
    if data:
        st.dataframe(data, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลนักเรียนในระบบในขณะนี้")