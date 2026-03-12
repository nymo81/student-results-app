import streamlit as st
import pandas as pd
from fpdf import FPDF
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os

# --- Helper: Fix Arabic RTL Display ---
def ar(text):
    if not text or pd.isna(text): 
        return ""
    # Reshape handles letter connectivity, get_display handles RTL direction
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
        # 1. Background Watermark (Main folder)
        if os.path.exists("watermark.png"):
            self.image("watermark.png", x=60, y=y_offset + 25, w=90)
        
        # 2. Header Logo (Main folder)
        if os.path.exists("logo.png"):
            self.image("logo.png", x=175, y=y_offset + 5, w=20)
        
        # 3. Header Text
        self.set_font("Amiri", size=11)
        self.set_xy(10, y_offset + 5)
        self.cell(160, 5, ar("جامعة التراث"), ln=1, align='R')
        self.cell(160, 5, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.cell(160, 5, ar("المرحلة الثانية - السميستر الاول"), ln=1, align='R')
        self.cell(160, 5, ar("العام الدراسي 2025-2026"), ln=1, align='R')

        # 4. Student Information
        self.set_y(y_offset + 30)
        self.set_font("Amiri", size=12)
        id_val = data.get('ت', '')
        name_val = data.get('اسم الطالب', '')
        self.cell(95, 10, ar(f"رقم الطالب: {id_val}"), 0, 0, 'R')
        self.cell(95, 10, ar(f"اسم الطالب: {name_val}"), 0, 1, 'R')

        # 5. Grades Table
        subjects = [
            ("الرياضيات", data.get("الرياضيات", 0)),
            ("المقاومة", data.get("المقاومة", 0)),
            ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
            ("الموائع", data.get("الموائع", 0)),
            ("الخرسانة", data.get("الخرسانة", 0)),
            ("انشاء المباني", data.get("انشاء المباني", 0))
        ]
        
        self.set_x(20)
        self.set_fill_color(245, 245, 245)
        self.cell(40, 8, ar("عدد المحاولات"), 1, 0, 'C', fill=True)
        self.cell(40, 8, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(90, 8, ar("المادة"), 1, 1, 'C', fill=True)
        
        for sub, score in subjects:
            self.set_x(20)
            self.cell(40, 7, "1", 1, 0, 'C')
            self.cell(40, 7, ar(get_grade(score)), 1, 0, 'C')
            self.cell(90, 7, ar(sub), 1, 1, 'C')

        # 6. Stamp/Signature (Main folder)
        if os.path.exists("stamp.png"):
            self.image("stamp.png", x=25, y=y_offset + 75, w=35)
        
        self.set_xy(10, y_offset + 88)
        self.set_font("Amiri", size=9)
        self.cell(190, 4, ar("توقيع اللجنة الامتحانية"), 0, 1, 'L')
        self.cell(190, 10, ar("ملاحظة: لا تعتبر هذه الورقة وثيقة رسمية"), 0, 1, 'C')
        
        # Divider Line
        self.set_draw_color(180, 180, 180)
        self.line(10, y_offset + 98, 200, y_offset + 98)

# --- Streamlit Frontend ---
st.set_page_config(page_title="Result Slip Generator", layout="centered")
st.title("📊 Civil Engineering Result Slips")

uploaded_file = st.file_uploader("Choose Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success(f"Loaded {len(df)} records.")
    
    if st.button("🚀 Generate PDF & Download"):
        pdf = ResultPDF(orientation='P', unit='mm', format='A4')
        
        if os.path.exists("Amiri-Regular.ttf"):
            pdf.add_font("Amiri", "", "Amiri-Regular.ttf")
        else:
            st.error("Missing Amiri-Regular.ttf in the main folder!")
            st.stop()
            
        for i, row in df.iterrows():
            if i % 3 == 0: pdf.add_page()
            y_offset = (i % 3) * 99 
            pdf.draw_slip(row, y_offset)
            
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf.output(),
            file_name="Results.pdf",
            mime="application/pdf"
        )
