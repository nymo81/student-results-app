import streamlit as st
import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os

# --- Helper Function for Arabic Text ---
def ar(text):
    if not text or pd.isna(text):
        return ""
    reshaped_text = reshape(str(text))
    return get_display(reshaped_text)

# --- Grading Logic ---
def get_grade(score):
    try:
        score = float(score)
        if score >= 90: return "ممتاز"
        if score >= 80: return "جيد جدًا"
        if score >= 70: return "جيد"
        if score >= 60: return "متوسط"
        if score >= 50: return "مقبول"
        if 45 <= score < 50: return "قيد المعالجة"
        return "ضعيف"
    except:
        return ""

class ResultPDF(FPDF):
    def add_student_slip(self, data, y_offset):
        # 1. Background Watermark
        if os.path.exists("images/watermark.png"):
            self.image("images/watermark.png", x=50, y=y_offset + 20, w=110, type='PNG')
        
        # 2. Header (Logo & University Info)
        if os.path.exists("images/logo.png"):
            self.image("images/logo.png", x=170, y=y_offset + 5, w=25)
            
        self.set_xy(10, y_offset + 10)
        self.set_font("Amiri", size=12)
        self.cell(160, 5, ar("جامعة التراث"), ln=1, align='R')
        self.cell(160, 5, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.cell(160, 5, ar("المرحلة الثانية - السميستر الاول"), ln=1, align='R')
        self.cell(160, 5, ar("العام الدراسي 2025-2026"), ln=1, align='R')

        # 3. Student Info
        self.set_xy(10, y_offset + 35)
        name_text = f"اسم الطالب: {data['اسم الطالب']}"
        self.cell(190, 10, ar(name_text), border=0, align='R')

        # 4. Results Table
        subjects = [
            ("الرياضيات", data.get("الرياضيات", 0)),
            ("المقاومة", data.get("المقاومة", 0)),
            ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
            ("الموائع", data.get("الموائع", 0)),
            ("الخرسانة", data.get("الخرسانة", 0)),
            ("انشاء المباني", data.get("انشاء المباني", 0))
        ]
        
        self.set_xy(15, y_offset + 45)
        # Table Header
        self.cell(40, 8, ar("عدد المحاولات"), 1, 0, 'C')
        self.cell(40, 8, ar("التقدير"), 1, 0, 'C')
        self.cell(100, 8, ar("المادة"), 1, 1, 'C')
        
        # Table Rows
        for sub, score in subjects:
            self.set_x(15)
            self.cell(40, 8, "1", 1, 0, 'C')
            self.cell(40, 8, ar(get_grade(score)), 1, 0, 'C')
            self.cell(100, 8, ar(sub), 1, 1, 'C')

        # 5. Footer & Stamp
        if os.path.exists("images/stamp.png"):
            self.image("images/stamp.png", x=20, y=y_offset + 75, w=35)
        
        self.set_xy(10, y_offset + 95)
        self.set_font("Amiri", size=8)
        self.cell(190, 5, ar("ملاحظة: لا تعتبر هذه الورقة وثيقة رسمية"), 0, 0, 'C')
        
        # Draw Divider Line
        self.line(10, y_offset + 100, 200, y_offset + 100)

# --- Streamlit UI ---
st.set_page_config(page_title="Student Result Generator")
st.title("🖨️ Civil Engineering Result Slips")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write(f"Loaded {len(df)} students.")
    
    if st.button("Generate All Slips (PDF)"):
        pdf = ResultPDF()
        pdf.add_font("Amiri", "", "fonts/Amiri-Regular.ttf")
        
        for i, row in df.iterrows():
            if i % 3 == 0:  # 3 slips per page
                pdf.add_page()
            
            y_pos = (i % 3) * 100 # Adjust spacing
            pdf.add_student_slip(row, y_pos)
            
        pdf_output = pdf.output()
        st.download_button("Download PDF", data=pdf_output, file_name="Results_2026.pdf")
