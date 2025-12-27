import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

st.set_page_config(page_title="Salary Calculator", layout="wide")

st.title("💰 โปรแกรมคำนวณเงินเดือน (Date Range & Highlight Version)")

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

# --- ส่วนที่ 3: เตรียมข้อมูลตารางตามวันที่เลือกจริง ---
# สร้างรายการวันที่และชื่อวัน
date_list = []
day_names_th = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

for i in range(num_days):
    current_dt = start_date + timedelta(days=i)
    day_name = day_names_th[current_dt.weekday()]
    date_str = f"{current_dt.strftime('%d/%m/%Y')} ({day_name})"
    date_list.append(date_str)

# เช็ค Session State เพื่อสร้างตารางใหม่เมื่อมีการเปลี่ยนช่วงวันที่
if 'df_input' not in st.session_state or len(st.session_state.df_input) != num_days:
    init_data = {
        "วันที่": date_list,
        "มาทำงาน": [False] * num_days,
        "มี OT": [False] * num_days,
        "x1": [0.0] * num_days, "x1.5": [0.0] * num_days, "x2": [0.0] * num_days,
        "x2.5": [0.0] * num_days, "x3": [0.0] * num_days, "x6": [0.0] * num_days,
    }
    st.session_state.df_input = pd.DataFrame(init_data)
else:
    # อัปเดตเฉพาะรายชื่อวันที่หากจำนวนวันเท่าเดิมแต่ช่วงวันที่เปลี่ยน
    st.session_state.df_input["วันที่"] = date_list

# ฟังก์ชันสำหรับระบายสีวันอาทิตย์
def highlight_sunday(row):
    return ['background-color: #ffff99' if 'อาทิตย์' in str(row['วันที่']) else '' for _ in row]

# แสดงตารางแบบ Data Editor
st.write("### 📝 ใบลงเวลา")
edited_df = st.data_editor(
    st.session_state.df_input.style.apply(highlight_sunday, axis=1), # ใส่สีเหลือง
    hide_index=True,
    use_container_width=True,
    column_config={
        "วันที่": st.column_config.TextColumn("วันที่", disabled=True, width="medium"),
        "มาทำงาน": st.column_config.CheckboxColumn("มาทำงาน"),
        "มี OT": st.column_config.CheckboxColumn("มี OT"),
        "x1": st.column_config.SelectboxColumn("x1", options=ot_options),
        "x1.5": st.column_config.SelectboxColumn("x1.5", options=ot_options),
        "x2": st.column_config.SelectboxColumn("x2", options=ot_options),
        "x2.5": st.column_config.SelectboxColumn("x2.5", options=ot_options),
        "x3": st.column_config.SelectboxColumn("x3", options=ot_options),
        "x6": st.column_config.SelectboxColumn("x6", options=ot_options),
    }
)

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