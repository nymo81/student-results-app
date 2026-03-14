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

# --- FIXED Grading Logic ---
def get_grade(score):
    try:
        # Handle empty cells
        if pd.isna(score) or str(score).strip() == "":
            return "غائب"
        
        # Convert to number
        s = float(str(score).strip())
        
        # Exact Grade Mapping
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
    def draw_slip(self, data, y_offset, logo_data):
        # 1. Header & Logo
        if logo_data:
            self.image(logo_data, x=155, y=y_offset + 4, w=45)

        self.set_font("Amiri", size=13)
        self.set_xy(10, y_offset + 4)
        self.cell(140, 6, ar("جامعة التراث"), ln=1, align='R')
        self.set_font("Amiri", size=10)
        self.cell(140, 5, ar("كلية الهندسة / قسم الهندسة المدنية"), ln=1, align='R')
        self.cell(140, 5, ar("المرحلة الثانية - العام الدراسي 2025-2026"), ln=1, align='R')

        # 2. Student Info (Clean Section Letter)
        self.set_y(y_offset + 22)
        self.set_font("Amiri", size=12)
        name_val = data.get('اسم الطالب', '---')
        raw_group = str(data.get('الشعبة', '---'))
        # Removes "group -", "Group -", and any trailing spaces
        group_letter = raw_group.replace('group -', '').replace('Group -', '').replace('group', '').replace('Group', '').strip()
        
        student_info = f"اسم الطالب: {name_val}    -    الشعبة: {group_letter}"
        self.cell(190, 8, ar(student_info), 0, 1, 'R')

        # 3. Subjects (Column Matching)
        subjects = [
            ("الرياضيات", data.get("الرياضيات", 0)),
            ("المقاومة", data.get("المقاومة", 0)),
            ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
            ("الموائع", data.get("الموائع", 0)),
            ("الخرسانة", data.get("الخرسانة", data.get("الخرسانه", 0))),
            ("انشاء المباني", data.get("انشاء المباني", 0))
        ]

        # 4. Table (Right 3/4)
        start_x = 65 
        self.set_xy(start_x, y_offset + 32)
        self.set_fill_color(245, 245, 245)
        self.set_font("Amiri", size=11)
        
        self.cell(45, 8, ar("التقدير"), 1, 0, 'C', fill=True)
        self.cell(85, 8, ar("المادة"), 1, 1, 'C', fill=True)
        
        for sub, score in subjects:
            self.set_x(start_x)
            self.cell(45, 7, ar(get_grade(score)), 1, 0, 'C')
            self.cell(85, 7, ar(sub), 1, 1, 'C')

        # 5. Stamp (Moved 2cm higher from text)
        if os.path.exists("stamp.png"):
            # x=5 for left alignment, y moved up to 25 to create the gap
            self.image("stamp.png", x=5, y=y_offset + 25, w=65)
        
        # 6. Signature Label
        self.set_xy(5, y_offset + 82)
        self.set_font("Amiri", size=10)
        self.cell(65, 5, ar("توقيع اللجنة الامتحانية"), 0, 1, 'C
