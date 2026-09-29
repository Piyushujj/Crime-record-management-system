import mysql.connector
from datetime import date, datetime
import re
import sys


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "india@123",
    "database": "crime_record",
    "raise_on_warnings": True
}

def connect():
    # create DB if not exists then connect
    tmp = mysql.connector.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"])
    tmp_cursor = tmp.cursor()
    tmp_cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(DB_CONFIG["database"]))
    tmp_cursor.close()
    tmp.close()
    return mysql.connector.connect(**DB_CONFIG)

# ------------ VALIDATION HELPERS ----------------

def get_non_empty(prompt):
    while True:
        x = input(prompt).strip()
        if x:
            return x
        print("Cannot be empty!")

def validate_phone():
    while True:
        p = input("Phone (10 digits): ").strip()
        if p.isdigit() and len(p) == 10:
            return p
        print("Invalid phone number.")

def validate_email():
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    while True:
        e = input("Email: ").strip()
        if re.match(pattern, e):
            return e
        print("Invalid email format.")

def validate_gender():
    while True:
        g = input("Gender (Male/Female/Other): ").strip().title()
        if g in ["Male", "Female", "Other"]:
            return g
        print("Invalid gender.")

def validate_age():
    while True:
        a = input("Age: ").strip()
        if a.isdigit() and 0 < int(a) < 120:
            return int(a)
        print("Invalid age.")

def validate_crime_type():
    types = [
        "Theft","Robbery","Assault","Fraud","Cybercrime","Kidnapping","Murder",
        "Harassment","Domestic Violence","Burglary","Drug Possession","Arson"
    ]
    print("Crime Types:")
    for t in types:
        print(" -", t)
    while True:
        c = input("Crime Type: ").strip().title()
        if c in [x.title() for x in types]:
            return c
        print("Invalid crime type.")

def print_table(rows, headers):
    if not rows:
        print("No records found.\n")
        return
    # convert rows to list in case cursor returns generator
    rows = list(rows)
    # compute widths
    col_widths = [max(len(str(val)) for val in col) for col in zip(*rows, headers)]
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print(" | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers))))
    print()

# ----------------- SCHEMA CREATION -----------------

def create_tables(cur, conn):

    # Disable warnings like "table already exists"
    cur.execute("SET sql_notes = 0;")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS COMPLAINANT (
        complaint_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        aadhar VARCHAR(12) UNIQUE,
        contact VARCHAR(15),
        address TEXT,
        date_reg DATE,
        gender VARCHAR(20)
    ) ENGINE=InnoDB;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS POLICE_OFFICER (
        officer_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        rank_officer VARCHAR(100),
        phone VARCHAR(15),
        email VARCHAR(255),
        station VARCHAR(255),
        password_hash VARCHAR(255)
    ) ENGINE=InnoDB;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS CRIME_REPORT (
        crime_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        complaint_id INT,
        crime_type VARCHAR(100),
        crime_date DATE,
        crime_location TEXT,
        status VARCHAR(50),
        FOREIGN KEY (complaint_id) REFERENCES COMPLAINANT(complaint_id) ON DELETE SET NULL
    ) ENGINE=InnoDB;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS VICTIM (
        victim_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        crime_id INT,
        name VARCHAR(255),
        age INT,
        gender VARCHAR(20),
        injuries TEXT,
        FOREIGN KEY (crime_id) REFERENCES CRIME_REPORT(crime_id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS SUSPECT (
        suspect_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        crime_id INT,
        name VARCHAR(255),
        contact VARCHAR(50),
        address TEXT,
        status VARCHAR(100),
        FOREIGN KEY (crime_id) REFERENCES CRIME_REPORT(crime_id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS EVIDENCE (
        evidence_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        crime_id INT,
        description TEXT,
        evidence_type VARCHAR(100),
        submitted_date DATE,
        FOREIGN KEY (crime_id) REFERENCES CRIME_REPORT(crime_id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS FIR (
        fir_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        crime_id INT,
        filing_date DATE,
        details TEXT,
        FOREIGN KEY (crime_id) REFERENCES CRIME_REPORT(crime_id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS CASE_ASSIGNMENT (
        assign_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        crime_id INT,
        officer_id INT,
        assigned_date DATE,
        remarks TEXT,
        FOREIGN KEY (crime_id) REFERENCES CRIME_REPORT(crime_id) ON DELETE CASCADE,
        FOREIGN KEY (officer_id) REFERENCES POLICE_OFFICER(officer_id) ON DELETE SET NULL
    ) ENGINE=InnoDB;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ACTION_LOG (
        log_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        officer_id INT,
        crime_id INT,
        action_description TEXT,
        timestamp DATETIME,
        FOREIGN KEY (officer_id) REFERENCES POLICE_OFFICER(officer_id) ON DELETE SET NULL,
        FOREIGN KEY (crime_id) REFERENCES CRIME_REPORT(crime_id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)

    # Re-enable warnings
    cur.execute("SET sql_notes = 1;")

    conn.commit()



# ---------------- CORE FUNCTIONS ----------------

def register_officer(cur, conn):
    print("\n======= Register New Officer =======")
    name = get_non_empty("Name: ")
    rank = get_non_empty("Rank: ")
    phone = validate_phone()
    email = validate_email()
    station = get_non_empty("Station: ")
    password = get_non_empty("Password: ")
    opass=(station[:3].lower()) + phone[-4:]
    if opass!=password:
        print('invalid password!')
        print('Exiting!!!!')
        time.sleep(1)
        print('Exiting!!!!')
    else:
        cur.execute("""
            INSERT INTO POLICE_OFFICER (name, rank_officer, phone, email, station, password_hash)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (name, rank, phone, email, station, password))

        conn.commit()
        print("Officer registered with ID:", cur.lastrowid)
        print()

def login_officer(cur):
    try:
        oid = int(get_non_empty("Officer ID: "))
    except:
        print("Invalid Officer ID.")
        return None

    pwd = get_non_empty("Password: ")

    cur.execute("SELECT officer_id, name, password_hash FROM POLICE_OFFICER WHERE officer_id=%s", (oid,))
    row = cur.fetchone()

    if not row:
        print("Officer not found.")
        return None

    if pwd != row[2]:
        print("Incorrect password.")
        return None

    print("\nLogin successful. Welcome,", row[1], "\n")
    return row[0]

# add complainant & full case creation
def add_complainant_flow(cur, conn):
    print("\n--- File New Full Case ---")
    name = get_non_empty("Complainant Name: ")
    aadhar = get_non_empty("Aadhar (12 digits): ")
    if not aadhar.isdigit() or len(aadhar) != 12:
        print('Invalid aadhar!')
        return
    contact = validate_phone()
    address = get_non_empty("Address: ")
    gender = validate_gender()

    # INSERT WITHOUT complaint_id (AUTO_INCREMENT will handle it)
    cur.execute("""
        INSERT INTO COMPLAINANT (name, aadhar, contact, address, date_reg, gender)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (name, aadhar, contact, address, date.today(), gender))

    conn.commit()
    complaint_id = cur.lastrowid
    print("Complainant ID:", complaint_id)

    # Crime
    ctype = validate_crime_type()
    location = get_non_empty("Crime Location: ")

    cur.execute("""
        INSERT INTO CRIME_REPORT (complaint_id, crime_type, crime_date, crime_location, status)
        VALUES (%s,%s,%s,%s,%s)
    """, (complaint_id, ctype, date.today(), location, "Open"))

    conn.commit()
    crime_id = cur.lastrowid
    print("Crime ID:", crime_id)

    # Victim
    if input("Add victim? (y/n): ").lower() == 'y':
        vname = get_non_empty("Victim Name: ")
        vage = validate_age()
        vgender = validate_gender()
        inj = input("Injuries: ")

        cur.execute("""
            INSERT INTO VICTIM (crime_id, name, age, gender, injuries)
            VALUES (%s,%s,%s,%s,%s)
        """, (crime_id, vname, vage, vgender, inj))
        conn.commit()
        print("Victim added.")

    # Suspect
    if input("Add suspect? (y/n): ").lower() == 'y':
        sname = get_non_empty("Suspect Name: ")
        scontact = input("Contact: ")
        saddr = input("Address: ")

        cur.execute("""
            INSERT INTO SUSPECT (crime_id, name, contact, address, status)
            VALUES (%s,%s,%s,%s,%s)
        """, (crime_id, sname, scontact, saddr, "Under Investigation"))
        conn.commit()
        print("Suspect added.")

    # Evidence
    if input("Add evidence? (y/n): ").lower() == 'y':
        desc = get_non_empty("Description: ")
        etype = get_non_empty("Type: ")

        cur.execute("""
            INSERT INTO EVIDENCE (crime_id, description, evidence_type, submitted_date)
            VALUES (%s,%s,%s,%s)
        """, (crime_id, desc, etype, date.today()))
        conn.commit()
        print("Evidence added.")

    # FIR
    if input("File FIR? (y/n): ").lower() == 'y':
        details = get_non_empty("FIR Details: ")
        cur.execute("""
            INSERT INTO FIR (crime_id, filing_date, details)
            VALUES (%s,%s,%s)
        """, (crime_id, date.today(), details))
        conn.commit()
        print("FIR Filed.")

    print("\nCase filing complete.\n")

# view case and related tables
def view_case(cur):
    try:
        cid = int(get_non_empty("Enter Crime ID: "))
    except:
        print("Invalid ID.")
        return

    cur.execute('''SELECT crime_id, complaint_id, crime_type, crime_date, crime_location,
                        status FROM CRIME_REPORT WHERE crime_id=%s''', (cid,))
    crime = cur.fetchone()
    if not crime:
        print("No such case.")
        return

    print_table([crime], ["crime_id","complaint_id","crime_type","crime_date","crime_location","status"])

    # Complainant
    cur.execute('''SELECT complaint_id, name, aadhar, contact, address, date_reg, gender
                FROM COMPLAINANT WHERE complaint_id=%s''', (crime[1],))
    comp = cur.fetchone()
    if comp:
        print_table([comp], ["complaint_id","name","aadhar","contact","address","date_reg","gender"])

    # Victim
    cur.execute("SELECT victim_id, crime_id, name, age, gender, injuries FROM VICTIM WHERE crime_id=%s", (cid,))
    print_table(cur.fetchall(), ["victim_id","crime_id","name","age","gender","injuries"])

    # Suspect
    cur.execute("SELECT suspect_id, crime_id, name, contact, address, status FROM SUSPECT WHERE crime_id=%s", (cid,))
    print_table(cur.fetchall(), ["suspect_id","crime_id","name","contact","address","status"])

    # Evidence
    cur.execute("SELECT evidence_id, crime_id, description, evidence_type, submitted_date FROM EVIDENCE WHERE crime_id=%s", (cid,))
    print_table(cur.fetchall(), ["evidence_id","crime_id","description","evidence_type","submitted_date"])

    # FIR
    cur.execute("SELECT fir_id, crime_id, filing_date, details FROM FIR WHERE crime_id=%s", (cid,))
    print_table(cur.fetchall(), ["fir_id","crime_id","filing_date","details"])

    # Assignments
    cur.execute("SELECT assign_id, crime_id, officer_id, assigned_date, remarks FROM CASE_ASSIGNMENT WHERE crime_id=%s", (cid,))
    print_table(cur.fetchall(), ["assign_id","crime_id","officer_id","assigned_date","remarks"])

    # Logs
    cur.execute("SELECT log_id, officer_id, crime_id, action_description, timestamp FROM ACTION_LOG WHERE crime_id=%s", (cid,))
    print_table(cur.fetchall(), ["log_id","officer_id","crime_id","action_description","timestamp"])

# log action
def log_action(cur, conn, oid, crime_id, action):
    cur.execute("""
        INSERT INTO ACTION_LOG (officer_id, crime_id, action_description, timestamp)
        VALUES (%s,%s,%s,%s)
    """, (oid, crime_id, action, datetime.now()))
    conn.commit()

# modify case
def modify_case(cur, conn, oid):
    try:
        cid = int(get_non_empty("Crime ID: "))
    except:
        print("Invalid.")
        return

    cur.execute("SELECT crime_type, crime_location, status FROM CRIME_REPORT WHERE crime_id=%s", (cid,))
    c = cur.fetchone()
    if not c:
        print("No such case.")
        return

    new_type = input("New Crime Type (leave blank to keep): ") or c[0]
    new_loc = input("New Location (leave blank to keep): ") or c[1]
    new_status = input("New Status (Open/Ongoing/Closed): ") or c[2]

    cur.execute("""
        UPDATE CRIME_REPORT SET crime_type=%s, crime_location=%s, status=%s WHERE crime_id=%s
    """, (new_type, new_loc, new_status, cid))
    conn.commit()

    log_action(cur, conn, oid, cid, f"Case modified by officer {oid}")
    print("Updated.")

# assign case
def assign_case(cur, conn, oid):
    try:
        cid = int(get_non_empty("Crime ID: "))
    except:
        print("Invalid.")
        return

    cur.execute("SELECT officer_id, name FROM POLICE_OFFICER")
    officers = cur.fetchall()
    print_table(officers, ["Officer ID","Name"])

    try:
        oid2 = int(get_non_empty("Assign to Officer ID: "))
    except:
        print("Invalid.")
        return

    remarks = input("Remarks: ")

    cur.execute("""
        INSERT INTO CASE_ASSIGNMENT (crime_id, officer_id, assigned_date, remarks)
        VALUES (%s,%s,%s,%s)
    """, (cid, oid2, date.today(), remarks))
    conn.commit()

    log_action(cur, conn, oid, cid, f"Assigned to officer {oid2}")
    print("Assigned.")

# reporting
def reporting_dashboard(cur):
    print("\n-- Crimes by Type --")
    cur.execute("SELECT crime_type, COUNT(*) FROM CRIME_REPORT GROUP BY crime_type")
    print_table(cur.fetchall(), ["Type","Count"])

    print("-- Crimes by Status --")
    cur.execute("SELECT status, COUNT(*) FROM CRIME_REPORT GROUP BY status")
    print_table(cur.fetchall(), ["Status","Count"])

# officer menu
def officer_menu(cur, conn, oid):
    while True:
        print("""
======= Officer Menu =======
    1. View Assigned Cases
    2. View Case
    3. Modify Case
    4. Assign Case
    5. Reports
    6. Logout
        """)
        c = input("Choice: ")

        if c == '1':
            cur.execute("SELECT assign_id, crime_id, officer_id, assigned_date, remarks FROM CASE_ASSIGNMENT WHERE officer_id=%s", (oid,))
            print_table(cur.fetchall(), ["assign_id","crime_id","officer_id","assigned_date","remarks"])

        elif c == '2':
            view_case(cur)

        elif c == '3':
            modify_case(cur, conn, oid)

        elif c == '4':
            assign_case(cur, conn, oid)

        elif c == '5':
            reporting_dashboard(cur)

        elif c == '6':
            print("Logged out.")
            break
        else:
            print('Invalid choice!!')
            print('Exiting')

# helpdesk menu
def helpdesk_menu(cur, conn):
    while True:
        print("""
======= Helpdesk =======
    1. File New Full Case
    2. View Case
    3. Assign Case
    4. Reports
    5. Back
        """)
        c = input("Choice: ")
        if c == '1':
            add_complainant_flow(cur, conn)
        elif c == '2':
            view_case(cur)
        elif c == '3':
            assign_case(cur, conn, None)
        elif c == '4':
            reporting_dashboard(cur)
        elif c == '5':
            break
        else:
            print('Enter a valid choice')

# main
def main():
    try:
        conn = connect()
    except mysql.connector.Error as e:
        print("Failed to connect to database:", e)
        sys.exit(1)

    # use buffered cursor to ensure fetchone() works reliably after inserts
    cur = conn.cursor(buffered=True)

    # create tables if missing (safe)
    create_tables(cur, conn)

    while True:
        print("""
        ========================== CRMS ==============================
                Welcome to Crime Record management system (CRMS)!!!!
        ==============================================================
            This project is made to manage and reduce the paper work of
                Police records, which includes registering as police officer
                        and keeping the records of registered complaints
        ==============================================================
        1. Helpdesk
        2. Officer Login
        3. Register Officer
        4. Exit
        """)
        c = input("Choice: ")

        if c == '1':
            helpdesk_menu(cur, conn)
        elif c == '2':
            oid = login_officer(cur)
            if oid:
                officer_menu(cur, conn, oid)
        elif c == '3':
            register_officer(cur, conn)
        elif c == '4':
            print("Goodbye!")
            break
        else:
            print('Invalid choice!!!')
            print('Choose again!!')

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()




