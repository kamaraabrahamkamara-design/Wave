import json
import os
import gradio as grad
from datetime import datetime # For timestamps

# Persistent Local Databases
STUDENT_DB = "students.json"
TEACHER_DB = "teachers.json"
STUDENT_TRANSACTIONS_DB = "student_transactions.json" # New
TEACHER_PAYROLL_DB = "teacher_payroll.json" # New

def read_db(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            return json.load(file)
    return {} # For dictionary-based DBs

def write_db(filepath, data):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

def read_list_db(filepath): # New function for list-based DBs
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            return json.load(file)
    return [] # For list-based DBs

def append_to_list_db(filepath, new_entry): # New function to append to list-based DBs
    db_list = read_list_db(filepath)
    db_list.append(new_entry)
    with open(filepath, "w") as file:
        json.dump(db_list, file, indent=4)

# ==================== STUDENT LOGIC ====================

def add_student(stu_id, name, grade):
    if not stu_id or not name or not grade:
        return "⚠️ Error: All fields are required."
    db = read_db(STUDENT_DB)
    if stu_id in db:
        return f"⚠️ Error: Student ID '{stu_id}' already exists."

    db[stu_id] = {"name": name, "grade": grade, "balance": 0.0}
    write_db(STUDENT_DB, db);
    return f"✅ Success: Added student {name} ({grade})"

def delete_student(stu_id):
    if not stu_id:
        return "⚠️ Error: Please enter a Student ID."
    db = read_db(STUDENT_DB)
    if stu_id in db:
        name = db[stu_id]["name"]
        del db[stu_id]
        write_db(STUDENT_DB, db)
        return f"🗑️ Success: Deleted student {name} from the portal."
    return "⚠️ Error: Student ID not found."

def transact_tuition(stu_id, transaction_type, amount, description):
    if not stu_id or not amount:
        return "⚠️ Error: Student ID and Amount are required.", None
    db = read_db(STUDENT_DB)
    if stu_id not in db:
        return "⚠️ Error: Student ID not found.", None

    amount = float(amount)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    transaction_record = {
        "stu_id": stu_id,
        "type": transaction_type,
        "amount": amount,
        "description": description if description else ("Tuition Fee" if transaction_type == "Charge Fee (+)" else "Tuition Payment"),
        "timestamp": current_time
    }

    if transaction_type == "Charge Fee (+)":
        db[stu_id]["balance"] += amount
        transaction_record["final_balance"] = db[stu_id]["balance"]
        append_to_list_db(STUDENT_TRANSACTIONS_DB, transaction_record) # Record transaction
        write_db(STUDENT_DB, db)
        return f"✅ Charged ${amount:.2f} to {db[stu_id]['name']}. Current balance: ${db[stu_id]['balance']:.2f}", None

    else:  # Payment Collection & Download Generation
        db[stu_id]["balance"] -= amount
        transaction_record["final_balance"] = db[stu_id]["balance"]
        append_to_list_db(STUDENT_TRANSACTIONS_DB, transaction_record) # Record transaction
        write_db(STUDENT_DB, db)

        # Build downloadable document layout
        receipt_content = (
            "============================================\n"
            "       PREVAILING WORD SCHOOL SYSTEM - TUITION RECEIPT       \n"
            "============================================\n"
            f"Receipt Reference: REC-{stu_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}\n"
            f"Student Name:      {db[stu_id]['name']}\n"
            f"Class/Grade:       {db[stu_id]['grade']}\n"
            "--------------------------------------------\n"
            f"Description:       {description if description else 'Tuition Payment'}\n"
            f"Amount Paid:       ${amount:.2f}\n"
            f"Transaction Time:  {current_time}\n"
            "--------------------------------------------\n"
            f"REMAINING BALANCE OWEING: ${db[stu_id]['balance']:.2f}\n\n"
            "Status: RECEIVED / SYSTEM COMPLETED\n"
            "============================================\n"
        )
        filepath = f"receipt_{stu_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        with open(filepath, "w") as f:
            f.write(receipt_content)

        return f"✅ Payment recorded! Download your receipt below.", filepath

def search_student(query):
    db = read_db(STUDENT_DB)
    results = {}
    query_lower = query.lower()

    if not query:
        return "⚠️ Error: Please enter a search query.", ""

    for stu_id, data in db.items():
        if query_lower in stu_id.lower() or query_lower in data['name'].lower():
            results[stu_id] = data

    if not results:
        return "No students found matching your query.", ""

    # Format results for display
    formatted_results = """ID        Name             Grade   Balance\n------------------------------------------------\n"""
    for stu_id, data in results.items():
        formatted_results += f"{stu_id:<9} {data['name']:<17} {data['grade']:<7} ${data['balance']:.2f}\n"

    return f"✅ Found {len(results)} student(s) matching '{query}'.", formatted_results

# ==================== TEACHER LOGIC ====================

def add_teacher(tch_id, name, salary):
    if not tch_id or not name or not salary:
        return "⚠️ Error: All fields are required."
    db = read_db(TEACHER_DB)
    if tch_id in db:
        return f"⚠️ Error: Teacher ID '{tch_id}' already exists."

    db[tch_id] = {"name": name, "base_pay": float(salary)}
    write_db(TEACHER_DB, db)
    return f"✅ Success: Registered teacher {name} with base salary of ${float(salary):.2f}"

def delete_teacher(tch_id):
    if not tch_id:
        return "⚠️ Error: Please enter a Teacher ID."
    db = read_db(TEACHER_DB)
    if tch_id in db:
        name = db[tch_id]["name"]
        del db[tch_id]
        write_db(TEACHER_DB, db)
        return f"🗑️ Success: Removed teacher {name} from the directory."
    return "⚠️ Error: Teacher ID not found."

def process_payroll(tch_id, month, deductions):
    if not tch_id or not month:
        return "⚠️ Error: Teacher ID and Month are required.", None
    db = read_db(TEACHER_DB)
    if tch_id not in db:
        return "⚠️ Error: Teacher not found.", None

    base_pay = db[tch_id]["base_pay"]
    deduct_val = float(deductions) if deductions else 0.0
    net_pay = base_pay - deduct_val
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payroll_record = {
        "tch_id": tch_id,
        "month": month,
        "base_pay": base_pay,
        "deductions": deduct_val,
        "net_pay": net_pay,
        "timestamp": current_time
    }
    append_to_list_db(TEACHER_PAYROLL_DB, payroll_record) # Record payroll

    # Build downloadable document layout
    payslip_content = (
        "============================================\n"
        "       PREVAILING WORD SCHOOL SYSTEM - MONTHLY PAYSLIP       \n"
        "============================================\n"
        f"Employee ID:   {tch_id}\n"
        f"Staff Name:    {db[tch_id]['name']}\n"
        f"Pay Period:    {month}\n"
        "--------------------------------------------\n"
        f"Base Salary Rate:   ${base_pay:.2f}\n"
        f"Salary Cuts (-):    ${deduct_val:.2f}\n"
        "--------------------------------------------\n"
        f"NET TAKE-HOME DISBURSEMENT: ${net_pay:.2f}\n\n"
        "Transaction Time:  {current_time}\n"
        "Teacher Signature: _______________________\n"
        "============================================\n"
    )
    filepath = f"payslip_{tch_id}_{month}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    with open(filepath, "w") as f:
        f.write(payslip_content)

    return f"✅ Payroll computed for {month}! Download the payslip below.", filepath

# ==================== DASHBOARD LOGIC ====================

def get_student_count():
    db = read_db(STUDENT_DB)
    return str(len(db)) # Return as string for Gradio Textbox

def get_teacher_count():
    db = read_db(TEACHER_DB)
    return str(len(db)) # Return as string for Gradio Textbox

def get_total_tuition_paid_summary():
    transactions = read_list_db(STUDENT_TRANSACTIONS_DB)
    total_paid = sum(t["amount"] for t in transactions if t["type"] == "Record Payment (-)")
    num_payments = len([t for t in transactions if t["type"] == "Record Payment (-)"])
    return f"${total_paid:.2f} ({num_payments} payments)"

def get_total_salary_paid_summary():
    payroll_records = read_list_db(TEACHER_PAYROLL_DB)
    total_salary = sum(p["net_pay"] for p in payroll_records)
    num_payslips = len(payroll_records)
    return f"${total_salary:.2f} ({num_payslips} payslips)"

def get_dashboard_data():
    return (
        get_total_tuition_paid_summary(),
        get_total_salary_paid_summary(),
        get_student_count(),
        get_teacher_count()
    )

def download_student_transactions_ledger():
    transactions = read_list_db(STUDENT_TRANSACTIONS_DB)
    if not transactions:
        return "No student transactions to download.", None

    header = "Student ID,Type,Amount,Description,Timestamp,Final Balance\n"
    ledger_content = header
    for t in transactions:
        ledger_content += f"{t.get('stu_id', 'N/A')},{t.get('type', 'N/A')},{t.get('amount', 0.0):.2f},{t.get('description', 'N/A')},{t.get('timestamp', 'N/A')},{t.get('final_balance', 0.0):.2f}\n"

    filepath = f"student_transactions_ledger_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    with open(filepath, "w") as f:
        f.write(ledger_content)
    return "✅ Student transactions ledger generated!", filepath

def download_teacher_payroll_ledger():
    payroll_records = read_list_db(TEACHER_PAYROLL_DB)
    if not payroll_records:
        return "No teacher payroll records to download.", None

    header = "Teacher ID,Month,Base Pay,Deductions,Net Pay,Timestamp\n"
    ledger_content = header
    for p in payroll_records:
        ledger_content += f"{p.get('tch_id', 'N/A')},{p.get('month', 'N/A')},{p.get('base_pay', 0.0):.2f},{p.get('deductions', 0.0):.2f},{p.get('net_pay', 0.0):.2f},{p.get('timestamp', 'N/A')}\n"

    filepath = f"teacher_payroll_ledger_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    with open(filepath, "w") as f:
        f.write(ledger_content)
    return "✅ Teacher payroll ledger generated!", filepath

# ==================== GRADIO INTERFACE LAYOUT ====================

with grad.Blocks(title="School Record Portal") as demo:
    grad.Markdown("# 🏫 School Portal Financial Record System")
    grad.Markdown("Manage basic records for student tuition invoices and teacher monthly salaries layout.")

    with grad.Tab("👧 Student Tuition Portal"):
        with grad.Row():
            with grad.Column():
                grad.Markdown("### Add / Remove Student profiles")
                stu_id = grad.Textbox(label="Student ID (Unique)", placeholder="e.g., STU101")
                stu_name = grad.Textbox(label="Full Name")
                stu_grade = grad.Textbox(label="Class/Grade")
                with grad.Row():
                    btn_add_stu = grad.Button("➕ Add Student Profile", variant="primary")
                    btn_del_stu = grad.Button("🗑️ Delete Student Profile", variant="stop")
                stu_profile_output = grad.Textbox(label="System Response Log", interactive=False)

            with grad.Column():
                grad.Markdown("### Financial Transactions & Receipts")
                trans_id = grad.Textbox(label="Target Student ID", placeholder="e.g., STU101")
                trans_type = grad.Radio(["Charge Fee (+)", "Record Payment (-)"], label="Action Type", value="Record Payment (-)")
                trans_amount = grad.Number(label="Amount ($)")
                trans_desc = grad.Textbox(label="Memo/Description", placeholder="e.g., Term 1 Baseline Payment")
                btn_transact = grad.Button("💰 Submit Financial Log Entry", variant="secondary")

                trans_output = grad.Textbox(label="Transaction Log Status", interactive=False)
                receipt_download = grad.File(label="📥 Download Generated Document Receipt")

        # Wire Up Student Actions
        btn_add_stu.click(add_student, inputs=[stu_id, stu_name, stu_grade], outputs=stu_profile_output)
        btn_del_stu.click(delete_student, inputs=[stu_id], outputs=stu_profile_output)
        btn_transact.click(transact_tuition, inputs=[trans_id, trans_type, trans_amount, trans_desc], outputs=[trans_output, receipt_download])

        # --- New Search Feature Integration ---
        with grad.Row():
            with grad.Column():
                grad.Markdown("### Search Student Records")
                search_query = grad.Textbox(label="Search by Student ID or Name", placeholder="e.g., STU101 or John Doe")
                btn_search_stu = grad.Button("🔍 Search Student", variant="secondary")
                search_output = grad.Textbox(label="Search Status", interactive=False)
                search_results = grad.Textbox(label="Search Results", interactive=False, lines=5, max_lines=10)

        # Wire Up Student Search Action
        btn_search_stu.click(search_student, inputs=[search_query], outputs=[search_output, search_results])
        # --- End New Search Feature Integration ---

    with grad.Tab("🧑‍🏫 Teacher Salary Portal"):
        with grad.Row():
            with grad.Column():
                grad.Markdown("### Manage Staff Registry")
                tch_id = grad.Textbox(label="Teacher ID (Unique)", placeholder="e.g., TCH001")
                tch_name = grad.Textbox(label="Full Name")
                tch_salary = grad.Number(label="Contracted Monthly Base Pay ($)")
                with grad.Row():
                    btn_add_tch = grad.Button("➕ Register New Staff", variant="primary")
                    btn_del_tch = grad.Button("🗑️ Remove Staff Member", variant="stop")
                tch_profile_output = grad.Textbox(label="System Response Log", interactive=False)

            with grad.Column():
                grad.Markdown("### Monthly Payroll Processing")
                pay_id = grad.Textbox(label="Target Teacher ID", placeholder="e.g., TCH001")
                pay_month = grad.Dropdown(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], label="Salary Month")
                pay_deduct = grad.Number(label="Deductions / Cuts ($) (e.g. Absences)", value=0.0)
                btn_payroll = grad.Button("⚙️ Process Monthly Payroll", variant="secondary")

                payroll_output = grad.Textbox(label="Payroll Log Status", interactive=False)
                payslip_download = grad.File(label="📥 Download Generated Monthly Payslip")

        # Wire Up Teacher Actions
        btn_add_tch.click(add_teacher, inputs=[tch_id, tch_name, tch_salary], outputs=tch_profile_output)
        btn_del_tch.click(delete_teacher, inputs=[tch_id], outputs=tch_profile_output)
        btn_payroll.click(process_payroll, inputs=[pay_id, pay_month, pay_deduct], outputs=[payroll_output, payslip_download])

    # --- New Dashboard Tab ---
    with grad.Tab("📊 Financial Dashboard"):
        grad.Markdown("### Overview of Financials")
        with grad.Row():
            total_tuition_display = grad.Textbox(label="Total Tuition Collected (Payments)", interactive=False)
            total_salary_display = grad.Textbox(label="Total Salary Disbursed (Payslips)", interactive=False)
        with grad.Row():
            student_count_display = grad.Textbox(label="Total Students Registered", interactive=False)
            teacher_count_display = grad.Textbox(label="Total Teachers Registered", interactive=False)

        btn_refresh_dashboard = grad.Button("🔄 Refresh Dashboard", variant="primary")

        btn_refresh_dashboard.click(
            get_dashboard_data,
            outputs=[total_tuition_display, total_salary_display, student_count_display, teacher_count_display]
        )

        grad.Markdown("### Download Financial Ledgers")
        with grad.Row():
            btn_download_student_ledger = grad.Button("⬇️ Download Student Transactions Ledger (CSV)", variant="secondary")
            btn_download_teacher_ledger = grad.Button("⬇️ Download Teacher Payroll Ledger (CSV)", variant="secondary")
        with grad.Row():
            student_ledger_output = grad.Textbox(label="Student Ledger Status", interactive=False)
            student_ledger_download = grad.File(label="📥 Download Student Transactions CSV")
        with grad.Row():
            teacher_ledger_output = grad.Textbox(label="Teacher Ledger Status", interactive=False)
            teacher_ledger_download = grad.File(label="📥 Download Teacher Payroll CSV")

        btn_download_student_ledger.click(download_student_transactions_ledger, outputs=[student_ledger_output, student_ledger_download])
        btn_download_teacher_ledger.click(download_teacher_payroll_ledger, outputs=[teacher_ledger_output, teacher_ledger_download])

    # --- End New Dashboard Tab ---

if __name__ == "__main__":
    demo.launch()