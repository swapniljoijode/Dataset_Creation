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



# —————— Core generation functions (as before) ——————

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
    for year in range(start_year, end_year+1):
        for idx,st in studs.iterrows():
            grade = st.starting_grade
            prev = st.last_pct
            # class
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
                                  "final_pct":pct,"age":age})
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

def upload_df_to_bq(df, project_id, dataset_id, table_name):
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset_id}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

def ensure_bq_dataset(key:str, pid:str, did: str, location: str = "US"):
    """
    Create the dataset if it doesn't already exist.
    """
    client = bigquery.Client.from_service_account_json(key, project=pid)
    # Create dataset if needed
    dataset_ref = f"{pid}.{did}"
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        client.create_dataset(dataset_ref)

def upload_all_to_bq(grade_df, students_df, academic_df, grads_df, term_df,
                     project_id, dataset_id, key):
    client = bigquery.Client.from_service_account_json(key, project=project_id)

    # 1) ensure dataset
    ensure_bq_dataset(key=key,pid=project_id, did=dataset_id)

    # 2) upload each table (truncating any existing)
    def _upload(df, table_name):
        table_ref = f"{project_id}.{dataset_id}.{table_name}"
        job = client.load_table_from_dataframe(
            df,
            table_ref,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        )
        job.result()
        print(f"Uploaded {len(df)} rows to {table_ref}")

    _upload(grade_df,    "grades")
    _upload(students_df, "students")
    _upload(academic_df, "academic")
    _upload(grads_df,    "graduates")
    _upload(term_df,     "terminated")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("School Records Generator")
        self.geometry("500x500")
        self.resizable(False, False)

        style = ttk.Style(self)
        style.theme_use("clam")

        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)

        # Inputs
        ttk.Label(frm, text="How many students (max 850)?").grid(row=0, column=0, sticky="w")
        self.e_students = ttk.Entry(frm); self.e_students.grid(row=0, column=1, pady=4)

        ttk.Label(frm, text="School start year:").grid(row=1, column=0, sticky="w")
        self.e_start = ttk.Entry(frm); self.e_start.grid(row=1, column=1, pady=4)

        ttk.Label(frm, text="Enter 8 subjects (one per line):").grid(
            row=2, column=0, sticky="nw", pady=4)
        self.t_subjects = tk.Text(frm, width=30, height=8); self.t_subjects.grid(row=2, column=1, pady=4)

        # Buttons
        ttk.Button(frm, text="Generate CSVs", command=self.on_generate).grid(
            row=3, column=0, columnspan=2, pady=8, sticky="ew")
        ttk.Button(frm, text="Upload to BigQuery", command=self.on_upload).grid(
            row=4, column=0, columnspan=2, pady=8, sticky="ew")

        self.status = ttk.Label(frm, text="", foreground="#007700")
        self.status.grid(row=5, column=0, columnspan=2)



    def generate_all(self):
        """Run the core pipeline and return all DataFrames."""
        n     = int(self.e_students.get())
        start = int(self.e_start.get())
        subs  = [s.strip() for s in self.t_subjects.get("1.0", tk.END).splitlines() if s.strip()]

        grade_df = generate_grade_table(subs)
        det_df   = generate_student_details(n, start)
        enr_df   = generate_student_enrollment(det_df, start, n)
        students = (enr_df
                    .merge(det_df, on="student_id")
                    .assign(last_pct=None, fail_count=0, terminated=False))
        acad_df, grads_df, term_df = generate_academic_and_events(
            students, grade_df, start, datetime.now().year
        )
        return grade_df, students, acad_df, grads_df, term_df

    def on_generate(self):
        try:
            grade_df, students_df, acad_df, grads_df, term_df = self.generate_all()
            grade_df.to_csv("grades.csv", index=False)
            students_df.drop(columns=["last_pct","fail_count","terminated"])\
                       .to_csv("students.csv", index=False)
            acad_df.to_csv("academic.csv", index=False)
            grads_df.to_csv("graduates.csv", index=False)
            term_df.to_csv("terminated.csv", index=False)
            self.status.config(text="✅ CSVs generated.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_upload(self):

        try:
            dlg = tk.Toplevel(self)
            dlg.title("Upload to BigQuery")
            dlg.geometry("400x180")

            # Use grid for the frame instead of pack
            frm2 = ttk.Frame(dlg, padding=10)
            frm2.grid(row=0, column=0, sticky="nsew")
             # Let the frame expand to fill the dialog
            dlg.grid_rowconfigure(0, weight=1)
            dlg.grid_columnconfigure(0, weight=1)

            # Project ID
            ttk.Label(frm2, text="GCP Project ID:").grid(row=0, column=0, sticky="w")
            proj = ttk.Entry(frm2);
            proj.grid(row=0, column=1, pady=5)

            # Dataset ID
            ttk.Label(frm2, text="Dataset ID:").grid(row=1, column=0, sticky="w")
            ds = ttk.Entry(frm2);
            ds.grid(row=1, column=1, pady=5)

            # Service-account key file
            ttk.Label(frm2, text="Service Account Key:").grid(row=2, column=0, sticky="w")
            key_path = ttk.Entry(frm2, width=30)
            key_path.grid(row=2, column=1, pady=5, sticky="w")

            def browse_key():
                path = filedialog.askopenfilename(
                    title="Select service account JSON",
                    filetypes=[("JSON key", "*.json")]
                )
                if path:
                    key_path.delete(0, tk.END)
                    key_path.insert(0, path)

            ttk.Button(frm2, text="Browse…", command=browse_key) \
                .grid(row=2, column=2, padx=5, pady=5)

            def do_upload():
                pid, did, key = proj.get().strip(), ds.get().strip(), key_path.get().strip()
                if not pid or not did or not key:
                    messagebox.showerror("Error","All fields required")
                    return
                try:
                    """client = bigquery.Client.from_service_account_json(key, project=pid)
                    # Create dataset if needed
                    dataset_ref = f"{pid}.{did}"
                    try:
                        client.get_dataset(dataset_ref)
                    except Exception:
                        client.create_dataset(dataset_ref)"""

                    # regenerate your DataFrames
                    grade_df, students_df, academic_df, grads_df, term_df = self.generate_all()

                    # call our helper
                    ensure_bq_dataset(key=key,pid=pid,did= did)
                    upload_all_to_bq(
                        grade_df, students_df, academic_df, grads_df, term_df,
                        project_id=pid, dataset_id=did, key=key
                    )

                    messagebox.showinfo("Success", f"Tables written to {pid}.{did}")
                    dlg.destroy()
                except Exception as e:
                    messagebox.showerror("Upload Error", str(e))

            ttk.Button(dlg, text="Upload", command=do_upload).grid(
                row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

            dlg.transient(self)
            dlg.grab_set()
            self.wait_window(dlg)
        except Exception as e:
            messagebox.showerror("Error", str(e))
# build window
if __name__ == "__main__":
    App().mainloop()