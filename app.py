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
    return get_display(reshape(str(text)))

# --- Helper: Grading Logic (Numbers to Words) ---
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
        # 1. Background Watermark
        if os.path.exists("watermark.png"):
            self.image("watermark.png", x=60, y=y_offset + 25, w=90)
        
        # 2. Header Logo
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
        id_val = data.get('ت', '---')
        name_val = data.get('اسم الطالب', 'Unknown')
        self.cell(95, 10, ar(f"رقم الطالب: {id_val}"), 0, 0, 'R')
        self.cell(95, 10, ar(f"اسم الطالب: {name_val}"), 0, 1, 'R')

        # 5. Grades Table (Converting Numbers to Words here)
        subjects = [
            ("الرياضيات", data.get("الرياضيات", 0)),
            ("المقاومة", data.get("المقاومة", 0)),
            ("المساحة الهندسية", data.get("المساحة الهندسية", 0)),
            ("الموائع", data.get("الموائع", 0)),
            ("الخرسانة", data.get("الخرسانة", data.get("الخرسانه", 0))),
            ("انشاء المباني", data.get("انشاء المباني", 0))
        ]
        
        self.set_x(20)
        self.set_fill_color(245, 245, 245)
        self.cell(40, 8, ar("عدد المحاولات"), 1, 0, 'C', fill=True)
        self.cell(40,
