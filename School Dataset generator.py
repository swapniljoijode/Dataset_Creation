#!/usr/bin/env python3
"""
school_records_generator.py

Auto-installs (and later uninstalls) its dependencies if missing,
then generates:
  • Grade reference table
  • Student enrollment table (using Faker for names, Mimesis for birthdates)
  • 5 years of Academic records with correct promotion, graduation & termination logic

Exports each table to individual CSV files:
  - grades.csv
  - students.csv
  - academic.csv
  - graduates.csv
  - terminated.csv
"""

import sys
import subprocess
import importlib

# —————— 1. DEPENDENCY MANAGEMENT ——————
_dependencies = {
    "pandas":  "pandas",
    "faker":   "Faker",
    "mimesis": "mimesis"
}

_installed_now = []
for module, pkg in _dependencies.items():
    try:
        importlib.import_module(module)
    except ImportError:
        print(f"⚙️ Installing missing dependency '{pkg}'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        _installed_now.append(pkg)

# Now import libraries
import random
from datetime import datetime
import pandas as pd
from faker import Faker
from mimesis import Datetime

fake = Faker()
dt   = Datetime()

# —————— 2. CORE LOGIC ——————

def get_subject_names():
    subjects = []
    print("Enter 8 distinct subject names:")
    while len(subjects) < 8:
        name = input(f"  Subject {len(subjects)+1}/8: ").strip()
        if not name:
            print("    ❌ Cannot be empty.")
        elif name in subjects:
            print("    ❌ Already entered.")
        else:
            subjects.append(name)
    return subjects

def generate_subject_counts():
    return {g: (3 if g <= 3 else random.randint(3, 5)) for g in range(1, 9)}

def generate_grade_table(subjects):
    rows = []
    counts = generate_subject_counts()
    for grade, total in counts.items():
        mandatory = subjects[:3]
        extras    = random.sample(subjects[3:], total - 3) if total > 3 else []
        for subj in mandatory + extras:
            rows.append({"grade": grade, "subject": subj, "min_marks": 0, "max_marks": 100})
    return pd.DataFrame(rows)


def generate_student_details(num_students: int, school_start_year: int) -> pd.DataFrame:
    """
    1) Picks a birthdate in [school_start_year - 10, current_year]
    2) Assigns a unique student_id = birth_year*1000 + seq
    3) Returns student_details_df with columns:
       [student_id, first_name, last_name, birthdate]
    """
    rows = []
    seq = 1
    current_year = datetime.now().year
    uniqueid_multiplier = 0
    earliest_birth = school_start_year - 10
    if num_students >= 100 and num_students <= 1000:
        uniqueid_multiplier = 100
    elif num_students >= 1000 and num_students <= 10000:
        uniqueid_multiplier = 1000


    for _ in range(num_students):
        # 1) pick birthdate
        birthdate = dt.date(start=earliest_birth, end=current_year)
        birth_year = birthdate.year

        # 2) build student_id
        student_id = birth_year * uniqueid_multiplier + seq
        seq += 1

        rows.append({
            "student_id": student_id,
            "first_name": fake.first_name(),
            "last_name":  fake.last_name(),
            "birthdate":  birthdate
        })

    return pd.DataFrame(rows)


def generate_student_enrollment_details(
        student_details_df: pd.DataFrame,
        school_start_year: int,
        num_students: int
) -> pd.DataFrame:
    """
    Builds the enrollment table from student_details_df.

    Columns in student_details_df:
      - student_id     (birth_year*1000 + seq)
      - first_name
      - last_name
      - birthdate      (a datetime.date)

    This function will output student_enrollment_df with:
      - student_id
      - enrollment_id     (enrollment_year*1000 + seq)
      - enrollment_status ('new' or 'transfer-in')
      - enrollment_year
      - starting_grade
    """
    rows = []
    seq = 1
    current_year = datetime.now().year
    uniqueid_multiplier = 0
    if num_students >= 100 and num_students <= 1000:
        uniqueid_multiplier = 100
    elif num_students >= 1000 and num_students <= 10000:
        uniqueid_multiplier = 1000

    for _, st in student_details_df.iterrows():
        birth_year = st["birthdate"].year

        # 1) initial status
        if birth_year < (school_start_year - 2):
            status = "transfer-in"
        else:
            status = random.choice(["new", "transfer-in"])

        # 2) enrollment_year & grade
        if status == "new":
            enrollment_year = birth_year + 2
            enrollment_year = max(enrollment_year, school_start_year)
            grade = 1
        else:
            earliest = max(school_start_year, birth_year + 3)
            latest   = min(current_year, birth_year + 10)
            if earliest <= latest:
                enrollment_year = random.randint(earliest, latest)
            else:
                # fallback to new
                status = "new"
                enrollment_year = max(birth_year + 2, school_start_year)

            age_at_enroll = enrollment_year - birth_year
            grade = max(1, min(age_at_enroll - 2, 8))

        # 3) unique enrollment_id
        enrollment_id = enrollment_year * uniqueid_multiplier + seq
        seq += 1

        rows.append({
            "student_id":        st["student_id"],
            "enrollment_id":     enrollment_id,
            "enrollment_status": status,
            "enrollment_year":   enrollment_year,
            "starting_grade":    grade
        })

    return pd.DataFrame(rows)

def generate_academic_and_events(students_df, grade_df, start_year, end_year):
    academic, graduates, terminated = [], [], []
    students = students_df.copy()

    for year in range(start_year, end_year + 1):
        for idx, st in students.iterrows():
            grade = st.starting_grade
            prev_pct = st.last_pct

            # class assignment
            if prev_pct is None:
                cls = random.choice(["A","B","C","D"])
            elif prev_pct < 30:
                cls = "D"
            elif prev_pct >=90:
                cls = "A"
            elif prev_pct >=70:
                cls = "B"
            elif prev_pct >=55:
                cls = "C"
            else:
                cls = "D"

            # simulate marks & pct
            subs = grade_df[grade_df.grade==grade]
            total_max = subs.max_marks.sum()
            marks = subs.max_marks.apply(lambda m: random.randint(0,m)).tolist()
            pct = round(sum(marks)/total_max*100,2)

            # record
            rec = {
                "academic_year":    year,
                "enrollment_id":    st.enrollment_id,
                "grade":            grade,
                "class":            cls,
                "final_percentage": pct
            }
            for i in range(5):
                rec[f"subject_{i+1}_marks"] = marks[i] if i<len(marks) else None
            academic.append(rec)

            # graduation / failure / termination
            if grade == 8:
                if pct >= 30:
                    age = year - st.birthdate.year
                    graduates.append({
                        "enrollment_id": st.enrollment_id,
                        "first_name":    st.first_name,
                        "last_name":     st.last_name,
                        "final_pct":     pct,
                        "age":           age
                    })
                    students.at[idx, "terminated"] = True
                else:
                    students.at[idx, "fail_count"] += 1
                    students.at[idx, "last_pct"] = pct
                    if students.at[idx, "fail_count"] >= 3:
                        terminated.append({
                            "enrollment_id": st.enrollment_id,
                            "first_name":    st.first_name,
                            "last_name":     st.last_name,
                            "grade":         grade,
                            "academic_year": year,
                            "reason":        f"Failed 3 times in grade {grade}"
                        })
                        students.at[idx, "terminated"] = True
            else:
                if pct >= 30:
                    students.at[idx, "starting_grade"] += 1
                    students.at[idx, "fail_count"] = 0
                    students.at[idx, "last_pct"] = pct
                else:
                    students.at[idx, "fail_count"] += 1
                    students.at[idx, "last_pct"] = pct
                    if students.at[idx, "fail_count"] >= 3:
                        terminated.append({
                            "enrollment_id": st.enrollment_id,
                            "first_name":    st.first_name,
                            "last_name":     st.last_name,
                            "grade":         grade,
                            "academic_year": year,
                            "reason":        f"Failed 3 times in grade {grade}"
                        })
                        students.at[idx, "terminated"] = True

        # drop grads & terminated
        students = students[~students.terminated]

    return pd.DataFrame(academic), pd.DataFrame(graduates), pd.DataFrame(terminated)


def main():
    subjects = get_subject_names()
    grade_df = generate_grade_table(subjects)

    num_students = int(input("How many students (max 850)? ").strip())
    school_start = int(input("School start year (e.g. 2010): ").strip())

    # 1) Details & Enrollment tables
    student_details_df   = generate_student_details(num_students, school_start)
    enrollment_df        = generate_student_enrollment_details(
                                student_details_df, school_start, num_students)
    enrollment_df = enrollment_df[enrollment_df.enrollment_year <= datetime.now().year]

    # 2) Merge + init tracking
    students_df = (
        enrollment_df
        .merge(student_details_df, on="student_id", how="left")
        .assign(
            last_pct   = None,
            fail_count = 0,
            terminated = False
        )
    )

    # 3) Simulate academics
    current_year = datetime.now().year
    academic_df, grads_df, term_df = generate_academic_and_events(
        students_df, grade_df, school_start, current_year
    )

    # 4) Export CSVs
    pd.DataFrame(grade_df).to_csv("grades.csv", index=False)
    students_df.drop(columns=["last_pct","fail_count","terminated"])\
               .to_csv("students.csv", index=False)
    academic_df.to_csv("academic.csv", index=False)
    grads_df.to_csv("graduates.csv", index=False)
    term_df.to_csv("terminated.csv", index=False)

    print("✅ CSVs written: grades, students, academic, graduates, terminated")

if __name__ == "__main__":
    try:
        main()
    finally:
        if _installed_now:
            print("⚙️ Removing installed dependencies:", ", ".join(_installed_now))
            for pkg in _installed_now:
                subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", pkg])

