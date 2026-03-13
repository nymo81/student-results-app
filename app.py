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
        s = round(float(str(score).strip()))
        if s >= 90: return "ممتاز"
        if s >= 80: return "جيد جدًا"
        if s >= 70: return "جيد"
        if s >= 60: return "متوسط"
        if s >= 50: return "مقبول"
        if 45 <= s < 50: return "قيد المعالجة"
        return "ضعيف"
    except:
        return "غائب"

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
    def draw_slip(self, data, y_offset, logo_data):
        # 1. Header & Logo (Logo moved slightly higher)
        if logo_data:
            self.image(logo_data, x=155, y=y_offset + 5, w=45)

        self.set_font("Amiri", size=13)
        self.set_xy(10, y_offset + 5)
        self.cell(140, 6, ar("جامعة التراث"), ln=1, align='R')
        self.set_font("Amiri", size=10)
        self.cell(140, 5, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.cell(140, 5, ar("المرحلة الثانية - العام الدراسي 2025-2026"), ln=1, align='R')

        # 2. Student Name (Space minimized)
        self.set_y(y_offset + 25)
        self.set_font("Amiri", size=12)
        name_val = data.get('اسم الطالب', '---')
        self.cell(190, 8, ar(f"اسم الطالب: {name_val}"), 0, 1, 'R')

        # 3. Layout: Table (3/4 Right) and Stamp (1/4 Left)
        subjects = [
            ("الرياضيات", data.get("الرياضيات", 0)),
            ("المقاومة", data.get("المقاومة", 0)),
            ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
            ("الموائع", data.get("الموائع", 0)),
            ("الخرسانة", data.get("الخرسانة", data.get("الخرسانه", 0))),
            ("انشاء المباني", data.get("انشاء المباني", 0))
        ]

        # Table Start Position (X=65 leaves 55mm space on the left)
        start_x = 65 
        self.set_xy(start_x, y_offset + 35)
        self.set_fill_color(245, 245, 245)
        self.set_font("Amiri", size=11)
        
        # Table Header
        self.cell(45, 8, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(85, 8, ar("المادة"), 1, 1, 'C', fill=True)
        
        # Table Rows
        for sub, score in subjects:
            self.set_x(start_x)
            self.cell(45, 7, ar(get_grade(score)), 1, 0, 'C')
            self.cell(85, 7, ar(sub), 1, 1, 'C')

        # 4. Note (Directly under the table)
        self.set_xy(start_x, y_offset + 80)
        self.set_font("Amiri", size=8)
        self.cell(130, 5, ar("ملاحظة: لا تعتبر هذه الورقة وثيقة رسمية"), 0, 1, 'C')

        # 5. Stamp (In the blank 1/4 area on the left)
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=15, y=y_offset + 50, w=40)
        
        # 6. Committee Signature Label
        self.set_xy(15, y_offset + 80)
        self.cell(40, 5, ar("توقيع اللجنة الامتحانية"), 0, 1, 'C')

        # 7. Exact Divider Line (End of Slip)
        self.set_draw_color(180, 180, 180)
        self.line(0, y_offset + 98.5, 210, y_offset + 98.5)

# --- Streamlit UI ---
st.set_page_config(page_title="Result Generator", layout="centered")
st.title("🎓 Result Slip Generator")

logo_url = "https://upload.wikimedia.org/wikipedia/commons/c/c0/Turath_University_Logo_New.jpg"
logo_data = get_logo_bytes(logo_url)

file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file, engine='openpyxl')
    
    if st.button("👁️ Preview Design"):
        pdf = ResultPDF(orientation='P', unit='mm', format='A4')
        pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
        pdf.add_page()
        pdf.draw_slip(df.iloc[0], 0, logo_data)
        base64_pdf = base64.b64encode(pdf.output()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="550" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    if st.button("🚀 Download All (3 Slips per A4)"):
        pdf = ResultPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=False)
        pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
        
        for i, row in df.iterrows():
            if i % 3 == 0: pdf.add_page()
            # 99mm offset ensures 3 fit on 297mm height
            pdf.draw_slip(row, (i % 3) * 99, logo_data)
        
        st.download_button("⬇️ Save PDF", bytes(pdf.output()), "Student_Results_2026.pdf")
