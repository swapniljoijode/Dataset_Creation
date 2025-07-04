# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from generator import (
    generate_grade_table,
    generate_student_details,
    generate_student_enrollment,
    generate_academic_and_events
)
from bigquery_loader import upload_all_to_bq
import pandas as pd
from datetime import datetime

class SchoolRecordsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("School Records Generator")
        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=20); frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="How many students?").grid(row=0, column=0, sticky="w")
        self.e_students = ttk.Entry(frm); self.e_students.grid(row=0, column=1)

        ttk.Label(frm, text="School start year:").grid(row=1, column=0, sticky="w")
        self.e_start = ttk.Entry(frm); self.e_start.grid(row=1, column=1)

        ttk.Label(frm, text="Subjects (one per line):")\
            .grid(row=2, column=0, sticky="nw")
        self.t_subs = tk.Text(frm, width=30, height=8)
        self.t_subs.grid(row=2, column=1)

        ttk.Button(frm, text="Generate CSVs", command=self._generate_csvs)\
            .grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

        ttk.Button(frm, text="Upload to BigQuery", command=self._open_upload_dialog)\
            .grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")

        self.status = ttk.Label(frm, text="", foreground="green")
        self.status.grid(row=5, column=0, columnspan=2)

    def _generate_csvs(self):
        try:
            dfs = self._make_all_dfs()
            names = ["grades","students","academic","graduates","terminated"]
            for df, nm in zip(dfs, names):
                df.to_csv(f"{nm}.csv", index=False)
            self.status.config(text="✅ CSVs generated.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_upload_dialog(self):
        dlg = tk.Toplevel(self); dlg.title("Upload to BigQuery")
        frm2 = ttk.Frame(dlg, padding=10); frm2.pack(fill="both", expand=True)

        ttk.Label(frm2, text="Project ID:").grid(row=0, column=0)
        pid = ttk.Entry(frm2); pid.grid(row=0, column=1)

        ttk.Label(frm2, text="Dataset ID:").grid(row=1, column=0)
        did = ttk.Entry(frm2); did.grid(row=1, column=1)

        ttk.Label(frm2, text="Key JSON:").grid(row=2, column=0)
        key = ttk.Entry(frm2, width=30); key.grid(row=2, column=1, sticky="w")
        ttk.Button(frm2, text="Browse…", command=lambda: _browse(key))\
            .grid(row=2, column=2)

        def _browse(entry):
            p = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
            if p: entry.delete(0,tk.END); entry.insert(0,p)

        def _do_upload():
            try:
                dfs = self._make_all_dfs()
                upload_all_to_bq(*dfs, key=key.get().strip(),project_id= pid.get().strip(),dataset_id= did.get().strip())
                messagebox.showinfo("Success", "Uploaded!")
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Upload Error", str(e))

        ttk.Button(frm2, text="Upload", command=_do_upload)\
            .grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

    def _make_all_dfs(self):
        n     = int(self.e_students.get())
        start = int(self.e_start.get())
        subs  = [s.strip() for s in self.t_subs.get("1.0",tk.END).splitlines() if s.strip()]
        grade_df = generate_grade_table(subs)
        det_df   = generate_student_details(n, start)
        enr_df   = generate_student_enrollment(det_df, start, n)
        students = enr_df.merge(det_df, on="student_id")\
                         .assign(last_pct=None, fail_count=0, terminated=False)
        acad, grads, term = generate_academic_and_events(students, grade_df, start, datetime.now().year)
        return grade_df, students, acad, grads, term
