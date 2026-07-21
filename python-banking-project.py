
print("This program requires the MySQL Connector for Python to communicate with the SQL database. The program cannot run unless it is installed.")
print("Please confirm whether the required connector is installed.")
choice = input("Enter 'Y' if it is installed, or 'N' if it is not (Y/N): ").strip().lower()

if choice == 'y':
    import mysql.connector as mysql
    from mysql.connector import Error
    import random
# ============================
# PASSWORD CHECKER
# ============================
    def get_password_input(prompt):
        """Ask password with 3 attempts"""
        for i in range(3):
            pwd = input(prompt)
            if pwd.strip() != "":
                return pwd
            print("Password cannot be empty. Try again.")
        print("Too many invalid attempts.")
        return None
        

# ============================
# DATABASE INITIALIZER
# ============================
    def initialize_database():
        print("\n--- DATABASE SETUP ---")
        host_name = input("Enter MySQL Host (e.g., localhost or IP): ")
        root_user = input("Enter MySQL Root/Admin Username: ")
        root_password = input("Enter MySQL Password for the Admin User: ")
        try:
            connection = mysql.connect(
                host=host_name,
                user=root_user,
                passwd=root_password,
                charset="utf8"
            )
            if not connection.is_connected():
                raise Error("Unable to connect to MySQL server.")
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS banking")
            connection.commit()
            connection.database = "banking"
            # FIX: UNSIGNED BIGINT so 9 or 10 digit numbers never fail
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS project (
                Accountname VARCHAR(30) NOT NULL,
                Accountnumber BIGINT UNSIGNED PRIMARY KEY,
                Password VARCHAR(30) NOT NULL,
                Balance INT DEFAULT 0,
                Recovery_Key INT
            )
            """)
            connection.commit()
            print("\nDatabase and table setup completed successfully.")
            return connection
        except Error as e:
            print(f"\nFATAL DATABASE ERROR DURING SETUP: {e}")
            return None


# ============================
# BANKING FUNCTIONS
# ============================
    def create_account(conn):
        cursor = conn.cursor()
        name = input("Enter Account Name: ")
        # SAFE 10-digit account number
        while True:
            acc_no = random.randint(1000000000, 9999999999)
            cursor.execute("SELECT Accountnumber FROM project WHERE Accountnumber=%s", (acc_no,))
            if not cursor.fetchone():
                break
        print(f"Generated Account Number: {acc_no}")
        pwd = get_password_input("Set Password: ")
        if pwd is None:
            print("Account creation cancelled.\n")
            return
        print('''
Very Imprortant Message :
Upon account creation, a one-time 4-digit recovery key will be provided.
This key is essential for password recovery and will only be displayed once.
"Please ensure you securely record and retain this key, as it is the sole means to regain access to your account in the event of a forgotten password."
Without this key, password recovery will not be possible, and access to the account cannot be restored.''')

        recovery_key = random.randint(1000,9999)
        print()
        print("4 Digit Recovery Key :",recovery_key)

        cursor.execute(
            "INSERT INTO project (Accountname, Accountnumber, Password, Balance, Recovery_Key) VALUES (%s, %s, %s, %s, %s)",
            (name, acc_no, pwd, 0, recovery_key)
        )
        conn.commit()
        print()
        print("Account created successfully!\n")
    def login(conn):
        cursor = conn.cursor()
        try:
            acc_no = int(input("Enter Account Number: "))
        except:
            print("Invalid account number format.\n")
            return None

        for attempt in range(3):
            pwd = input("Enter Password: ")

            cursor.execute(
                "SELECT * FROM project WHERE Accountnumber=%s AND Password=%s",
                (acc_no, pwd)
            )

            data = cursor.fetchone()

            if data:
                print(f"\nWelcome {data[0]}!")
                return acc_no

            print("Incorrect Password.")

            recovery = input("Forgot Password? (y/n): ").lower()

            if recovery == "y":
                print("Too many failed login attempts.")

                recovery = input("Forgot Password (y/n): ").lower()

                if recovery == "n":
                    print("Login cancelled.\n")
                    return None

                elif recovery == "y":

                    print("""
In order to reset your password
and gain access to your account again.
Kindly enter your Recovery Key.
(It was the 4 Digit Key which was provided to you when you created the account.)
    """)

                    try:
                        recover = int(input("Enter the Key: "))
                    except:
                        print("Invalid Recovery Key.")
                        return None

                    cursor.execute(
                        "SELECT Recovery_Key FROM project WHERE Accountnumber=%s",
                        (acc_no,)
                    )

                    data = cursor.fetchone()

                    if data is None:
                        print("Account not found.")
                        return None

                    if recover != data[0]:
                        print("Wrong Recovery Key.")
                        return None

                    # Recovery key matched
                    for attempt in range(2):

                        new_password = input("Enter your New Password: ")
                        confirm = input("Confirm Password: ")

                        if new_password == confirm:

                            cursor.execute(
                                "UPDATE project SET Password=%s WHERE Accountnumber=%s",
                                (new_password, acc_no)
                            )

                            conn.commit()

                            print("Password Updated Successfully.\n")
                            return None

                        else:
                            if attempt == 0:
                                print("Passwords do not match. One attempt remaining.")
                            else:
                                print("Passwords do not match. Password recovery failed.\n")
                                return None

                else:
                    print("Invalid choice.")
                    return None

            elif recovery != "n":
                print("Invalid choice.")

        print("Too many failed login attempts.\n")
        return None
    def  verify_password(conn, acc_no):
        """Before withdraw, deposit, view balance, delete — verify password"""
        cursor = conn.cursor()
        for attempt in range(3):
            pwd = input("Enter your password again: ")
            cursor.execute("SELECT Password FROM project WHERE Accountnumber=%s", (acc_no,))
            correct_pwd = cursor.fetchone()[0]
            if pwd == correct_pwd:
                return True
            print("Incorrect password. Try again.")
        print("Too many incorrect password attempts.\n")
        return False

    def check_balance(conn, acc_no):
        if not verify_password(conn, acc_no):
            return
        cursor = conn.cursor()
        cursor.execute("SELECT Balance FROM project WHERE Accountnumber=%s", (acc_no,))
        balance = cursor.fetchone()[0]
        print(f"Your Current Balance: ${balance}\n")

    def deposit(conn, acc_no):
        if not verify_password(conn, acc_no):
            return
        cursor = conn.cursor()
        try:
            amt = int(input("Enter amount to deposit: "))
        except ValueError:
            print("invalid")
            return

        if amt > 999999999:
            print("Cannot deposit more than $ 999999999.")
            return

        cursor.execute("SELECT Balance FROM project WHERE Accountnumber=%s", (acc_no,))
        balance = cursor.fetchone()[0]

        if balance + amt > 999999999:
            print("Cannot deposit more than $ 999999999.")
        else:
            cursor.execute("UPDATE project SET Balance = Balance + %s WHERE Accountnumber=%s", (amt, acc_no))
            conn.commit()
            print("Amount deposited successfully.\n")   
    def withdraw(conn, acc_no):
        if not verify_password(conn, acc_no):
            return
        cursor = conn.cursor()
        try:
            amt = int(input("Enter amount to withdraw: "))
        except ValueError:  
            print("invalid")
            return
        cursor.execute("SELECT Balance FROM project WHERE Accountnumber=%s", (acc_no,))
        balance = cursor.fetchone()[0]
        if amt > balance:
            print("Insufficient Balance!\n")
        else:
            cursor.execute("UPDATE project SET Balance = Balance - %s WHERE Accountnumber=%s", (amt, acc_no))
            conn.commit()
            print("Withdrawal Successful.\n")
    def delete_account(conn, acc_no):
        if not verify_password(conn, acc_no):
            return False
        cursor = conn.cursor()
        confirm = input("Are you sure you want to delete your account? (yes/no): ")
        if confirm.lower() == "yes":
            cursor.execute("DELETE FROM project WHERE Accountnumber=%s", (acc_no,))
            conn.commit()
            print("Account deleted successfully.\n")
            return True
        else:
            print("Deletion cancelled.\n")
            return False

    def update_name(conn, acc_no):
        if not verify_password(conn, acc_no):
            return
        cursor = conn.cursor()
        new_name = input("Enter New Name: ")
        cursor.execute("UPDATE project SET Accountname = %s WHERE Accountnumber = %s" , (new_name, acc_no))
        conn.commit()
        print("Name updated successfully.\n")

    # ============================
    # MAIN PROGRAM
    # ============================
    def main():
        conn = initialize_database()
        if conn is None:
            print("Program terminated due to database failure.")
            return
        while True:
            print("""
====== BANKING SYSTEM ======
1. Create Account
2. Login
3. Exit
""")
            choice = input("Enter your choice: ")
            if choice == "1":
                create_account(conn)
            elif choice == "2":
                acc_no = login(conn)
                if acc_no:
                    while True:
                        print("""
---- ACCOUNT MENU ----
1. Check Balance
2. Deposit
3. Withdraw
4. Update Name
5. Delete Account
6. Logout
""")
                        c = input("Enter option: ")
                        if c == "1":
                            check_balance(conn, acc_no)
                        elif c == "2":
                            deposit(conn, acc_no)
                        elif c == "3":
                            withdraw(conn, acc_no)
                        elif c == "5":
                            if delete_account(conn, acc_no):
                                break
                        elif c == "6":
                            print("Logged out.\n")
                            break
                        elif c == "4":
                            update_name(conn, acc_no)
                        else:
                            print("Invalid option.\n")
            elif choice == "3":
                print("Exiting Program...")
                break
            else:
                print("Invalid input. Try again.\n")

    if __name__ == "__main__":
        main()

elif choice == 'n':
    print("""
The MySQL Connector for Python is not installed.

This application requires the MySQL Connector for Python to communicate with the database.
The program cannot continue until the required package is installed.

Installation Instructions:
1. Open Command Prompt (Windows) or Terminal (macOS/Linux).
2. Run the following command:

   pip install mysql-connector-python

3. Wait for the installation to complete successfully.
4. Restart and run this program again.

Thank you.
""")

else:
    print("Invalid Choice Entered")

    

