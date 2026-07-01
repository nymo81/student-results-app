import streamlit as st
import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os
import base64
import requests
from io import BytesIO
import re

# --- Arabic Text Fixer ---
def ar(text):
    if not text or pd.isna(text): 
        return ""
    return get_display(reshape(str(text)))

# --- Grading Logic (With "قيد المعالجة" for 45) ---
def get_grade(score):
    try:
        if pd.isna(score): return "غائب"
        clean_s = re.sub(r'[^\d.]', '', str(score).strip())
        if not clean_s: return "غائب"
        
        s = float(clean_s)
        # Condition for exactly 45 or rounded to 45
        if round(s) == 45: return "قيد المعالجة"
        
        if s >= 90: return "ممتاز"
        if s >= 80: return "جيد جدًا"
        if s >= 70: return "جيد"
        if s >= 60: return "متوسط"
        if s >= 50: return "مقبول"
        return "ضعيف"
    except:
        return "ضعيف"

@st.cache_data
def get_logo_bytes(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        return None

class ResultPDF(FPDF):
    def draw_slip(self, data, y_offset, logo_data, stage_name):
        # 1. Logo (Top Right)
        if logo_data:
            self.image(logo_data, x=155, y=y_offset + 12, w=45)

        # 2. Header Text
        self.set_text_color(0, 0, 0)
        self.set_font("Amiri", size=15)
        self.set_xy(10, y_offset + 12)
        self.cell(140, 8, ar("جامعة التراث"), ln=1, align='R')
        self.set_font("Amiri", size=12)
        self.cell(140, 7, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.set_font("Amiri", size=11)
        self.cell(140, 6, ar(f"{stage_name} - العام الدراسي 2025-2026"), ln=1, align='R')

        # 3. Student Name & Group (Column B / Index 1)
        self.set_y(y_offset + 42)
        self.set_font("Amiri", size=14) 
        name_val = data.iloc[1]
        
        # Extract Group Letter Dynamic Check
        raw_group = "---"
        for col in data.index:
            if "الشعب" in str(col):
                raw_group = str(data[col])
                break
        group_letter = raw_group.replace('group -', '').replace('Group -', '').replace('group-','').strip()
        
        student_info = f"اسم الطالب: {name_val}    -    الشعبة: {group_letter}"
        self.cell(190, 10, ar(student_info), 0, 1, 'R')

        # 4. SUBJECT MAPPING
        subjects = []
        if "الأولى" in stage_name:
            try:
                subjects = [
                    (data.index[2], data.iloc[2]), 
                    (data.index[3], data.iloc[3]), 
                    (data.index[4], data.iloc[4]), 
                    (data.index[5], data.iloc[5]), 
                    (data.index[6], data.iloc[6]), 
                    (data.index[7], data.iloc[7])
                ]
            except Exception as e:
                st.error("Excel columns are not in the expected order.")
        else:
            # New updated Semester 2 subject list for Phase 2
            sub_list = [
                "المقاومة", "التحليلات الهندسية", "تقنية الخرسانية", 
                "المساحة الهندسية", "ميكانيك الموائع", "جرائم البعث", 
                "اللغة العربية", "الحاسوب", "اللغة الانكليزية", "معالجات"
            ]
            for s_name in sub_list:
                val = 0
                found_name = s_name
                for col in data.index:
                    if s_name in str(col):
                        val = data[col]
                        found_name = str(col) # Keep actual column header text
                        break
                subjects.append((found_name, val))

        # 5. Table Layout (Dynamic spacing if subject list gets long)
        start_x = 65 
        # Scale row height slightly based on row count to ensure perfect fit inside A4 half
        row_h = 7.5 if len(subjects) > 7 else 10
        
        self.set_xy(start_x, y_offset + 55)
        self.set_fill_color(214, 230, 245) 
        self.set_font("Amiri", size=12)
        self.cell(45, 9, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(85, 9, ar("المادة"), 1, 1, 'C', fill=True)
        
        for i, (sub, score) in enumerate(subjects):
            self.set_x(start_x)
            self.set_fill_color(245, 250, 255) if i % 2 == 0 else self.set_fill_color(255, 255, 255)
            
            grade = get_grade(score)
            self.set_font("Amiri", size=11)
            
            # Text formatting highlights
            if grade == "ضعيف": 
                self.set_text_color(200, 0, 0)
            elif grade == "قيد المعالجة":
                self.set_text_color(210, 105, 30) # Distinct orange/brown color
            else: 
                self.set_text_color(0, 0, 0)

            self.cell(45, row_h, ar(grade), 1, 0, 'C', fill=True)
            self.set_text_color(0, 0, 0)
            self.cell(85, row_h, ar(sub), 1, 1, 'C', fill=True)

        # 6. Stamp & Sign (Actual Size Left Space)
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=5, y=y_offset + 62, w=65)
        
        self.set_xy(5, y_offset + 128)
        self.set_font("Amiri", size=11)
        self.cell(65, 5, ar("توقيع اللجنة الامتحانية"), 0, 1, 'C')

        # 7. Note
        self.set_xy(10, y_offset + 140)
        self.set_font("Amiri", size=12)
        self.cell(190, 5, ar("ملاحظة: لاتعتبر هذة الورقة وثيقة رسمية"), 0, 1, 'C')

        # 8. Divider Line
        self.set_draw_color(200, 200, 200)
        self.line(0, y_offset + 148.5, 210, y_offset + 148.5)

# --- Streamlit UI ---
st.set_page_config(page_title="Al-Turath Official Results", layout="centered")
st.title("📑 Official Result Slips")

stage_option = st.selectbox("Academic Stage:", ("المرحلة الأولى", "المرحلة الثانية"))

logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Turath_University_Logo_New.jpg"
logo_data = get_logo_bytes(logo_url)

file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    # Ensure raw header string spaces don't interfere with rendering
    df = pd.read_excel(file, engine='openpyxl')
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ Preview First Slip"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            pdf.add_page()
            pdf.draw_slip(df.iloc[0], 0, logo_data, stage_option)
            b64_pdf = base64.b64encode(pdf.output()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="700" type="application/pdf"></iframe>', unsafe_allow_html=True)

    with col2:
        if st.button("🚀 Download Full PDF"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            for i, row in df.iterrows():
                if i % 2 == 0: pdf.add_page()
                pdf.draw_slip(row, (i % 2) * 148.5, logo_data, stage_option)
            st.download_button("⬇️ Save PDF", bytes(pdf.output()), f"Final_Results_{stage_option}.pdf")
