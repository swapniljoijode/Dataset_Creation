#!/usr/bin/env python3
"""
school_records_generator.py – ENHANCED VERSION WITH SEMESTER LOGIC
Using proven distribution logic + semester-wise scoring with mandatory subjects

NEW SEMESTER FEATURES:
• Semester-wise subject distribution with mandatory subjects
• Conditional semester 2 scoring based on semester 1 performance
• Academic year score calculation based on semester performance rules
• Enhanced academic records with semester details
"""

# ── 1. DEPENDENCY MANAGEMENT ──────────────────────────────────────────
import sys, subprocess, importlib, random, collections, os
from datetime import datetime

_DEPENDENCIES = {"pandas": "pandas", "faker": "Faker", "mimesis": "mimesis"}
_INSTALLED_NOW = []
for mod, pkg in _DEPENDENCIES.items():
    try:
        importlib.import_module(mod)
    except ImportError:
        print(f"⚙️  Installing missing dependency {pkg}…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        _INSTALLED_NOW.append(pkg)

import pandas as pd
from faker import Faker
from mimesis import Datetime

fake, dt = Faker(), Datetime()


# ── 2. ENHANCED SUBJECT MANAGEMENT WITH MANDATORY SUBJECTS ──────────
def get_subject_names_with_mandatory() -> tuple[list[str], list[str]]:
    """Get all subjects and identify mandatory ones"""
    subjects = []
    tot_subjects = int(input("Enter total number of subjects taught in school: "))
    print(f"Enter {tot_subjects} distinct subject names:")
    while len(subjects) < tot_subjects:
        name = input(f"  Subject {len(subjects) + 1}/{tot_subjects}: ").strip()
        if not name:
            print("    ❌ Cannot be empty.")
        elif name in subjects:
            print("    ❌ Already entered.")
        else:
            subjects.append(name)

    print(f"\nFrom the {tot_subjects} subjects, select 3 mandatory subjects:")
    mandatory_subjects = []
    for i in range(3):
        while True:
            print(f"Available subjects: {[s for s in subjects if s not in mandatory_subjects]}")
            choice = input(f"Mandatory subject {i + 1}/3: ").strip()
            if choice in subjects and choice not in mandatory_subjects:
                mandatory_subjects.append(choice)
                break
            else:
                print("❌ Invalid choice or already selected.")

    return subjects, mandatory_subjects


def generate_semester_grade_table(all_subjects: list[str], mandatory_subjects: list[str],
                                  total_grades: int) -> pd.DataFrame:
    """Generate semester-wise subject table with mandatory subjects"""
    rows = []
    for grade in range(1, total_grades + 1):
        for semester in [1, 2]:
            # All grades have mandatory subjects
            semester_subjects = mandatory_subjects.copy()

            # Grades 4+ get additional subjects
            if grade >= 4:
                additional_count = random.randint(1, 2)
                available_additional = [s for s in all_subjects if s not in mandatory_subjects]
                if available_additional:
                    additional_subjects = random.sample(available_additional,
                                                        min(additional_count, len(available_additional)))
                    semester_subjects.extend(additional_subjects)

            for subject in semester_subjects:
                rows.append({
                    "grade": grade,
                    "semester": semester,
                    "subject": subject,
                    "is_mandatory": subject in mandatory_subjects,
                    "min_marks": 0,
                    "max_marks": 100
                })
    return pd.DataFrame(rows)


# ── 3. PROVEN UTILITIES (UNCHANGED) ──────────────────────────────────
def calculate_student_distribution(total_students: int, total_grades: int,
                                   total_classes: int) -> tuple[int, int]:
    if total_students % total_grades:
        raise ValueError("Total students must be divisible by number of grades")
    per_grade = total_students // total_grades
    if per_grade % total_classes:
        raise ValueError("Students per grade must be divisible by number of classes")
    return per_grade, per_grade // total_classes


def safe_csv_save(df: pd.DataFrame, filename: str, retries: int = 3) -> None:
    for attempt in range(retries):
        try:
            df.to_csv(filename, index=False)
            print(f"   ✅ {filename} saved successfully")
            return
        except PermissionError:
            print(f"❌ Close {filename} and press Enter to retry ({retries - attempt - 1} attempts left)…")
            input()
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
            return
    print(f"⚠️  Skipped saving {filename} after {retries} failed attempts")


def get_performance_class(percentage: float) -> str:
    """Get class based on performance"""
    if percentage >= 90:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 55:
        return "C"
    else:
        return "D"


def can_move_to_class(percentage: float, target_class: str) -> bool:
    """Check if student with given percentage can be moved to target class"""
    if target_class == "A":
        return percentage >= 30
    elif target_class == "B":
        return percentage >= 30 and percentage < 90
    elif target_class == "C":
        return percentage >= 30 and percentage < 70
    elif target_class == "D":
        return percentage < 55
    return False


def balance_class_distribution(students_in_grade: pd.DataFrame, target_per_class: int,
                               class_labels: list) -> pd.DataFrame:
    """
    PROVEN: Balance class distribution maintaining equal numbers per class
    while respecting performance constraints and using alphabetical ordering
    """
    students = students_in_grade.copy()

    # Step 1: Initial performance-based assignment
    for idx, student in students.iterrows():
        academic_pct = student.get('academic_year_percentage', student.get('last_pct', 50))
        performance_class = get_performance_class(academic_pct)
        students.at[idx, 'curr_class'] = performance_class

    # Step 2: Balance classes using alphabetical ordering
    for target_class in class_labels:
        current_count = len(students[students['curr_class'] == target_class])
        needed = target_per_class - current_count

        if needed > 0:
            eligible_students = []
            class_hierarchy = {"A": 4, "B": 3, "C": 2, "D": 1}

            for idx, student in students.iterrows():
                curr_class = student['curr_class']
                academic_pct = student.get('academic_year_percentage', student.get('last_pct', 50))

                if curr_class == target_class:
                    continue

                if can_move_to_class(academic_pct, target_class):
                    if class_hierarchy.get(target_class, 0) > class_hierarchy.get(curr_class, 0):
                        full_name = f"{student['first_name']} {student['last_name']}"
                        eligible_students.append((idx, full_name, academic_pct))

            # Sort alphabetically and move
            eligible_students.sort(key=lambda x: x[1].lower())
            moved = 0
            for idx, full_name, pct in eligible_students:
                if moved >= needed:
                    break
                students.at[idx, 'curr_class'] = target_class
                moved += 1

    return students


# ── 4. PROVEN STUDENT GENERATION (UNCHANGED) ────────────────────────
def generate_student_details(n: int, school_start: int) -> pd.DataFrame:
    uid_mult = 1000 if n < 1000 else 10000
    yoy_seq, rows = collections.defaultdict(int), []
    for _ in range(n):
        birthdate = dt.date(start=school_start - 10, end=datetime.now().year)
        year = birthdate.year
        yoy_seq[year] += 1
        student_id = year * uid_mult + yoy_seq[year]
        rows.append(
            {"student_id": student_id,
             "first_name": fake.first_name(),
             "last_name": fake.last_name(),
             "birthdate": birthdate}
        )
    return pd.DataFrame(rows)


def generate_initial_student_enrollment(details_df: pd.DataFrame,
                                        school_start: int,
                                        total: int,
                                        grades: int = 8,
                                        classes: int = 4) -> pd.DataFrame:
    per_grade, per_class = calculate_student_distribution(total, grades, classes)
    class_labels = ["A", "B", "C", "D"][:classes]

    uid_mult = 1000 if total < 1000 else 10000
    seq_by_year = collections.defaultdict(int)
    rows, idx = [], 0

    for grade in range(1, grades + 1):
        for cls in class_labels:
            for _ in range(per_class):
                base = details_df.iloc[idx]
                idx += 1

                if grade == 1:
                    status = random.choice(["new", "transfer-in"])
                    birth_year = school_start - 2 if status == "new" else school_start - 3
                else:
                    status = "transfer-in"
                    birth_year = school_start - (grade + 2)

                birthdate = datetime(
                    birth_year, random.randint(1, 12), random.randint(1, 28)
                ).date()
                details_df.at[base.name, "birthdate"] = birthdate

                seq_by_year[school_start] += 1
                enrol_id = school_start * uid_mult + seq_by_year[school_start]

                rows.append(
                    {"student_id": base.student_id,
                     "enrollment_id": enrol_id,
                     "enrollment_status": status,
                     "enrollment_year": school_start,
                     "starting_grade": grade,
                     "starting_class": cls}
                )
    return pd.DataFrame(rows)


def add_new_students(required: int, year: int, classes: int = 4) -> pd.DataFrame:
    """ENHANCED: Add new students with balanced class distribution"""
    if required == 0:
        return pd.DataFrame()

    rows, uid0 = [], year * 10000 + 9000
    class_labels = ["A", "B", "C", "D"][:classes]

    # Distribute evenly across classes
    per_class = required // classes
    remainder = required % classes

    counter = 0
    for i, cls in enumerate(class_labels):
        class_count = per_class + (1 if i < remainder else 0)
        for _ in range(class_count):
            counter += 1
            sid = uid0 + counter
            rows.append(
                {"student_id": sid,
                 "enrollment_id": sid,
                 "first_name": fake.first_name(),
                 "last_name": fake.last_name(),
                 "birthdate": datetime(year - 2, random.randint(1, 12),
                                       random.randint(1, 28)).date(),
                 "enrollment_status": "new",
                 "enrollment_year": year,
                 "starting_grade": 1,
                 "starting_class": cls}
            )

    return pd.DataFrame(rows)


# ── 5. ENHANCED ACADEMIC SIMULATION WITH SEMESTER LOGIC ────────────
def generate_semester_performance(grade: int, semester: int, grade_df: pd.DataFrame) -> tuple[
    list[str], list[int], float]:
    """Generate performance for a specific semester"""
    semester_subjects = grade_df[
        (grade_df.grade == grade) & (grade_df.semester == semester)
        ]['subject'].tolist()

    if not semester_subjects:
        # Fallback if no subjects found
        semester_subjects = ["Subject1", "Subject2", "Subject3"]

    # Generate marks for each subject
    marks = []
    for _ in semester_subjects:
        # Realistic mark generation with some failing students
        if random.random() < 0.75:  # 75% chance of decent performance
            mark = random.randint(30, 100)
        else:  # 25% chance of poor performance
            mark = random.randint(0, 29)
        marks.append(mark)

    # Calculate semester percentage
    semester_percentage = sum(marks) / len(marks) if marks else 0

    return semester_subjects, marks, round(semester_percentage, 2)


def calculate_academic_year_score(sem1_percentage: float, sem2_percentage: float = None) -> float:
    """
    Calculate academic year score based on semester performance rules:
    - If sem1 < 30%, academic score = sem1 score
    - If sem1 >= 30% and sem2 < 30%, academic score = sem2 score
    - If both >= 30%, academic score = average of both
    """
    if sem1_percentage < 30:
        return sem1_percentage
    elif sem2_percentage is None:
        return sem1_percentage
    elif sem2_percentage < 30:
        return sem2_percentage
    else:
        return round((sem1_percentage + sem2_percentage) / 2, 2)


def generate_enhanced_academics(students_df: pd.DataFrame, grade_df: pd.DataFrame,
                                start_year: int, end_year: int,
                                total_pop: int, per_grade: int, per_class: int,
                                grades: int = 8, classes: int = 4):
    """Enhanced academic simulation with semester logic"""

    academic_records = []
    graduates = []
    terminated = []
    students = students_df.copy()

    # Initialize tracking fields
    students["academic_year_percentage"] = None
    students["semester1_percentage"] = None
    students["semester2_percentage"] = None
    students["fail_count"] = 0
    students["terminated"] = False
    students["curr_class"] = students["starting_class"]

    class_labels = ["A", "B", "C", "D"][:classes]

    for year in range(start_year, end_year + 1):
        active = students[~students.terminated]
        print(f"\n📅 Year {year}: {len(active)} active students")

        # Process semester-wise academics
        semester_data = {}

        for idx, student in students.iterrows():
            if student.terminated:
                continue

            student_id = student.enrollment_id
            grade = student.starting_grade

            # SEMESTER 1
            print(f"  📚 Processing Semester 1 for Grade {grade}")
            sem1_subjects, sem1_marks, sem1_pct = generate_semester_performance(grade, 1, grade_df)
            students.at[idx, "semester1_percentage"] = sem1_pct

            # SEMESTER 2 - Only if Semester 1 >= 30%
            sem2_subjects, sem2_marks, sem2_pct = [], [], None
            if sem1_pct >= 30:
                print(f"  📚 Processing Semester 2 for Grade {grade} (Sem1: {sem1_pct}%)")
                sem2_subjects, sem2_marks, sem2_pct = generate_semester_performance(grade, 2, grade_df)
                students.at[idx, "semester2_percentage"] = sem2_pct
            else:
                print(f"  ❌ Skipping Semester 2 for Grade {grade} (Sem1: {sem1_pct}% < 30%)")
                students.at[idx, "semester2_percentage"] = None

            # Calculate academic year score based on rules
            academic_year_score = calculate_academic_year_score(sem1_pct, sem2_pct)
            students.at[idx, "academic_year_percentage"] = academic_year_score

            # Store semester data for record generation
            semester_data[student_id] = {
                'sem1_subjects': sem1_subjects,
                'sem1_marks': sem1_marks,
                'sem1_percentage': sem1_pct,
                'sem2_subjects': sem2_subjects,
                'sem2_marks': sem2_marks,
                'sem2_percentage': sem2_pct,
                'academic_year_percentage': academic_year_score
            }

        # Balance class distributions based on academic year scores
        print(f"  🎯 Balancing class distributions...")
        for current_grade in range(1, grades + 1):
            grade_students = students[
                (~students.terminated) &
                (students.starting_grade == current_grade)
                ]

            if len(grade_students) > 0:
                print(f"    Grade {current_grade}: Balancing {len(grade_students)} students")
                balanced_students = balance_class_distribution(
                    grade_students, per_class, class_labels
                )

                # Update the main dataframe with balanced classes
                for idx in balanced_students.index:
                    students.at[idx, 'curr_class'] = balanced_students.at[idx, 'curr_class']

        # Generate comprehensive academic records
        for idx, student in students.iterrows():
            if student.terminated:
                continue

            student_id = student.enrollment_id
            grade = student.starting_grade
            class_assigned = student.curr_class
            data = semester_data.get(student_id, {})

            # Create comprehensive academic record
            record = {
                "academic_year": year,
                "enrollment_id": student_id,
                "grade_current": grade,
                "class_current": class_assigned,

                # Semester 1 details
                "Sem 1 Subjects": "; ".join(data.get('sem1_subjects', [])),
                "Sem 1 Scores": "; ".join(map(str, data.get('sem1_marks', []))),
                "Sem 1 Percentage": data.get('sem1_percentage', 0),
                "Active backlogs until sem 1": 0,  # Simplified for now
                "cleared backlogs in Sem 1": 0,

                # Semester 2 details
                "Sem 2 subjects": "; ".join(data.get('sem2_subjects', [])),
                "Sem 2 Scores": "; ".join(map(str, data.get('sem2_marks', []))),
                "Sem 2 Percentage": data.get('sem2_percentage') if data.get('sem2_percentage') is not None else 0,
                "Active backlogs until sem 2": 0,  # Simplified for now
                "cleared backlogs in Sem 2": 0,

                # Academic year summary
                "Total Weighted percentage in current academic year": data.get('academic_year_percentage', 0),
                "Next year projected grade": grade + 1 if data.get('academic_year_percentage',
                                                                   0) >= 30 and grade < grades else grade,
                "Next year projected class": get_performance_class(data.get('academic_year_percentage', 0))
            }

            academic_records.append(record)

        # Handle progression/graduation/termination based on academic year scores
        leavers = 0
        for idx, student in students.iterrows():
            if student.terminated:
                continue

            student_id = student.enrollment_id
            grade = student.starting_grade
            academic_pct = student.academic_year_percentage

            # Progression logic based on academic year percentage
            if grade == grades:  # Final grade
                if academic_pct >= 30:  # Graduate
                    graduates.append({
                        "enrollment_id": student_id,
                        "first_name": student.first_name,
                        "last_name": student.last_name,
                        "final_pct": academic_pct,
                        "age": year - student.birthdate.year,
                        "graduation_year": year
                    })
                    students.at[idx, "terminated"] = True
                    leavers += 1
                else:  # Failed final grade
                    students.at[idx, "fail_count"] += 1
                    # Set class to D for failed students
                    students.at[idx, "curr_class"] = "D"
                    if students.at[idx, "fail_count"] >= 3:
                        terminated.append({
                            "enrollment_id": student_id,
                            "first_name": student.first_name,
                            "last_name": student.last_name,
                            "grade": grade,
                            "academic_year": year,
                            "reason": f"Failed 3× in Grade {grade}"
                        })
                        students.at[idx, "terminated"] = True
                        leavers += 1
            else:  # Grades 1 to (final-1)
                if academic_pct >= 30:  # Promote
                    students.at[idx, "starting_grade"] += 1
                    students.at[idx, "fail_count"] = 0
                else:  # Repeat grade in class D
                    students.at[idx, "fail_count"] += 1
                    students.at[idx, "curr_class"] = "D"  # Failed students go to D class
                    if students.at[idx, "fail_count"] >= 3:
                        terminated.append({
                            "enrollment_id": student_id,
                            "first_name": student.first_name,
                            "last_name": student.last_name,
                            "grade": grade,
                            "academic_year": year,
                            "reason": f"Failed 3× in Grade {grade}"
                        })
                        students.at[idx, "terminated"] = True
                        leavers += 1

        # Maintain population with balanced new students
        if leavers and year < end_year:
            print(f"   📈 Adding {leavers} new Grade 1 students with balanced distribution")
            new_students = add_new_students(leavers, year + 1, classes)
            if not new_students.empty:
                new_students[["academic_year_percentage", "semester1_percentage", "semester2_percentage", "fail_count",
                              "terminated"]] = [None, None, None, 0, False]
                new_students["curr_class"] = new_students["starting_class"]
                students = pd.concat([students, new_students], ignore_index=True)

        print(f"   📊 {leavers} students left, {len(graduates)} total graduates")

    return (pd.DataFrame(academic_records),
            pd.DataFrame(graduates),
            pd.DataFrame(terminated),
            students[["student_id", "first_name", "last_name", "birthdate"]].drop_duplicates())


# ── 6. MAIN FUNCTION ─────────────────────────────────────────────────
def main():
    print("🏫 ENHANCED SCHOOL RECORDS GENERATOR")
    print("🎯 Using PROVEN distribution logic + SEMESTER scoring system")
    print("=" * 60)

    while True:
        try:
            total = int(input("Total students: ").strip())
            grades = int(input("Number of grades (default 8): ").strip() or "8")
            classes = int(input("Classes per grade (default 4): ").strip() or "4")
            per_grade, per_class = calculate_student_distribution(total, grades, classes)
            print(f"✅ Distribution: {per_grade} students per grade, {per_class} students per class")
            break
        except ValueError as e:
            print(f"❌ {e} – please re-enter.")

    # Get subjects with mandatory selection
    all_subjects, mandatory_subjects = get_subject_names_with_mandatory()
    print(f"✅ Mandatory subjects: {mandatory_subjects}")

    # Generate semester-wise grade table
    grade_df = generate_semester_grade_table(all_subjects, mandatory_subjects, grades)
    print(f"✅ Generated semester-wise subject distribution")
    print(f"   Grades 1-3: {len(mandatory_subjects)} mandatory subjects per semester")
    print(f"   Grade 4+: {len(mandatory_subjects)} mandatory + 1-2 additional subjects per semester")

    school_start = int(input("School start year (e.g. 2010): ").strip())
    current_year = datetime.now().year

    print(f"\n🔄 Generating enhanced school system...")
    print("📝 Creating student details...")
    details_df = generate_student_details(total, school_start)

    print("📝 Creating enrollment records...")
    enrol_df = generate_initial_student_enrollment(details_df,
                                                   school_start, total,
                                                   grades, classes)
    students_df = enrol_df.merge(details_df, on="student_id", how="left")

    print("📚 Running enhanced semester-based academic simulation...")
    academic_df, grads_df, term_df, all_students = generate_enhanced_academics(
        students_df, grade_df, school_start, current_year,
        total, per_grade, per_class, grades, classes
    )

    print("\n💾 Saving enhanced CSV files…")
    safe_csv_save(grade_df, "grades.csv")
    safe_csv_save(all_students, "students.csv")
    safe_csv_save(academic_df, "academic_records.csv")
    safe_csv_save(grads_df, "graduates.csv")
    safe_csv_save(term_df, "terminated.csv")

    print("\n✅ Enhanced generation complete!")
    print(f"   Students records  : {len(all_students):>6}")
    print(f"   Academic records  : {len(academic_df):>6}")
    print(f"   Graduates         : {len(grads_df):>6}")
    print(f"   Terminated        : {len(term_df):>6}")

    print(f"\n🎯 NEW SEMESTER FEATURES:")
    print(f"   ✅ Mandatory subjects for all grades")
    print(f"   ✅ Semester-wise subject distribution")
    print(f"   ✅ Conditional Semester 2 scoring (only if Sem 1 >= 30%)")
    print(f"   ✅ Smart academic year score calculation")
    print(f"   ✅ Class assignment based on academic performance")
    print(f"   ✅ Failed students automatically assigned to Class D")
    print(f"   ✅ Comprehensive academic records with semester details")


if __name__ == "__main__":
    try:
        main()
    finally:
        if _INSTALLED_NOW:
            print("⚙️  Removing installed dependencies:", ", ".join(_INSTALLED_NOW))
            for pkg in _INSTALLED_NOW:
                subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", pkg])
