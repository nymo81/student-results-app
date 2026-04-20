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

# --- FIXED GRADING LOGIC (Aggressive Cleaning) ---
def get_grade(score):
    try:
        if pd.isna(score): return "غائب"
        # Remove any non-numeric characters except dots
        clean_s = re.sub(r'[^\d.]', '', str(score).strip())
        if not clean_s: return "غائب"
        
        s = float(clean_s)
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
        self.set_text_color(0, 51, 102) # Dark Blue Header
        self.set_font("Amiri", size=15)
        self.set_xy(10, y_offset + 12)
        self.cell(140, 8, ar("جامعة التراث"), ln=1, align='R')
        self.set_font("Amiri", size=12)
        self.cell(140, 7, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.set_font("Amiri", size=11)
        self.cell(140, 6, ar(f"{stage_name} - العام الدراسي 2025-2026"), ln=1, align='R')

        # 3. Student Name
        self.set_text_color(0, 0, 0) # Black Text
        self.set_y(y_offset + 45)
        self.set_font("Amiri", size=14)
        # Find name by index 1 (Column B)
        name_val = data.iloc[1] if len(data) > 1 else "---"
        self.cell(190, 10, ar(f"اسم الطالب: {name_val}"), 0, 1, 'R')

        # 4. Define Subjects
        if "الأولى" in stage_name:
            sub_list = ["الرسم الهندسي", "ميكانيك", "الرياضيات", "اللغة العربية", "مواد البناء", "حاسوب", "رسم هندسي"]
        else:
            sub_list = ["الرياضيات", "المقاومة", "المساحة الهندسية", "الموائع", "الخرسانة", "انشاء المباني"]

        subjects = []
        for s_name in sub_list:
            # Flexible mapping: find column that contains the subject name
            val = 0
            for col in data.index:
                if s_name in str(col):
                    val = data[col]
                    break
            subjects.append((s_name, val))

        # 5. Table (Colorful & Bordered)
        start_x = 65 
        self.set_xy(start_x, y_offset + 60)
        
        # Header Styling
        self.set_fill_color(0, 51, 102) # Dark Blue Header
        self.set_text_color(255, 255, 255) # White Text
        self.set_font("Amiri", size=12)
        self.cell(45, 10, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(85, 10, ar("المادة"), 1, 1, 'C', fill=True)
        
        # Rows Styling
        self.set_text_color(0, 0, 0)
        for i, (sub, score) in enumerate(subjects):
            self.set_x(start_x)
            # Alternating Row Colors
            if i % 2 == 0:
                self.set_fill_color(240, 245, 255) # Very Light Blue
            else:
                self.set_fill_color(255, 255, 255) # White
            
            grade = get_grade(score)
            # Highlight "Weak" in red-ish text
            if grade == "ضعيف": self.set_text_color(200, 0, 0)
            else: self.set_text_color(0, 0, 0)
                
            self.cell(45, 9, ar(grade), 1, 0, 'C', fill=True)
            self.set_text_color(0, 0, 0) # Reset to black for subject name
            self.cell(85, 9, ar(sub), 1, 1, 'C', fill=True)

        # 6. Stamp & Sign (Actual Size)
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=10, y=y_offset + 75, w=55)
        
        self.set_xy(10, y_offset + 130)
        self.set_font("Amiri", size=11)
        self.cell(55, 5, ar("توقيع اللجنة الامتحانية"), 0, 1, 'C')

        # 7. Bold Official Note
        self.set_xy(10, y_offset + 142)
        self.set_font("Amiri", size=12)
        self.cell(190, 5, ar("ملاحظة: لاتعتبر هذة الورقة وثيقة رسمية"), 0, 1, 'C')

        # 8. Divider Line
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.5)
        self.line(0, y_offset + 148.5, 210, y_offset + 148.5)

# --- Streamlit UI ---
st.set_page_config(page_title="Result Generator", layout="centered")
st.title("📑 Al-Turath Official Result Slips")

stage_option = st.selectbox("Select Stage:", ("المرحلة الأولى", "المرحلة الثانية"))

logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Turath_University_Logo_New.jpg"
logo_data = get_logo_bytes(logo_url)

file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file, engine='openpyxl')
    # Strip spaces from column names
    df.columns = [str(c).strip() for c in df.columns]
    
    st.success(f"Loaded {len(df)} students.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ Preview First Slip"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            pdf.add_page()
            pdf.draw_slip(df.iloc[0], 0, logo_data, stage_option)
            base64_pdf = base64.b64encode(pdf.output()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>', unsafe_allow_html=True)

    with col2:
        if st.button("🚀 Download Full PDF"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            for i, row in df.iterrows():
                if i % 2 == 0: pdf.add_page()
                pdf.draw_slip(row, (i % 2) * 148.5, logo_data, stage_option)
            st.download_button("⬇️ Download", bytes(pdf.output()), f"{stage_option}_Results.pdf")
