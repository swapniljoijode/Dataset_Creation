# !/usr/bin/env python3
"""
grade_table_generator.py

1. Ask the user for 5 subject names.
2. Randomly decide total subjects per grade:
     - Grades 1–3 → exactly 3 subjects
     - Grades 4–8 → randint(3, 5)
3. For each grade:
     - First 3 subjects are treated as “mandatory”
     - Any extra slots are filled by randomly sampling from the remaining 2 subjects
4. Outputs a pandas.DataFrame with columns [grade, subject, min_marks, max_marks]
"""

import random
from datetime import date
import pandas as pd
from faker import Faker
from mimesis import Datetime

# Initialize libraries
fake = Faker()
dt = Datetime()


def get_subject_names():
    """Prompt the user to enter exactly 5 distinct subject names."""
    subjects = []
    print("Enter the names of 5 subjects (e.g. Mathematics, English, ...):")
    while len(subjects) < 5:
        name = input(f"  Subject {len(subjects) + 1}/5: ").strip()
        if not name:
            print("    ❌ Name cannot be empty.")
        elif name in subjects:
            print("    ❌ You've already entered that.")
        else:
            subjects.append(name)
    return subjects


def generate_subject_counts():
    """
    Build a dict mapping grade → total subject count.
      grades 1–3 → 3
      grades 4–8 → random int between 3 and 5
    """
    counts = {}
    for g in range(1, 9):
        counts[g] = 3 if g <= 3 else random.randint(3, 5)
    return counts


def generate_grade_table(subjects):
    """
    Constructs the Grade table.

    Args:
        subjects (list of str): Exactly 5 user‐provided subject names.

    Returns:
        pandas.DataFrame: columns = [grade, subject, min_marks, max_marks]
    """
    counts = generate_subject_counts()
    records = []

    for grade, total in counts.items():
        # first 3 are mandatory
        mandatory = subjects[:3]
        # extras come from the last 2 subjects
        optional_slots = total - len(mandatory)
        optionals = []
        if optional_slots > 0:
            optionals = random.sample(subjects[3:], optional_slots)

        for subj in mandatory + optionals:
            records.append({
                "grade": grade,
                "subject": subj,
                "min_marks": 0,
                "max_marks": 100
            })

    return pd.DataFrame(records)


# !/usr/bin/env python3
"""
academic_dataset_generator.py

Generates:
  • Student Table
  • Academic Table
for one academic year, based on your rules.
"""


def generate_student_table(num_students, start_year):
    rows = []
    seq = 1
    for _ in range(num_students):
        status = random.choice(["new", "transfer-in"])
        grade  = 1 if status == "new" else random.randint(1, 8)
        age    = grade + 2
        birth  = fake.date_of_birth(minimum_age=age, maximum_age=age)
        eid    = start_year * 1000 + seq
        seq   += 1
        rows.append({
            "enrollment_id":     eid,
            "first_name":        fake.first_name(),
            "last_name":         fake.last_name(),
            "birthdate":         birth,
            "enrollment_year":   start_year,
            "enrollment_status": status,
            "current_grade":     grade,
            "last_pct":          None   # placeholder for chaining
        })
    return pd.DataFrame(rows)

def generate_academic_table_multi(student_df, grade_df, start_year, num_years=5):
    records = []
    students = student_df.copy()

    for year in range(start_year, start_year + num_years):
        for idx, st in students.iterrows():
            grade    = st["current_grade"]
            prev_pct = st["last_pct"]

            # Class placement for this year:
            if prev_pct is None:
                cls = random.choice(["A","B","C","D"])
            elif prev_pct < 30:
                cls = "D"
            elif prev_pct >= 90:
                cls = "A"
            elif prev_pct >= 70:
                cls = "B"
            elif prev_pct >= 55:
                cls = "C"
            else:
                cls = "D"

            # Generate this year's marks & percentage:
            subs      = grade_df[grade_df.grade == grade]
            max_total = subs["max_marks"].sum()
            marks     = subs["max_marks"].apply(lambda m: random.randint(0, m)).tolist()
            pct       = round(sum(marks) / max_total * 100, 2)

            # Build record:
            row = {
                "academic_year":    year,
                "enrollment_id":    st["enrollment_id"],
                "grade":            grade,
                "class":            cls,
                "final_percentage": pct
            }
            # up to 5 subject columns
            for i in range(5):
                row[f"subject_{i+1}_marks"] = marks[i] if i < len(marks) else None

            records.append(row)

            # Prepare for next year:
            students.at[idx, "last_pct"] = pct
            if pct >= 30 and grade < 8:
                students.at[idx, "current_grade"] += 1
            # if pct < 30, grade stays the same (and next year class= D per above)

    return pd.DataFrame(records)


if __name__ == "__main__":
    # 1) Subjects & Grade Table
    subj_list = get_subject_names()
    grade_df = generate_grade_table(subj_list)

    # 2) Student enrollment settings
    num_students = int(input("How many students (max 850)? ").strip())
    start_year = int(input("Start academic year (e.g. 2025): ").strip())

    # 3) Generate tables
    student_df = generate_student_table(num_students, start_year)
    academic_df = generate_academic_table_multi(student_df, grade_df, start_year, num_years=5)

    # 4) Export to Excel
    grade_df.to_csv("grades.csv", index=False)
    student_df.to_csv("students.csv", index=False)
    academic_df.to_csv("academic.csv", index=False)

    #print("✅ school_records.xlsx generated with Grades, Students, and Academic sheets.")


