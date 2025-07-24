import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk
import sqlite3
import csv
import re

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
        self.root.geometry("1200x700")
        self.nav_stack = []
        self.current_class_id = None

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(side='left', fill='both', expand=True)

        self.homepage()

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

    def go_to(self, screen_function):
        self.nav_stack.append(screen_function)
        screen_function()

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
        tk.Label(self.main_frame, text="📚 Student Grading System", font=("Helvetica", 18)).pack(pady=20)
        tk.Button(self.main_frame, text="Student Management", width=30, command=lambda: self.go_to(self.student_menu)).pack(pady=5)
        tk.Button(self.main_frame, text="Class Management", width=30, command=lambda: self.go_to(self.class_menu)).pack(pady=5)
        tk.Button(self.main_frame, text="Assignment Management", width=30, command=lambda: self.go_to(self.assignment_menu)).pack(pady=5)
        tk.Button(self.main_frame, text="Grades", width=30, command=lambda: self.go_to(self.grade_menu)).pack(pady=5)
    # === Student Management ===
    def student_menu(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="👨‍🎓 Student Management", font=("Helvetica", 16)).pack(pady=10)

        tk.Button(self.main_frame, text="Add Student", width=30, command=self.add_student).pack(pady=5)
        tk.Button(self.main_frame, text="Edit Student", width=30, command=self.edit_student).pack(pady=5)
        tk.Button(self.main_frame, text="Delete Student", width=30, command=self.delete_student).pack(pady=5)
        tk.Button(self.main_frame, text="Sort by Name", width=30, command=lambda: self.list_students(sort_by='name')).pack(pady=5)
        tk.Button(self.main_frame, text="Sort by Rocket ID", width=30, command=lambda: self.list_students(sort_by='rocket_id')).pack(pady=5)
        tk.Button(self.main_frame, text="List All Students", width=30, command=self.list_students).pack(pady=5)

    def add_student(self):
        rocket_id = simpledialog.askstring("Rocket ID", "Enter Rocket ID (R########):")
        if not re.match(r'^R\d{8}$', rocket_id or ''):
            messagebox.showerror("Invalid ID", "Rocket ID must start with 'R' and 8 digits.")
            return
        name = simpledialog.askstring("Name", "Enter Student Name:")
        if name:
            try:
                cursor.execute("INSERT INTO students VALUES (?, ?)", (rocket_id, name))
                conn.commit()
                messagebox.showinfo("Success", "Student added.")
            except sqlite3.IntegrityError:
                messagebox.showwarning("Exists", "Student already exists.")

    def edit_student(self):
        students = self.get_all_students()
        if not students:
            messagebox.showinfo("None", "No students found.")
            return
        ids = [s[0] for s in students]
        selected_id = simpledialog.askstring("Edit Student", "Choose Rocket ID:\n" + "\n".join(ids))
        if selected_id:
            new_name = simpledialog.askstring("Edit Name", "Enter New Name:")
            if new_name:
                cursor.execute("UPDATE students SET name = ? WHERE rocket_id = ?", (new_name, selected_id))
                conn.commit()
                messagebox.showinfo("Updated", "Student updated.")

    def delete_student(self):
        students = self.get_all_students()
        if not students:
            messagebox.showinfo("None", "No students found.")
            return
        ids = [s[0] for s in students]
        selected_id = simpledialog.askstring("Delete Student", "Choose Rocket ID:\n" + "\n".join(ids))
        if selected_id:
            confirm = messagebox.askyesno("Confirm", "Are you sure?")
            if confirm:
                cursor.execute("DELETE FROM students WHERE rocket_id = ?", (selected_id,))
                conn.commit()
                messagebox.showinfo("Deleted", "Student deleted.")

    def list_students(self, sort_by=None):
        self.clear_frame()
        tk.Label(self.main_frame, text="📋 All Students", font=("Helvetica", 16)).pack(pady=10)

        query = "SELECT rocket_id, name FROM students"
        if sort_by == 'name':
            query += " ORDER BY name ASC"
        elif sort_by == 'rocket_id':
            query += " ORDER BY rocket_id ASC"

        cursor.execute(query)
        students = cursor.fetchall()
        for rocket_id, name in students:
            tk.Label(self.main_frame, text=f"{rocket_id} - {name}").pack()

    def get_all_students(self):
        cursor.execute("SELECT rocket_id, name FROM students")
        return cursor.fetchall()
    # === Class Management ===
    def class_menu(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="🏫 Class Management", font=("Helvetica", 16)).pack(pady=10)

        tk.Button(self.main_frame, text="Add Class", width=30, command=self.add_class).pack(pady=5)
        tk.Button(self.main_frame, text="Edit Class", width=30, command=self.edit_class).pack(pady=5)
        tk.Button(self.main_frame, text="Delete Class", width=30, command=self.delete_class).pack(pady=5)
        tk.Button(self.main_frame, text="Sort by Class ID", width=30, command=lambda: self.list_classes(sort_by='class_id')).pack(pady=5)
        tk.Button(self.main_frame, text="Sort by Class Name", width=30, command=lambda: self.list_classes(sort_by='class_name')).pack(pady=5)
        tk.Button(self.main_frame, text="List All Classes", width=30, command=self.list_classes).pack(pady=5)

    def add_class(self):
        class_id = simpledialog.askstring("Class ID", "Enter Class ID:")
        class_name = simpledialog.askstring("Class Name", "Enter Class Name:")
        if class_id and class_name:
            try:
                cursor.execute("INSERT INTO classes VALUES (?, ?)", (class_id, class_name))
                conn.commit()
                messagebox.showinfo("Success", "Class added.")
            except sqlite3.IntegrityError:
                messagebox.showwarning("Exists", "Class already exists.")

    def edit_class(self):
        classes = self.get_all_classes()
        if not classes:
            messagebox.showinfo("None", "No classes found.")
            return
        ids = [c[0] for c in classes]
        selected_id = simpledialog.askstring("Edit Class", "Choose Class ID:\n" + "\n".join(ids))
        if selected_id:
            new_name = simpledialog.askstring("Edit Name", "Enter New Class Name:")
            if new_name:
                cursor.execute("UPDATE classes SET class_name = ? WHERE class_id = ?", (new_name, selected_id))
                conn.commit()
                messagebox.showinfo("Updated", "Class updated.")

    def delete_class(self):
        classes = self.get_all_classes()
        if not classes:
            messagebox.showinfo("None", "No classes found.")
            return
        ids = [c[0] for c in classes]
        selected_id = simpledialog.askstring("Delete Class", "Choose Class ID:\n" + "\n".join(ids))
        if selected_id:
            confirm = messagebox.askyesno("Confirm", "Are you sure?")
            if confirm:
                cursor.execute("DELETE FROM classes WHERE class_id = ?", (selected_id,))
                conn.commit()
                messagebox.showinfo("Deleted", "Class deleted.")

    def list_classes(self, sort_by=None):
        self.clear_frame()
        tk.Label(self.main_frame, text="📋 All Classes", font=("Helvetica", 16)).pack(pady=10)

        query = "SELECT class_id, class_name FROM classes"
        if sort_by == 'class_id':
            query += " ORDER BY class_id ASC"
        elif sort_by == 'class_name':
            query += " ORDER BY class_name ASC"

        cursor.execute(query)
        classes = cursor.fetchall()
        for class_id, name in classes:
            tk.Label(self.main_frame, text=f"{class_id} - {name}").pack()

    def get_all_classes(self):
        cursor.execute("SELECT class_id, class_name FROM classes")
        return cursor.fetchall()
    # === Assignment Management ===
    def assignment_menu(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="📚 Assignment Management", font=("Helvetica", 16)).pack(pady=10)

        cursor.execute("SELECT class_id FROM classes")
        classes = [row[0] for row in cursor.fetchall()]
        if not classes:
            messagebox.showinfo("None", "No classes available.")
            return

        self.assignment_class_dropdown = ttk.Combobox(self.main_frame, values=classes, state="readonly")
        self.assignment_class_dropdown.pack(pady=5)
        tk.Button(self.main_frame, text="Select Class", command=self.show_assignment_options).pack(pady=5)

    def show_assignment_options(self):
        class_id = self.assignment_class_dropdown.get()
        if not class_id:
            messagebox.showwarning("Missing", "Select a class first.")
            return

        self.clear_frame()
        tk.Label(self.main_frame, text=f"Assignments for {class_id}", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.main_frame, text="Add Assignment", width=30, command=lambda: self.add_assignment(class_id)).pack(pady=5)
        tk.Button(self.main_frame, text="Edit Assignment", width=30, command=lambda: self.edit_assignment(class_id)).pack(pady=5)
        tk.Button(self.main_frame, text="Delete Assignment", width=30, command=lambda: self.delete_assignment(class_id)).pack(pady=5)
        tk.Button(self.main_frame, text="Sort by Title", width=30, command=lambda: self.list_assignments(class_id, sort_by='title')).pack(pady=5)
        tk.Button(self.main_frame, text="List All Assignments", width=30, command=lambda: self.list_assignments(class_id)).pack(pady=5)

    def add_assignment(self, class_id):
        title = simpledialog.askstring("Title", "Enter Assignment Title:")
        due_date = simpledialog.askstring("Due Date", "Enter Due Date (YYYY-MM-DD):")
        try:
            max_score = int(simpledialog.askstring("Max Score", "Enter Maximum Score:"))
        except:
            messagebox.showerror("Invalid", "Max score must be a number.")
            return
        type_ = simpledialog.askstring("Type", "Enter Type (Homework/Test):")
        if type_ not in ["Homework", "Test"]:
            messagebox.showerror("Invalid", "Type must be Homework or Test.")
            return
        cursor.execute("INSERT INTO assignments (title, due_date, max_score, type, class_id) VALUES (?, ?, ?, ?, ?)",
                       (title, due_date, max_score, type_, class_id))
        conn.commit()
        messagebox.showinfo("Success", "Assignment added.")

    def edit_assignment(self, class_id):
        cursor.execute("SELECT id, title FROM assignments WHERE class_id = ?", (class_id,))
        assignments = cursor.fetchall()
        if not assignments:
            messagebox.showinfo("None", "No assignments found.")
            return
        choices = [f"{aid}: {title}" for aid, title in assignments]
        selected_id = simpledialog.askstring("Edit Assignment", "Choose ID:\n" + "\n".join(choices))
        if selected_id:
            try:
                assignment_id = int(selected_id.split(":")[0])
            except:
                messagebox.showerror("Invalid", "Invalid assignment selected.")
                return
            new_title = simpledialog.askstring("New Title", "Enter New Title:")
            new_due_date = simpledialog.askstring("New Due Date", "Enter New Due Date (YYYY-MM-DD):")
            try:
                new_max_score = int(simpledialog.askstring("New Max Score", "Enter New Max Score:"))
            except:
                messagebox.showerror("Invalid", "Max score must be a number.")
                return
            new_type = simpledialog.askstring("New Type", "Enter Type (Homework/Test):")
            if new_title and new_due_date and new_type:
                cursor.execute('''
                    UPDATE assignments
                    SET title = ?, due_date = ?, max_score = ?, type = ?
                    WHERE id = ?
                ''', (new_title, new_due_date, new_max_score, new_type, assignment_id))
                conn.commit()
                messagebox.showinfo("Updated", "Assignment updated.")

    def delete_assignment(self, class_id):
        cursor.execute("SELECT id, title FROM assignments WHERE class_id = ?", (class_id,))
        assignments = cursor.fetchall()
        if not assignments:
            messagebox.showinfo("None", "No assignments to delete.")
            return
        choices = [f"{aid}: {title}" for aid, title in assignments]
        selected_id = simpledialog.askstring("Delete Assignment", "Choose ID:\n" + "\n".join(choices))
        if selected_id:
            try:
                assignment_id = int(selected_id.split(":")[0])
            except:
                messagebox.showerror("Invalid", "Invalid assignment selected.")
                return
            confirm = messagebox.askyesno("Confirm", "Are you sure?")
            if confirm:
                cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
                conn.commit()
                messagebox.showinfo("Deleted", "Assignment deleted.")

    def list_assignments(self, class_id, sort_by=None):
        self.clear_frame()
        tk.Label(self.main_frame, text=f"📋 Assignments for {class_id}", font=("Helvetica", 16)).pack(pady=10)

        query = "SELECT id, title FROM assignments WHERE class_id = ?"
        if sort_by == 'title':
            query += " ORDER BY title ASC"

        cursor.execute(query, (class_id,))
        for aid, title in cursor.fetchall():
            tk.Label(self.main_frame, text=f"{aid} - {title}").pack()
    # === Grade Management ===
    def grade_menu(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="📋 Grade Management", font=("Helvetica", 16)).pack(pady=10)

        cursor.execute("SELECT class_id FROM classes")
        classes = [row[0] for row in cursor.fetchall()]
        if not classes:
            messagebox.showinfo("None", "No classes available.")
            return

        self.grade_class_dropdown = ttk.Combobox(self.main_frame, values=classes, state="readonly")
        self.grade_class_dropdown.pack(pady=5)
        tk.Button(self.main_frame, text="Select Class", command=self.grade_class_interface).pack(pady=5)
        tk.Button(self.main_frame, text="View Student Report", width=30, command=self.view_student_report).pack(pady=5)

    def grade_class_interface(self):
        class_id = self.grade_class_dropdown.get()
        if not class_id:
            messagebox.showwarning("Missing", "Select a class first.")
            return

        self.clear_frame()
        self.current_class_id = class_id
        tk.Label(self.main_frame, text=f"Grading for {class_id}", font=("Helvetica", 16)).pack(pady=10)

        cursor.execute("SELECT rocket_id FROM students")
        students = [row[0] for row in cursor.fetchall()]
        if not students:
            messagebox.showinfo("No Students", "No students available.")
            return
        self.student_dropdown = ttk.Combobox(self.main_frame, values=students, state="readonly")
        self.student_dropdown.pack(pady=5)

        cursor.execute("SELECT title FROM assignments WHERE class_id = ?", (class_id,))
        assignments = [row[0] for row in cursor.fetchall()]
        if not assignments:
            messagebox.showinfo("No Assignments", "No assignments for this class.")
            return
        self.assignment_dropdown = ttk.Combobox(self.main_frame, values=assignments, state="readonly")
        self.assignment_dropdown.pack(pady=5)

        self.score_entry = tk.Entry(self.main_frame)
        self.score_entry.pack(pady=5)

        tk.Button(self.main_frame, text="Submit/Update Grade", command=self.submit_or_update_grade).pack(pady=5)

    def submit_or_update_grade(self):
        rocket_id = self.student_dropdown.get()
        assignment_title = self.assignment_dropdown.get()
        try:
            score = int(self.score_entry.get())
        except:
            messagebox.showerror("Invalid", "Score must be a number.")
            return

        cursor.execute("SELECT id FROM assignments WHERE title = ?", (assignment_title,))
        result = cursor.fetchone()
        if not result:
            messagebox.showerror("Error", "Assignment not found.")
            return
        assignment_id = result[0]

        cursor.execute("SELECT * FROM grades WHERE rocket_id = ? AND assignment_id = ?", (rocket_id, assignment_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("UPDATE grades SET score = ?, class_id = ? WHERE rocket_id = ? AND assignment_id = ?",
                           (score, self.current_class_id, rocket_id, assignment_id))
        else:
            cursor.execute("INSERT INTO grades (rocket_id, assignment_id, score, class_id) VALUES (?, ?, ?, ?)",
                           (rocket_id, assignment_id, score, self.current_class_id))
        conn.commit()
        messagebox.showinfo("Success", "Grade submitted or updated.")

    def view_student_report(self):
        cursor.execute("SELECT rocket_id FROM students")
        students = [row[0] for row in cursor.fetchall()]
        if not students:
            messagebox.showinfo("None", "No students available.")
            return

        student_id = simpledialog.askstring("Select Student", f"Enter Rocket ID:\n{', '.join(students)}")
        if not student_id:
            return

        self.clear_frame()
        tk.Label(self.main_frame, text=f"📖 Report for {student_id}", font=("Helvetica", 16)).pack(pady=10)

        cursor.execute('''
            SELECT c.class_name, a.title, a.max_score, g.score
            FROM grades g
            JOIN assignments a ON g.assignment_id = a.id
            JOIN classes c ON g.class_id = c.class_id
            WHERE g.rocket_id = ?
            ORDER BY c.class_name
        ''', (student_id,))
        results = cursor.fetchall()

        if not results:
            tk.Label(self.main_frame, text="No grades found for this student.").pack()
            return

        last_class = None
        for class_name, title, max_score, score in results:
            if class_name != last_class:
                tk.Label(self.main_frame, text=f"\n📚 Class: {class_name}", font=("Helvetica", 14, "bold")).pack()
                last_class = class_name
            percentage = (score / max_score) * 100 if max_score else 0
            letter, _ = calculate_letter_grade(percentage)
            tk.Label(self.main_frame, text=f" - {title}: {score}/{max_score} ({percentage:.2f}%) ➔ {letter}").pack()

    # === Export Management ===
    def export_csv_dropdown(self):
        cursor.execute("SELECT class_id FROM classes")
        class_ids = [row[0] for row in cursor.fetchall()]
        class_id = simpledialog.askstring("Export CSV", f"Enter Class ID:\n{', '.join(class_ids)}")
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
            messagebox.showinfo("Exported", "Class grades exported.")

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
            messagebox.showinfo("Exported", "All data exported.")

# === Launch the App ===
if __name__ == "__main__":
    root = tk.Tk()
    app = StudentGradingApp(root)
    root.mainloop()
