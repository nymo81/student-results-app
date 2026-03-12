import streamlit as st
import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os

def ar(text):
    if not text or pd.isna(text): return ""
    return get_display(reshape(str(text)))

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
        # 1. Centered Transparent Watermark
        if os.path.exists("watermark.png"):
            self.set_alpha(0.1) # Set transparency (0.1 = 10%)
            # A4 is 210mm wide. Watermark is 100mm. (210-100)/2 = 55mm
            self.image("watermark.png", x=55, y=y_offset + 15, w=100)
            self.set_alpha(1.0) # Reset transparency to full for the rest of the slip
        
        # 2. Larger Logo
        if os.path.exists("logo.png"):
            self.image("logo.png", x=165, y=y_offset + 8, w=30)
        
        # 3. Header Text
        self.set_font("Amiri", size=12)
        self.set_xy(10, y_offset + 10)
        self.cell(150, 6, ar("جامعة التراث"), ln=1, align='R')
        self.cell(150, 6, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.set_font("Amiri", size=10)
        self.cell(150, 5, ar("المرحلة الثانية - العام الدراسي 2025-2026"), ln=1, align='R')

        # 4. Student Info
        self.set_y(y_offset + 35)
        self.set_font("Amiri", size=13)
        id_val = data.get('ت', '---')
        name_val = data.get('اسم الطالب', '---')
        self.cell(95, 10, ar(f"رقم الطالب: {id_val}"), 0, 0, 'R')
        self.cell(95, 10, ar(f"اسم الطالب: {name_val}"), 0, 1, 'R')

        # 5. Grades Table
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
        self.set_font("Amiri", size=11)
        self.cell(40, 8, ar("عدد المحاولات"), 1, 0, 'C', fill=True)
        self.cell(40, 8, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(100, 8, ar("المادة"), 1, 1, 'C', fill=True)
        
        for sub, score in subjects:
            self.set_x(15)
            self.cell(40, 7, "1", 1, 0, 'C')
            self.cell(40, 7, ar(get_grade(score)), 1, 0, 'C')
            self.cell(100, 7, ar(sub), 1, 1, 'C')

        # 6. Fit-to-Scale Stamp & Signature
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=20, y=y_offset + 78, w=45) 
        
        # 7. Official Note
        self.set_xy(10, y_offset + 92)
        self.set_font("Amiri", size=8)
        self.cell(190, 4, ar("ملاحظة: لا تعتبر هذه الورقة وثيقة رسمية"), 0, 1, 'C')
        
        # 8. Boundary/Cut Line (Dashed for 3 slips on A4)
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.3)
        self.line(5, y_offset + 98.8, 205, y_offset + 98.8)

# --- Streamlit UI ---
st.set_page_config(page_title="Civil Engineering Slips", layout="wide")
st.title("📑 Professional Result Slip Generator")

file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file, engine='openpyxl')
    st.success(f"Loaded {len(df)} records.")
    
    if st.button("🚀 Download 3-per-Page PDF"):
        pdf = ResultPDF(orientation='P', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=False)
        
        if os.path.exists("Amiri-Regular.ttf"):
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
        else:
            st.error("Font missing!")
            st.stop()
            
        for i, row in df.iterrows():
            if i % 3 == 0: 
                pdf.add_page()
            
            y_offset = (i % 3) * 99 
            pdf.draw_slip(row, y_offset)
            
        pdf_bytes = bytes(pdf.output())
        st.download_button("⬇️ Download PDF", pdf_bytes, "Student_Results.pdf", "application/pdf")
