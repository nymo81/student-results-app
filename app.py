import streamlit as st
import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os
import base64
import requests
from io import BytesIO

# --- Arabic Text Fixer ---
def ar(text):
    if not text or pd.isna(text): 
        return ""
    return get_display(reshape(str(text)))

# --- Grading Logic ---
def get_grade(score):
    try:
        if pd.isna(score) or str(score).strip() == "":
            return "غائب"
        s = float(str(score).strip())
        if s >= 90: return "ممتاز"
        if s >= 80: return "جيد جدًا"
        if s >= 70: return "جيد"
        if s >= 60: return "متوسط"
        if s >= 50: return "مقبول"
        if 45 <= s < 50: return "قيد المعالجة"
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
            self.image(logo_data, x=155, y=y_offset + 10, w=45)

        # 2. Header Text
        self.set_font("Amiri", size=15)
        self.set_xy(10, y_offset + 10)
        self.cell(140, 8, ar("جامعة التراث"), ln=1, align='R')
        self.set_font("Amiri", size=12)
        self.cell(140, 7, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.set_font("Amiri", size=11)
        # Dynamic Stage Name from Dropdown
        self.cell(140, 6, ar(f"{stage_name} - العام الدراسي 2025-2026"), ln=1, align='R')

        # 3. Student Info
        self.set_y(y_offset + 40)
        self.set_font("Amiri", size=14)
        name_val = data.get('اسم الطالب', '---')
        self.cell(190, 10, ar(f"اسم الطالب: {name_val}"), 0, 1, 'R')

        # 4. Define Subjects based on Stage
        if "الأولى" in stage_name:
            subjects = [
                ("الرسم الهندسي", data.get("الرسم الهندسي", 0)),
                ("ميكانيك", data.get("ميكانيك", 0)),
                ("الرياضيات", data.get("الرياضيات", 0)),
                ("اللغة العربية", data.get("اللغة العربية", 0)),
                ("مواد البناء", data.get("مواد البناء", 0)),
                ("حاسوب", data.get("حاسوب", 0))
            ]
        else:
            subjects = [
                ("الرياضيات", data.get("الرياضيات", 0)),
                ("المقاومة", data.get("المقاومة", 0)),
                ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
                ("الموائع", data.get("الموائع", 0)),
                ("الخرسانة", data.get("الخرسانة", data.get("الخرسانه", 0))),
                ("انشاء المباني", data.get("انشاء المباني", 0))
            ]

        # 5. Table (Shifted Right)
        start_x = 65 
        self.set_xy(start_x, y_offset + 55)
        self.set_fill_color(245, 245, 245)
        self.set_font("Amiri", size=12)
        
        self.cell(45, 10, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(85, 10, ar("المادة"), 1, 1, 'C', fill=True)
        
        for sub, score in subjects:
            self.set_x(start_x)
            self.cell(45, 9, ar(get_grade(score)), 1, 0, 'C')
            self.cell(85, 9, ar(sub), 1, 1, 'C')

        # 6. Stamp & Sign (Actual Size - Colorful)
        if os.path.exists("stamp.png"):
            # Increased Y-offset and size for the 2-slip layout
            self.image("stamp.png", x=10, y=y_offset + 60, w=50)
        
        self.set_xy(10, y_offset + 115)
        self.set_font("Amiri", size=10)
        self.cell(50, 5, ar("توقيع اللجنة الامتحانية"), 0, 1, 'C')

        # 7. Bold Official Note
        self.set_xy(10, y_offset + 135)
        self.set_font("Amiri", size=11)
        self.cell(190, 5, ar("ملاحظة: لاتعتبر هذة الورقة وثيقة رسمية"), 0, 1, 'C')

        # 8. Divider Line (A4 height is 297, so half is 148.5)
        self.set_draw_color(180, 180, 180)
        self.line(0, y_offset + 148, 210, y_offset + 148)

# --- Streamlit UI ---
st.set_page_config(page_title="Al-Turath Results", layout="centered")
st.title("🎓 Result Slip Management System")

# 1. Dropdown for Stage Selection
stage_option = st.selectbox(
    "Select Academic Stage:",
    ("المرحلة الأولى", "المرحلة الثانية")
)

logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Turath_University_Logo_New.jpg"
logo_data = get_logo_bytes(logo_url)

file = st.file_uploader("Upload Excel File", type=["xlsx"])

if file:
    df = pd.read_excel(file, engine='openpyxl')
    df.columns = df.columns.str.strip()
    
    st.success(f"Successfully loaded {len(df)} records for {stage_option}.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ Preview Design"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            pdf.add_page()
            pdf.draw_slip(df.iloc[0], 0, logo_data, stage_option)
            base64_pdf = base64.b64encode(pdf.output()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)

    with col2:
        if st.button("🚀 Download Full PDF"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            
            for i, row in df.iterrows():
                # For 2 slips per page: check if index is even
                if i % 2 == 0: pdf.add_page()
                # Math: 148.5mm per slip
                pdf.draw_slip(row, (i % 2) * 148.5, logo_data, stage_option)
                
            st.download_button("⬇️ Save PDF", bytes(pdf.output()), f"Results_{stage_option}.pdf")
