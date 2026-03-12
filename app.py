import streamlit as st
import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os

# Function to fix Arabic text rendering
def ar(text):
    if not text or pd.isna(text): return ""
    return get_display(reshape(str(text)))

# Grading Logic based on your requirements
def get_grade(score):
    try:
        s = float(score)
        if s >= 90: return "ممتاز"
        if s >= 80: return "جيد جدًا"
        if s >= 70: return "جيد"
        if s >= 60: return "متوسط"
        if s >= 50: return "مقبول"
        if 45 <= s < 50: return "قيد المعالجة"
        return "ضعيف"
    except: return "غائب"

class ResultPDF(FPDF):
    def draw_slip(self, data, y_offset):
        # 1. Watermark (Centered in the slip area)
        if os.path.exists("watermark.png"):
            self.image("watermark.png", x=60, y=y_offset + 25, w=90)
        
        # 2. Header
        if os.path.exists("logo.png"):
            self.image("logo.png", x=175, y=y_offset + 5, w=20)
        
        self.set_font("Amiri", size=11)
        self.set_xy(10, y_offset + 5)
        header_info = [
            "جامعة التراث",
            "كلية الهندسة / قسم الهندسة المدنية",
            "المرحلة الثانية - السميستر الاول",
            "العام الدراسي 2025-2026"
        ]
        for line in header_info:
            self.cell(160, 5, ar(line), ln=1, align='R')

        # 3. Student Details
        self.set_y(y_offset + 30)
        self.set_font("Amiri", size=12)
        # Using columns for Name and ID
        self.cell(95, 10, ar(f"رقم الطالب: {data.get('ت', '')}"), 0, 0, 'R')
        self.cell(95, 10, ar(f"اسم الطالب: {data['اسم الطالب']}"), 0, 1, 'R')

        # 4. Table
        subjects = [
            ("الرياضيات", data.get("الرياضيات", 0)),
            ("المقاومة", data.get("المقاومة", 0)),
            ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
            ("الموائع", data.get("الموائع", 0)),
            ("الخرسانة", data.get("الخرسانة", 0)),
            ("انشاء المباني", data.get("انشاء المباني", 0))
        ]
        
        self.set_x(20)
        self.set_fill_color(240, 240, 240)
        self.cell(40, 8, ar("عدد المحاولات"), 1, 0, 'C', fill=True)
        self.cell(40, 8, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(90, 8, ar("المادة"), 1, 1, 'C', fill=True)
        
        for sub, score in subjects:
            self.set_x(20)
            self.cell(40, 7, "1", 1, 0, 'C')
            self.cell(40, 7, ar(get_grade(score)), 1, 0, 'C')
            self.cell(90, 7, ar(sub), 1, 1, 'C')

        # 5. Stamp & Signature
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=25, y=y_offset + 75, w=35)
        
        self.set_xy(10, y_offset + 88)
        self.set_font("Amiri", size=8)
        self.cell(190, 4, ar("توقيع اللجنة الامتحانية"), 0, 1, 'L')
        self.set_x(10)
        self.cell(190, 4, ar("ملاحظة: لا تعتبر هذه الورقة وثيقة رسمية"), 0, 1, 'C')
        
        # Cut line
        self.set_draw_color(200, 200, 200)
        self.line(10, y_offset + 98, 200, y_offset + 98)

# --- Streamlit UI ---
st.title("🎓 نظام إصدار وثائق درجات الطلاب")
file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    if st.button("Generate All Slips"):
        pdf = ResultPDF(orientation='P', unit='mm', format='A4')
        pdf.add_font("Amiri", "", "fonts/Amiri-Regular.ttf")
        
        for i, row in df.iterrows():
            if i % 3 == 0: pdf.add_page()
            y_pos = (i % 3) * 99 # 99mm per slip = ~3 per A4
            pdf.draw_slip(row, y_pos)
            
        st.download_button("Download Result Slips", pdf.output(), "Slips.pdf")
