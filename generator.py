#!/usr/bin/env python3
import sys
import subprocess
import importlib

# —————— 1. DEPENDENCY MANAGEMENT ——————
_dependencies = {
    "pandas":  "pandas",
    "faker":   "Faker",
    "mimesis": "mimesis",
    "tkinter": "tkinter",
    "google.cloud.bigquery":"google-cloud-bigquery",
    "google.api_core.exceptions":"google.api_core.exceptions",
    "pyarrow":"pyarrow"
}

_installed_now = []
for module, pkg in _dependencies.items():
    try:
        importlib.import_module(module)
    except ImportError:
        print(f"⚙️ Installing missing dependency '{pkg}'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        _installed_now.append(pkg)

import json
import random
import sys
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from faker import Faker
from mimesis import Datetime
from google.cloud import bigquery
from google.api_core.exceptions import Conflict

fake = Faker()
dt   = Datetime()



# —————— Core generation functions  ——————

def generate_subject_counts():
    return {g: (3 if g <= 3 else random.randint(3, 5)) for g in range(1, 9)}

def generate_grade_table(subjects):
    rows = []
    for grade, total in generate_subject_counts().items():
        mandatory = subjects[:3]
        extras    = random.sample(subjects[3:], total - 3)
        for subj in mandatory + extras:
            rows.append({"grade":grade,"subject":subj,"min_marks":0,"max_marks":100})
    return pd.DataFrame(rows)

def generate_student_details(n, school_start):
    rows, seq = [], 1
    current = datetime.now().year
    earliest = school_start - 10
    mult = 1000 if n>=1000 else 100
    for _ in range(n):
        bd = dt.date(start=earliest,end=current-2)  # never born <2 years ago
        yr = bd.year
        sid = yr*mult + seq; seq+=1
        rows.append({"student_id":sid,
                     "first_name":fake.first_name(),
                     "last_name": fake.last_name(),
                     "birthdate": bd})
    return pd.DataFrame(rows)

def generate_student_enrollment(student_details_df, school_start, n):
    rows, seq = [], 1
    current = datetime.now().year
    mult = 1000 if n>=1000 else 100
    for _,st in student_details_df.iterrows():
        by = st.birthdate.year
        if by < (school_start-2):
            status="transfer-in"
        else:
            status=random.choice(["new","transfer-in"])
        if status=="new":
            ey = max(by+2, school_start)
            grade=1
        else:
            e_min = max(school_start, by+3)
            e_max = min(current, by+10)
            if e_min<=e_max:
                ey = random.randint(e_min,e_max)
            else:
                status="new"; ey=max(by+2,school_start); grade=1
            age=ey-by; grade=max(1,min(age-2,8))
        eid = ey*mult + seq; seq+=1
        rows.append({"student_id":st.student_id,
                     "enrollment_id":eid,
                     "enrollment_status":status,
                     "enrollment_year":ey,
                     "starting_grade":grade})
    return pd.DataFrame(rows)

def generate_academic_and_events(students_df, grade_df, start_year, end_year):
    academic,grads,term = [],[],[]
    studs = students_df.copy()
    for year in range(start_year, end_year + 1):
        for idx, st in studs.iterrows():
            grade = st["starting_grade"]
            prev = st["last_pct"]
            enrol_id = st["enrollment_id"]
            if st["enrollment_year"] > year:
                continue
            else:
                # class
                enrol_id+=1
                if prev is None: cls=random.choice(["A","B","C","D"])
                elif prev<30:    cls="D"
                elif prev>=90:   cls="A"
                elif prev>=70:   cls="B"
                elif prev>=55:   cls="C"
                else:            cls="D"
                # simulate marks
                subs=grade_df[grade_df.grade==grade]
                msum=subs.max_marks.sum()
                marks=subs.max_marks.apply(lambda m: random.randint(0,m)).tolist()
                pct=round(sum(marks)/msum*100,2)
                # record
                rec={"academic_year":year,"enrollment_id":st.enrollment_id,
                     "grade":grade,"class":cls,"final_percentage":pct}
                for i in range(5):
                    rec[f"subject_{i+1}_marks"]=marks[i] if i<len(marks) else None
                academic.append(rec)
                # grad/fail/term
                if grade==8:
                    if pct>=30:
                        age=year-st.birthdate.year
                        grads.append({"enrollment_id":st.enrollment_id,
                                      "first_name":st.first_name,
                                      "last_name":st.last_name,
                                      "final_pct":pct,
                                      "age":age,
                                      "Graduation Year": year+1})
                        studs.at[idx,"terminated"]=True
                    else:
                        studs.at[idx,"fail_count"]+=1
                        studs.at[idx,"last_pct"]=pct
                        if studs.at[idx,"fail_count"]>=3:
                            term.append({"enrollment_id":st.enrollment_id,
                                         "first_name":st.first_name,
                                         "last_name":st.last_name,
                                         "grade":grade,"academic_year":year,
                                         "reason":f"Failed 3× in grade {grade}"})
                            studs.at[idx,"terminated"]=True
                else:
                    if pct>=30:
                        studs.at[idx,"starting_grade"]+=1
                        studs.at[idx,"fail_count"]=0
                        studs.at[idx,"last_pct"]=pct
                    else:
                        studs.at[idx,"fail_count"]+=1
                        studs.at[idx,"last_pct"]=pct
                        if studs.at[idx,"fail_count"]>=3:
                            term.append({"enrollment_id":st.enrollment_id,
                                         "first_name":st.first_name,
                                         "last_name":st.last_name,
                                         "grade":grade,"academic_year":year,
                                         "reason":f"Failed 3× in grade {grade}"})
                            studs.at[idx,"terminated"]=True
        studs=studs[~studs.terminated]
    return (pd.DataFrame(academic),
            pd.DataFrame(grads),
            pd.DataFrame(term))
