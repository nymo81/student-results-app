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

# --- Robust Grading Logic ---
def get_grade(score):
    try:
        s = round(float(str(score).strip()))
        if s >= 90: return "ممتاز"
        if s >= 80: return "جيد جدًا"
        if s >= 70: return "جيد"
        if s >= 60: return "متوسط"
        if s >= 50: return "مقبول"
        if 45 <= s < 50: return "قيد المعالجة"
        return "ضعيف"
    except (ValueError, TypeError):
        return "غائب"

# --- Function to Download Image safely ---
@st.cache_data
def get_logo_bytes(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return BytesIO(response.content)
    except Exception as e:
        st.error(f"Error loading logo: {e}")
    return None

class ResultPDF(FPDF):
    def draw_slip(self, data, y_offset, logo_data):
        # 1. Logo (Top Right)
        if logo_data:
            self.image(logo_data, x=155, y=y_offset + 8, w=45)

        # 2. University Header
        self.set_font("Amiri", size=14)
        self.set_xy(10, y_offset + 10)
        self.cell(140, 7, ar("جامعة التراث"), ln=1, align='R')
        self.set_font("Amiri", size=11)
        self.cell(140, 6, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.set_font("Amiri", size=10)
        self.cell(140, 5, ar("المرحلة الثانية - العام الدراسي 2025-2026"), ln=1, align='R')

        # 3. Student Name
        self.set_y(y_offset + 38)
        self.set_font("Amiri", size=14)
        name_val = data.get('اسم الطالب', '---')
        self.cell(190, 10, ar(f"اسم الطالب: {name_val}"), 0, 1, 'R')

        # 4. Results Table
        subjects = [
            ("الرياضيات", data.get("الرياضيات", 0)),
            ("المقاومة", data.get("المقاومة", 0)),
            ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
            ("الموائع", data.get("الموائع", 0)),
            ("الخرسانة", data.get("الخرسانة", data.get("الخرسانه", 0))),
            ("انشاء المباني", data.get("انشاء المباني", 0))
        ]

        self.set_x(15)
        self.set_fill_color(245, 245, 245)
        self.set_font("Amiri", size=12)
        
        self.cell(70, 10, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(110, 10, ar("المادة"), 1, 1, 'C', fill=True)
        
        for sub, score in subjects:
            self.set_x(15)
            self.cell(70, 8, ar(get_grade(score)), 1, 0, 'C')
            self.cell(110, 8, ar(sub), 1, 1, 'C')

        # 5. Stamp (Left Side)
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=20, y=y_offset + 72, w=40)

        # 6. Footer
        self.set_xy(10, y_offset + 90)
        self.set_font("Amiri", size=8)
        self.cell(190, 4, ar("توقيع اللجنة الامتحانية"), 0, 1, 'L')
        self.cell(190, 4, ar("ملاحظة: لا تعتبر هذه الورقة وثيقة رسمية"), 0, 1, 'C')

        # 7. Divider Line
        self.set_draw_color(210, 210, 210)
        self.line(0, y_offset + 99, 210, y_offset + 99)

# --- Streamlit UI ---
st.set_page_config(page_title="Result Generator", layout="centered")
st.title("🎓 Civil Engineering - Result Slips")

# Pre-load Logo
logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Turath_University_Logo_New.jpg"
logo_data = get_logo_bytes(logo_url)

file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if file:
    df = pd.read_excel(file, engine='openpyxl')
    st.success(f"Records found: {len(df)}")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👁️ Preview Design"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            pdf.add_page()
            pdf.draw_slip(df.iloc[0], 0, logo_data)
            
            base64_pdf = base64.b64encode(pdf.output()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="550" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

    with col2:
        if st.button("🚀 Download All PDF"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            
            for i, row in df.iterrows():
                if i % 3 == 0: pdf.add_page()
                pdf.draw_slip(row, (i % 3) * 99, logo_data)
            
            st.download_button("⬇️ Save PDF", bytes(pdf.output()), "Student_Results_2026.pdf")
