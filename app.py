import streamlit as st
import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os
import base64

# --- Helper: Fix Arabic RTL ---
def ar(text):
    if not text or pd.isna(text): 
        return ""
    return get_display(reshape(str(text)))

# --- Fixed Grading Logic ---
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
    except:
        return "غائب"

class ResultPDF(FPDF):
    def draw_slip(self, data, y_offset):
        # 1. Header: Logo (Balanced Size)
        if os.path.exists("logo.png"):
            self.image("logo.png", x=170, y=y_offset + 8, w=30)

        # 2. Header: University Info
        self.set_font("Amiri", size=14)
        self.set_xy(10, y_offset + 10)
        self.cell(155, 7, ar("جامعة التراث"), ln=1, align='R')
        self.set_font("Amiri", size=11)
        self.cell(155, 6, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.set_font("Amiri", size=10)
        self.cell(155, 5, ar("المرحلة الثانية - العام الدراسي 2025-2026"), ln=1, align='R')

        # 3. Student Info (Name Only)
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
        self.set_fill_color(240, 240, 240)
        self.set_font("Amiri", size=12)
        
        # Table Header
        self.cell(60, 9, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(120, 9, ar("المادة"), 1, 1, 'C', fill=True)
        
        # Table Rows
        for sub, score in subjects:
            self.set_x(15)
            self.cell(60, 8, ar(get_grade(score)), 1, 0, 'C')
            self.cell(120, 8, ar(sub), 1, 1, 'C')

        # 5. Stamp and Signature (Natural Fit)
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=25, y=y_offset + 76, w=38)

        # 6. Official Footer
        self.set_xy(10, y_offset + 92)
        self.set_font("Amiri", size=8)
        self.cell(190, 4, ar("توقيع اللجنة الامتحانية"), 0, 1, 'L')
        self.cell(190, 4, ar("ملاحظة: لا تعتبر هذه الورقة وثيقة رسمية"), 0, 1, 'C')

        # 7. Boundary Divider
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(5, y_offset + 98.8, 205, y_offset + 98.8)

# --- Streamlit UI ---
st.set_page_config(page_title="Result Slip System", layout="wide")
st.title("📑 Professional Result Slip Generator")

file = st.file_uploader("Upload Excel File", type=["xlsx"])

if file:
    df = pd.read_excel(file, engine='openpyxl')
    st.success(f"Successfully loaded {len(df)} records.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👁️ Preview First Student"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            pdf.add_page()
            pdf.draw_slip(df.iloc[0], 0)
            
            base64_pdf = base64.b64encode(pdf.output()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="550" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

    with col2:
        if st.button("🚀 Download Full PDF"):
            with st.spinner("Generating 360 slips..."):
                pdf = ResultPDF(orientation='P', unit='mm', format='A4')
                pdf.set_auto_page_break(auto=False)
                pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
                
                for i, row in df.iterrows():
                    if i % 3 == 0: pdf.add_page()
                    pdf.draw_slip(row, (i % 3) * 99)
                    
                st.download_button("⬇️ Save Full PDF", bytes(pdf.output()), "Student_Results_Final.pdf")
