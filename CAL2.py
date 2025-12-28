import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

st.set_page_config(page_title="Salary Calculator", layout="wide")

st.title("💰 โปรแกรมคำนวณเงินเดือน")

# --- ส่วนที่ 1: แถบด้านข้าง (Sidebar) สำหรับเลือกช่วงวันที่ ---
with st.sidebar:
    st.header("🗓️ เลือกช่วงวันที่ลงเวลา")
    # เลือกช่วงวันที่ (Start Date - End Date)
    today = datetime.now()
    date_range = st.date_input(
        "ตั้งแต่วันที่ - จนถึงวันที่",
        value=(today.replace(day=1), today), # ค่าเริ่มต้นคือวันที่ 1 ถึงวันนี้
        label_visibility="visible"
    )
    
    # ตรวจสอบว่าเลือกครบทั้งเริ่มและจบหรือยัง
    if len(date_range) == 2:
        start_date, end_date = date_range
        # คำนวณจำนวนวันจริงในช่วงที่เลือก
        num_days = (end_date - start_date).days + 1
        st.info(f"รวมระยะเวลา: {num_days} วัน")
    else:
        st.warning("กรุณาเลือกวันที่สิ้นสุดในปฏิทินด้วยครับ")
        st.stop()

# --- ส่วนที่ 2: ตั้งค่าค่าจ้าง ---
col_rate1, col_rate2 = st.columns(2)
with col_rate1:
    daily_rate = st.number_input("ค่าจ้างรายวัน (บาท)", min_value=0.0, value=362.0)
    hourly_rate = daily_rate / 8

ot_options = [0,2,8]

# --- 3. ส่วนแสดงตารางสะสม และ รวมยอดทั้งหมด ---
st.divider()
if not st.session_state.salary_db.empty:
    st.subheader("📋 รายการบันทึกทั้งหมดของเดือนนี้")

    # ฟังก์ชันสำหรับกำหนดสีพื้นหลัง (วันอาทิตย์ = สีเหลือง)
    def highlight_sunday(row):
        # ตรวจสอบชื่อวันจากคอลัมน์ "วันที่"
        # แปลง string วันที่กลับเป็น datetime object เพื่อเช็คว่าเป็นวันอาทิตย์หรือไม่
        date_obj = datetime.strptime(row["วันที่"], "%d/%m/%Y")
        if date_obj.weekday() == 6:  # 6 คือวันอาทิตย์
            return ['background-color: #FFFF00; color: black'] * len(row)
        return [''] * len(row)

    # นำตารางมาใส่สีไฮไลต์
    styled_df = st.session_state.salary_db.style.apply(highlight_sunday, axis=1)

    # แสดงตาราง (หมายเหตุ: st.data_editor ในปัจจุบันยังไม่รองรับการแสดงสีพร้อมแก้ไขแบบ Real-time เป๊ะๆ
    # แนะนำให้ใช้ st.dataframe แสดงผลที่มีสี และใช้ st.data_editor แยกหากต้องการแก้ข้อมูล)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # หากต้องการแก้ไขข้อมูล ให้กดปุ่มนี้เพื่อเปิดโหมดแก้ไข
    with st.expander("🛠 คลิกที่นี่เพื่อแก้ไขข้อมูลในตาราง"):
        edited_df = st.data_editor(st.session_state.salary_db, use_container_width=True, hide_index=True)
        
        # อัปเดต Logic การคำนวณใหม่เมื่อมีการแก้ (เหมือนที่เคยทำก่อนหน้า)
        if not edited_df.equals(st.session_state.salary_db):
            edited_df["เงินรายวัน"] = pd.to_numeric(edited_df["เงินรายวัน"], errors='coerce').fillna(0)
            edited_df["OT(ชม.)"] = pd.to_numeric(edited_df["OT(ชม.)"], errors='coerce').fillna(0)
            edited_df["ค่าอาหาร"] = pd.to_numeric(edited_df["ค่าอาหาร"], errors='coerce').fillna(0)
            multiplier_num = edited_df["ตัวคูณ"].str.replace('x', '').astype(float)
            edited_df["ค่า OT"] = edited_df["OT(ชม.)"] * multiplier_num * rate_per_hour
            edited_df["รวมสุทธิ"] = edited_df["เงินรายวัน"] + edited_df["ค่า OT"] + edited_df["ค่าอาหาร"]
            
            st.session_state.salary_db = edited_df
            st.rerun()

    # --- ส่วนรวบรวมยอดรวมสะสมด้านล่าง ---
    st.markdown("### 💰 สรุปยอดรวมสะสม")
    sum_c1, sum_c2, sum_c3, sum_c4 = st.columns(4)
    
    total_wage = pd.to_numeric(st.session_state.salary_db["เงินรายวัน"]).sum()
    total_ot = pd.to_numeric(st.session_state.salary_db["ค่า OT"]).sum()
    total_meal = pd.to_numeric(st.session_state.salary_db["ค่าอาหาร"]).sum()
    total_all = pd.to_numeric(st.session_state.salary_db["รวมสุทธิ"]).sum()
    
    sum_c1.metric("รวมเงินรายวัน", f"{total_wage:,.2f} ฿")
    sum_c2.metric("รวมค่า OT", f"{total_ot:,.2f} ฿")
    sum_c3.metric("รวมค่าอาหาร", f"{total_meal:,.2f} ฿")
    sum_c4.metric("ยอดรับสุทธิทั้งหมด", f"{total_all:,.2f} ฿")

# --- ส่วนที่ 4: Logic การคำนวณ (เหมือนเดิมแต่แม่นยำขึ้น) ---
results = []
for _, row in edited_df.iterrows():
    if row["มาทำงาน"]:
        basic = daily_rate
        if row["มี OT"]:
            kpi, meal = 95, 80
            ot_sum = (
                (row["x1"] * hourly_rate * 1) + (row["x1.5"] * hourly_rate * 1.5) +
                (row["x2"] * hourly_rate * 2) + (row["x2.5"] * hourly_rate * 2.5) +
                (row["x3"] * hourly_rate * 3) + (row["x6"] * hourly_rate * 6)
            )
        else:
            kpi, meal, ot_sum = 90, 45, 0
    else:
        basic = ot_sum = kpi = meal = 0
    results.append({"basic": basic, "ot": ot_sum, "kpi": kpi, "meal": meal, "total": basic+ot_sum+kpi+meal})

res_df = pd.DataFrame(results)

# --- ส่วนที่ 5: แสดงผลสรุป ---
st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 ค่าจ้างปกติรวม", f"{res_df['basic'].sum():,.2f}")
m2.metric("⚡ OT รวม", f"{res_df['ot'].sum():,.2f}")
m3.metric("📊 KPI รวม", f"{res_df['kpi'].sum():,.2f}")
m4.metric("🍱 ค่าอาหารรวม", f"{res_df['meal'].sum():,.2f}")


st.success(f"## 🏆 รายรับสุทธิรวมในช่วงวันที่เลือก: {res_df['total'].sum():,.2f} บาท")
