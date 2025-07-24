# FINAL FULL VERSION OF STUDENT GRADING APP WITH ALL FEATURES
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk
import sqlite3
import csv
import re
import datetime

# --- Database Setup ---
conn = sqlite3.connect('student_grading.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS students (
    rocket_id TEXT PRIMARY KEY,
    name TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS classes (
    class_id TEXT PRIMARY KEY,
    class_name TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    due_date TEXT,
    max_score INTEGER,
    type TEXT,
    class_id TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS grades (
    rocket_id TEXT,
    assignment_id INTEGER,
    score INTEGER,
    class_id TEXT
)''')

conn.commit()

GRADE_SCALE = [
    (93, 'A', 4.0), (90, 'A-', 3.7), (87, 'B+', 3.3), (83, 'B', 3.0), (80, 'B-', 2.7),
    (77, 'C+', 2.3), (73, 'C', 2.0), (70, 'C-', 1.7), (67, 'D+', 1.3), (63, 'D', 1.0),
    (60, 'D-', 0.7), (0, 'F', 0.0)
]

def calculate_letter_grade(score):
    for min_score, letter, gpa in GRADE_SCALE:
        if score >= min_score:
            return letter, gpa
    return 'F', 0.0

class StudentGradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Grading App")
        self.root.geometry("1080x650")
        self.nav_stack = []
        self.current_class_id = None

        self.log_area = tk.Text(root, width=45, height=30, bg="#f4f4f4", state='disabled')
        self.log_area.pack(side='right', padx=10, pady=10)

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(side='left', fill='both', expand=True)

        self.homepage()

    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"{datetime.datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.render_nav_buttons()

    def render_nav_buttons(self):
        nav_frame = tk.Frame(self.main_frame)
        nav_frame.pack(side='bottom', fill='x', pady=5)
        tk.Button(nav_frame, text="🏠 Home", width=15, command=self.home_button_action).pack(side='left', padx=5)
        tk.Button(nav_frame, text="🔙 Back", width=15, command=self.back_button_action).pack(side='left', padx=5)
        tk.Button(nav_frame, text="📤 Export Class CSV", width=18, command=self.export_csv_dropdown).pack(side='left', padx=5)
        tk.Button(nav_frame, text="📦 Export All Data", width=18, command=self.export_all_data).pack(side='left', padx=5)

    def home_button_action(self):
        self.nav_stack = []
        self.homepage()

    def back_button_action(self):
        if len(self.nav_stack) > 1:
            self.nav_stack.pop()
            self.nav_stack[-1]()
        else:
            self.homepage()

    def homepage(self):
        self.clear_frame()
        self.nav_stack = [self.homepage]
        tk.Label(self.main_frame, text="📚 Student Grading System", font=("Helvetica", 16)).pack(pady=20)
        tk.Button(self.main_frame, text="Student Management", width=30, command=self.student_menu).pack(pady=5)
        tk.Button(self.main_frame, text="Class Management", width=30, command=self.class_menu).pack(pady=5)
        tk.Button(self.main_frame, text="Assignment Management", width=30, command=self.assignment_menu).pack(pady=5)
        tk.Button(self.main_frame, text="Grades", width=30, command=self.grade_menu).pack(pady=5)

    def student_menu(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="👨‍🎓 Student Management", font=("Helvetica", 14)).pack(pady=10)
        tk.Button(self.main_frame, text="Add Student", width=30, command=self.add_student).pack(pady=5)
        tk.Button(self.main_frame, text="List Students", width=30, command=self.list_students).pack(pady=5)
        tk.Button(self.main_frame, text="Delete Student", width=30, command=self.delete_student).pack(pady=5)

    def add_student(self):
        rocket_id = simpledialog.askstring("Rocket ID", "Enter Rocket ID (R########):", parent=self.root)
        if not re.match(r'^R\d{8}$', rocket_id or ''):
            messagebox.showerror("Invalid ID", "Rocket ID must start with 'R' and 8 digits.", parent=self.root)
            return
        name = simpledialog.askstring("Name", "Enter Student Name:", parent=self.root)
        if name:
            try:
                cursor.execute("INSERT INTO students VALUES (?, ?)", (rocket_id, name))
                conn.commit()
                self.log(f"Added student {name} ({rocket_id})")
                messagebox.showinfo("Success", "Student added.", parent=self.root)
            except sqlite3.IntegrityError:
                messagebox.showwarning("Exists", "Student already exists.", parent=self.root)

    def list_students(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="All Students", font=("Helvetica", 14)).pack(pady=10)
        cursor.execute("SELECT * FROM students")
        for rocket_id, name in cursor.fetchall():
            tk.Label(self.main_frame, text=f"{rocket_id} - {name}").pack()
        self.log("Listed all students.")

    def delete_student(self):
        rocket_id = simpledialog.askstring("Delete Student", "Enter Rocket ID to delete:", parent=self.root)
        if rocket_id:
            cursor.execute("DELETE FROM grades WHERE rocket_id = ?", (rocket_id,))
            cursor.execute("DELETE FROM students WHERE rocket_id = ?", (rocket_id,))
            conn.commit()
            self.log(f"Deleted student and their grades: {rocket_id}")
            messagebox.showinfo("Deleted", f"Student {rocket_id} and their grades removed.", parent=self.root)

    def class_menu(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="🏫 Class Management", font=("Helvetica", 14)).pack(pady=10)
        tk.Button(self.main_frame, text="Add Class", width=30, command=self.add_class).pack(pady=5)
        tk.Button(self.main_frame, text="List Classes", width=30, command=self.list_classes).pack(pady=5)

    def add_class(self):
        class_id = simpledialog.askstring("Class ID", "Enter class ID (e.g., CS101):", parent=self.root)
        class_name = simpledialog.askstring("Class Name", "Enter class name:", parent=self.root)
        if class_id and class_name:
            try:
                cursor.execute("INSERT INTO classes VALUES (?, ?)", (class_id, class_name))
                conn.commit()
                self.log(f"Added class {class_id} - {class_name}")
                messagebox.showinfo("Success", "Class added.", parent=self.root)
            except sqlite3.IntegrityError:
                messagebox.showwarning("Exists", "Class already exists.", parent=self.root)

    def list_classes(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="All Classes", font=("Helvetica", 14)).pack(pady=10)
        cursor.execute("SELECT * FROM classes")
        for cid, cname in cursor.fetchall():
            tk.Label(self.main_frame, text=f"{cid} - {cname}").pack()
        self.log("Listed all classes.")

    def assignment_menu(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Select Class for Assignments", font=("Helvetica", 14)).pack(pady=10)
        cursor.execute("SELECT class_id FROM classes")
        class_ids = [row[0] for row in cursor.fetchall()]
        self.class_selector = ttk.Combobox(self.main_frame, values=class_ids, state="readonly")
        self.class_selector.pack(pady=10)
        tk.Button(self.main_frame, text="Manage Assignments", command=self.show_assignment_options).pack(pady=5)

    def show_assignment_options(self):
        class_id = self.class_selector.get()
        if not class_id:
            messagebox.showwarning("Missing", "Select a class.", parent=self.root)
            return
        self.clear_frame()
        tk.Label(self.main_frame, text=f"Assignments for {class_id}", font=("Helvetica", 14)).pack(pady=10)
        tk.Button(self.main_frame, text="Add Assignment", width=30, command=lambda: self.add_assignment(class_id)).pack(pady=5)
        tk.Button(self.main_frame, text="List Assignments", width=30, command=lambda: self.list_assignments(class_id)).pack(pady=5)

    def add_assignment(self, class_id):
        title = simpledialog.askstring("Title", "Enter assignment title:")
        due_date = simpledialog.askstring("Due Date", "Enter due date (YYYY-MM-DD):")
        try:
            max_score = int(simpledialog.askstring("Max Score", "Enter maximum score:"))
        except:
            messagebox.showerror("Invalid", "Max score must be a number.")
            return
        type_ = simpledialog.askstring("Type", "Enter type (Homework/Test):")
        if type_ not in ["Homework", "Test"]:
            messagebox.showerror("Invalid", "Type must be Homework or Test.")
            return
        cursor.execute("INSERT INTO assignments (title, due_date, max_score, type, class_id) VALUES (?, ?, ?, ?, ?)",
                       (title, due_date, max_score, type_, class_id))
        conn.commit()
        self.log(f"Added assignment: {title} for {class_id}")
        messagebox.showinfo("Success", "Assignment added.")

    def list_assignments(self, class_id):
        self.clear_frame()
        tk.Label(self.main_frame, text=f"Assignments for {class_id}", font=("Helvetica", 14)).pack(pady=10)
        cursor.execute("SELECT id, title FROM assignments WHERE class_id = ?", (class_id,))
        for aid, title in cursor.fetchall():
            tk.Label(self.main_frame, text=f"{aid} - {title}").pack()

    def grade_menu(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Select Class to Grade", font=("Helvetica", 14)).pack(pady=10)
        cursor.execute("SELECT class_id FROM classes")
        class_ids = [row[0] for row in cursor.fetchall()]
        self.grade_class_selector = ttk.Combobox(self.main_frame, values=class_ids, state="readonly")
        self.grade_class_selector.pack(pady=10)
        tk.Button(self.main_frame, text="Grade Class", command=self.grade_class_interface).pack(pady=5)

    def grade_class_interface(self):
        class_id = self.grade_class_selector.get()
        if not class_id:
            messagebox.showwarning("Missing", "Select a class.")
            return

        self.clear_frame()
        self.current_class_id = class_id
        tk.Label(self.main_frame, text=f"Grading for {class_id}", font=("Helvetica", 14)).pack(pady=10)

        cursor.execute("SELECT rocket_id FROM students")
        students = [row[0] for row in cursor.fetchall()]
        self.student_dropdown = ttk.Combobox(self.main_frame, values=students, state="readonly")
        self.student_dropdown.pack(pady=5)

        cursor.execute("SELECT id FROM assignments WHERE class_id = ?", (class_id,))
        assignments = [str(row[0]) for row in cursor.fetchall()]
        self.assignment_dropdown = ttk.Combobox(self.main_frame, values=assignments, state="readonly")
        self.assignment_dropdown.pack(pady=5)

        self.score_entry = tk.Entry(self.main_frame)
        self.score_entry.pack(pady=5)

        tk.Button(self.main_frame, text="Submit Grade", command=self.submit_grade).pack(pady=5)
        tk.Button(self.main_frame, text="Show Class Average", command=self.class_average).pack(pady=5)
        tk.Button(self.main_frame, text="📋 Show All Grades", command=self.show_all_grades).pack(pady=5)

    def show_all_grades(self):
        if not self.current_class_id:
            messagebox.showerror("No Class Selected", "Please select a class first.")
            return

        self.clear_frame()
        tk.Label(self.main_frame, text=f"All Grades for Class {self.current_class_id}", font=("Helvetica", 14)).pack(pady=10)

        cursor.execute('''
            SELECT s.rocket_id, s.name, a.title, g.score
            FROM grades g
            JOIN students s ON s.rocket_id = g.rocket_id
            JOIN assignments a ON a.id = g.assignment_id
            WHERE g.class_id = ?
        ''', (self.current_class_id,))

        results = cursor.fetchall()
        if results:
            for rocket_id, name, title, score in results:
                tk.Label(self.main_frame, text=f"{rocket_id} - {name} | {title}: {score}").pack()
            self.log(f"Displayed all grades for class {self.current_class_id}")
        else:
            tk.Label(self.main_frame, text="No grades found for this class.").pack()

        tk.Button(self.main_frame, text="Back", command=self.grade_class_interface).pack(pady=10)

    def submit_grade(self):
        rocket_id = self.student_dropdown.get()
        assignment_id = self.assignment_dropdown.get()
        try:
            score = int(self.score_entry.get())
        except:
            messagebox.showerror("Invalid", "Score must be a number.")
            return
        cursor.execute("INSERT INTO grades (rocket_id, assignment_id, score, class_id) VALUES (?, ?, ?, ?)",
                       (rocket_id, assignment_id, score, self.current_class_id))
        conn.commit()
        self.log(f"Grade submitted: {rocket_id}, AID {assignment_id}, Class {self.current_class_id}, Score {score}")
        messagebox.showinfo("Submitted", "Grade saved.")

    def class_average(self):
        cursor.execute("SELECT score FROM grades WHERE class_id = ?", (self.current_class_id,))
        scores = [row[0] for row in cursor.fetchall()]
        if scores:
            avg = sum(scores) / len(scores)
            letter, gpa = calculate_letter_grade(avg)
            self.log(f"{self.current_class_id} avg: {avg:.2f}% = {letter}")
            messagebox.showinfo("Average", f"Avg: {avg:.2f}%\nGrade: {letter}\nGPA: {gpa}")
        else:
            messagebox.showinfo("No Grades", "No grades found.")

    def export_csv_dropdown(self):
        cursor.execute("SELECT class_id FROM classes")
        class_ids = [row[0] for row in cursor.fetchall()]
        class_id = simpledialog.askstring("Export CSV", f"Enter one of these class IDs to export:\n{', '.join(class_ids)}")
        if class_id:
            self.export_csv(class_id)

    def export_csv(self, class_id):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv")
        if file_path:
            cursor.execute('''
                SELECT s.rocket_id, s.name, a.title, g.score
                FROM grades g
                JOIN students s ON s.rocket_id = g.rocket_id
                JOIN assignments a ON a.id = g.assignment_id
                WHERE g.class_id = ?
            ''', (class_id,))
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Rocket ID", "Name", "Assignment", "Score"])
                for row in cursor.fetchall():
                    writer.writerow(row)
            self.log(f"Exported {class_id} to {file_path}")
            messagebox.showinfo("Exported", "Grades exported.")

    def export_all_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", title="Export All Data as CSV")
        if file_path:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Rocket ID", "Student Name", "Class ID", "Class Name", "Assignment ID", "Assignment Title", "Type", "Due Date", "Max Score", "Score"])
                cursor.execute('''
                    SELECT s.rocket_id, s.name, c.class_id, c.class_name,
                           a.id, a.title, a.type, a.due_date, a.max_score, g.score
                    FROM students s
                    LEFT JOIN grades g ON s.rocket_id = g.rocket_id
                    LEFT JOIN assignments a ON g.assignment_id = a.id
                    LEFT JOIN classes c ON g.class_id = c.class_id
                ''')
                for row in cursor.fetchall():
                    writer.writerow(row)
            self.log(f"Exported ALL data to {file_path}")
            messagebox.showinfo("Exported", "All data exported to CSV.")

# Launch the app
if __name__ == "__main__":
    root = tk.Tk()
    app = StudentGradingApp(root)
    root.mainloop()
