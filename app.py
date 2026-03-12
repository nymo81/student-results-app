import streamlit as st
import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os

# --- Helper: Fix Arabic RTL ---
def ar(text):
    if not text or pd.isna(text): 
        return ""
    return get_display(reshape(str(text)))

# --- Helper: Grading Logic ---
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
        # 1. Background Watermark (Light and Centered)
        if os.path.exists("watermark.png"):
            self.set_alpha(0.08)
            # Centered on A4 (210mm wide): (210-110)/2 = 50
            self.image("watermark.png", x=50, y=y_offset + 10, w=110)
            self.set_alpha(1.0)

        # 2. Header: Logo (Large)
        if os.path.exists("logo.png"):
            self.image("logo.png", x=165, y=y_offset + 5, w=35)

        # 3. Header: University Info
        self.set_font("Amiri", size=14)
        self.set_xy(10, y_offset + 8)
        self.cell(150, 7, ar("جامعة التراث"), ln=1, align='R')
        self.set_font("Amiri", size=11)
        self.cell(150, 6, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.set_font("Amiri", size=10)
        self.cell(150, 5, ar("المرحلة الثانية - العام الدراسي 2025-2026"), ln=1, align='R')

        # 4. Student Info
        self.set_y(y_offset + 32)
        self.set_font("Amiri", size=13)
        id_val = data.get('ت', '---')
        name_val = data.get('اسم الطالب', '---')
        student_line = f"اسم الطالب: {name_val}           ت: {id_val}"
        self.cell(190, 10, ar(student_line), 0, 1, 'R')

        # 5. Results Table (2 Columns: Grade | Subject)
        subjects = [
            ("الرياضيات", data.get("الرياضيات", 0)),
            ("المقاومة", data.get("المقاومة", 0)),
            ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
            ("الموائع", data.get("الموائع", 0)),
            ("الخرسانة", data.get("الخرسانة", data.get("الخرسانه", 0))),
            ("انشاء المباني", data.get("انشاء المباني", 0))
        ]

        self.set_x(15)
        self.set_fill_color(235, 235, 235)
        self.set_font("Amiri", size=12)
        
        # Header Row
        self.cell(60, 9, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(120, 9, ar("المادة"), 1, 1, 'C', fill=True)
        
        # Data Rows
        for sub, score in subjects:
            self.set_x(15)
            self.cell(60, 8, ar(get_grade(score)), 1, 0, 'C')
            self.cell(120, 8, ar(sub), 1, 1, 'C')

        # 6. Stamp and Signature (Bottom Left)
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=20, y=y_offset + 72, w=50)

        # 7. Official Note
        self.set_xy(10, y_offset + 90)
        self.set_font("Amiri", size=8)
        self.cell(190, 4, ar("توقيع اللجنة الامتحانية"), 0, 1, 'L')
        self.cell(190, 4, ar("ملاحظة: لا تعتبر هذه الورقة وثيقة رسمية"), 0, 1, 'C')

        # 8. Exact Divider Line
        self.set_draw_color(170, 170, 170)
        self.set_line_width(0.3)
        self.line(0, y_offset + 98.8, 210, y_offset + 98.8)

# --- Streamlit Frontend ---
st.set_page_config(page_title="Result Slip System", layout="wide")
st.title("📑 Civil Engineering Result Slips")

file = st.file_uploader("Upload Excel File", type=["xlsx"])

if file:
    try:
        df = pd.read_excel(file, engine='openpyxl')
        st.success(f"Loaded {len(df)} records successfully.")
        
        if st.button("🚀 Generate and Download PDF"):
            pdf = ResultPDF(orientation='P', unit='mm', format='A4')
            pdf.set_auto_page_break(auto=False)
            
            if os.path.exists("Amiri-Regular.ttf"):
                pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
            else:
                st.error("Font 'Amiri-Regular.ttf' not found in main directory!")
                st.stop()
                
            for i, row in df.iterrows():
                if i % 3 == 0:
                    pdf.add_page()
                
                # Math: 297mm height / 3 = 99mm offset
                y_offset = (i % 3) * 99
                pdf.draw_slip(row, y_offset)
                
            pdf_bytes = bytes(pdf.output())
            st.download_button(
                label="⬇️ Download All Slips",
                data=pdf_bytes,
                file_name="Final_Results.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Error reading file: {e}")
