import psycopg2
import getpass
from datetime import date
from tabulate import tabulate
from psycopg2 import sql, OperationalError


# Class for handling database operations
class StudentManager:
    def __init__(self, dbname, user, password, host="localhost", port=5432):
        # Initialize database connection on init
        self.conn = None
        try:
            # Attempt connection to database
            self.conn = psycopg2.connect(
                dbname=dbname, user=user, password=password, host=host, port=port
            )
            self.cur = self.conn.cursor()
            print(f"Connected to the database {dbname}!")
        except OperationalError as e:
            # Catch any error on connect and print it
            print(f"Error connecting to the database: {e}")

    # Add to student table with given values only default is enrollment_date which
    # defaults to the current date
    def addStudent(
        self,
        first_name,
        last_name,
        email,
        enrollment_date=date.today().strftime("%Y-%m-%d"),
    ):

        # Prepare sql INSERT statement 
        # Returning value is nice for checking if the query actually completed without issue
        # and possibly doing other things with the newly created student later
        insert_query = sql.SQL(
            "INSERT INTO students (first_name, last_name, email, enrollment_date) VALUES (%s, %s, %s, %s) RETURNING student_id"
        )

        # Execute the query grabbing the fist line and first word
        data = self.executeQuery(
            insert_query,
            (
                first_name,
                last_name,
                email,
                enrollment_date,
            ),
            True,
            0,
        )

        # Attempt to commit the data on fail return nothing
        return data if self.commitEdit() else None
    
    # Get student ID and checking for its existence
    def getStudentWithID(self, student_id):
        # Simple select statement to find student with id
        select_query = sql.SQL("SELECT * FROM students WHERE student_id = %s")
        # Execute search for student with id
        data = self.executeQuery(select_query, (student_id,), True)
        if data is None:
            # Did not find student print error and return nothing
            print(f"No student found with ID: {student_id}")
            return None
        return data

    # Get all students in student table
    def getAllStudents(self):
        # Simple query to get all students (test and set var results with :=)
        if results := self.executeQuery("SELECT * FROM students"):
            # Get the column names so can be printed nicely
            columns = [desc[0] for desc in self.cur.description]
            # Return table with columns as first entry
            return [columns] + results
        return []
    # Update a student with ID given column : value pairs
    def updateStudent(self, student_id, update_values):
        # Check if update_values empty or if student with ID exits
        # Note: The reason for the student ID check is so we can print
        #       an informative message if student_id not found
        if not update_values or not self.getStudentWithID(student_id):
            return None

        # Set up UPDATE query string start
        update_query = "UPDATE students SET "
        set_values = []
        
        # Loop through update_values and put them as parameters to update
        for column, value in update_values.items():
            update_query += f"{column} = %s,"
            set_values.append(value)

        # Create final query (with last comma removed from the update_query string)
        # Return something so on successful run we have something returned to app
        sql_query = sql.SQL(
            f"{update_query[:-1]} WHERE student_id = %s RETURNING student_id"
        )
        set_values.append(student_id)

        # execute query
        data = self.executeQuery(sql_query, set_values, True, 0)
        # commit and check for commit failure
        return data if self.commitEdit() else None

    # Update student email (example to how updateStudent works)
    def updateStudentEmail(self, student_id, new_email):
        self.updateStudent(student_id, {"email": new_email})

    # Delete student with given ID
    def deleteStudent(self, student_id):
        # Mainly for informative output
        if not self.getStudentWithID(student_id):
            return None

        # Delete sql query for student for ID
        # Return for null checking on output (just in case)
        delete_query = sql.SQL(
            "DELETE FROM students WHERE student_id = %s RETURNING student_id"
        )
        # Execute query
        data = self.executeQuery(delete_query, (student_id,), True, 0)
        # commit and check for fail
        return data if self.commitEdit() else None
    
    # Execute a given query using psycopg2 execute functions
    # Made so error checking can be handled by one function and not 
    # put in every one
    def executeQuery(
        self, query, v=None, fetch_one=False, arg_num=None, no_fetch=False
    ):
        try:
            # Execute the query
            self.cur.execute(query, v)
            if no_fetch:
                # Error if we try to fetch something but there is nothing to fetch
                # Allow to skip fetching
                return []
            if fetch_one:
                # Fetch one or one argument of fetch one
                return self.cur.fetchone()[arg_num] if arg_num else self.cur.fetchone()
            # If nothing else specified assumed you want everything
            return self.cur.fetchall()
        except psycopg2.Error as e:
            # An error happened print it out
            print(f"Error executing query: {e}")
            return []

    # commit to database and error check
    def commitEdit(self):
        try:
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            print(f"Error committing to database: {e}")
            return False

    # close connection to database
    def closeConnection(self):
        if self.conn:
            self.cur.close()
            self.conn.close()
            print("Connection to the database closed.")

# Command class specifies command structure to StudentApp
class Command:
    def __init__(self, action, description):
        self.action = action
        self.description = description

# Class for user facing processes 
class StudentApp:
    # Get input from user. Does basic universal checking
    # and has capabilities to ask for password and have default values
    def getInput(self, prompt, default_value=None, is_password=False):
        try:
            while True:
                # Get user input (as password if specified)
                user_input = getpass.getpass(prompt) if is_password else input(prompt)
                if not user_input.strip() and default_value is not None:
                    return default_value # default value if input empty
                elif not user_input.strip():
                    print("Value cannot be empty.") # no default value requires a value
                else:
                    return user_input.strip() # return input string
        except KeyboardInterrupt as e:
            raise KeyboardInterrupt from e # User escaped input raise the error

    # Connect to database (get the values and initialize StudentManager class)
    def getDBConnection(self):
        while True:
            print("Running Start Up ...")
            print("#################################")
            dbname = self.getInput("Enter the database name: ")
            user = self.getInput("Enter the username: ")
            password = self.getInput("Enter the password: ", is_password=True)
            host = self.getInput("Enter the host [localhost]: ", "localhost")
            port = self.getInput("Enter the port [5432]: ", "5432")
            print("#################################\n")
            self.manager = StudentManager(dbname, user, password, host, port)
            if self.manager.conn:
                break # connection was successful no error can proceed

    def __init__(self):
        self.manager = None
        self.prompt_active = True

        # Commands list user can send to the app
        self.commands = {
            "all": Command(lambda: self.allStudents(), "View all students"),
            "add": Command(lambda *args: self.addStudent(args), "Add a new student"),
            "del": Command(
                lambda *args: self.deleteStudent(args), "Delete an existing student"
            ),
            "up": Command(
                lambda *args: self.updateStudent(args), "Update an existing student"
            ),
            "exit": Command(lambda: self.exitApp(), "Exit the program"),
            "help": Command(lambda: self.printHelpMenu(), "Show help menu"),
        }

    # Print help menu (print all command list descriptions)
    def printHelpMenu(self):
        print("\nCommands:")
        print("=================================")
        for cmd, val in self.commands.items():
            print(f"{cmd} : {val.description}")
        print("=================================\n")

    # Print header of StudentApp
    def printAppHeader(self):
        print(
            """
The Student Database Manager:
=================================
This program allows you to modify the Students table of a database
=================================
        """
        )
        self.printHelpMenu()
    
    # Prompt loop for student app allowing you to run commands
    # to manipulate the student table
    def displayApp(self):
        self.printAppHeader() # on start print header
        while self.prompt_active:
            prompt = self.getInput("[Enter Command?]> ").strip().lower().split(" ")
            command = prompt[0]

            if command in self.commands:
                if len(prompt) > 1:
                    # send other values as arguments to command functions
                    # allows for values to be read as cmd arguments
                    self.commands[command].action(*prompt[1:])
                else:
                    self.commands[command].action()
            else:
                print("Invalid command.")

    # Print add student dialog to get all values needed for function call
    def addStudent(self, args):
        try:
            # all these statements just read from the arguments and if they
            # dont exist prompt for them
            fname = args[0] if args else self.getInput("Enter student firstname: ")
            lname = (
                self.getInput("Enter student lastname: ") if len(args) < 2 else args[1]
            )
            email = self.getInput("Enter student email: ") if len(args) < 3 else args[2]
            d = (
                self.getInput(
                    "Enter enrollment date [Today]: ", date.today().strftime("%Y-%m-%d")
                )
                if len(args) < 4
                else args[3]
            )
            # call the manager to perform actual database operations
            if self.manager.addStudent(fname, lname, email, d):
                print(
                    f"Successfully added {fname} {lname} with email {email}. Enrolled on {d}!"
                )
        except KeyboardInterrupt:
            # Keyboard interrupt checking allows you to exit dialog at any time
            # Mimicing any real cmd app in theory
            print("\nExiting add student dialog...")

    # update student dialog gets inputs for updating values of student
    def updateStudent(self, args):
        try:
            # if we have long argument string (we have multiple updates)
            if len(args) > 3:
                # If odd number of args i.e not valid column : value pairs
                # try to recover by removing the last arg
                if len(args) % 2 != 0:
                    args = args[:-1]
                # Create column : value map by reading arguments in pairs
                updates = {args[i]: args[i + 1] for i in range(1, len(args) - 1, 2)}
                # perform the operation
                if self.manager.updateStudent(args[0], updates):
                    print(f"Successfully updated student {args[0]}")
            else:
                # We are building a single update statement
                # Prompt for inputs if the arguments dont exist 
                sid = (
                    args[0]
                    if args
                    else self.getInput("Enter student ID of student to update: ")
                )
                column = (
                    self.getInput("Enter value type: ") if len(args) < 2 else args[1]
                )
                val = (
                    self.getInput("Enter updated value: ") if len(args) < 3 else args[2]
                )
                # Send the column value map with student id
                if self.manager.updateStudent(sid, {column: val}):
                    print(f"Successfully updated student {sid} with {column} = {val}")
        except KeyboardInterrupt:
            print("\nExiting update student dialog...")

    # prompts for values needed to delete student
    def deleteStudent(self, args):
        try:
            sid = (
                args[0]
                if args
                else self.getInput("Enter student ID of student to delete: ")
            )
            if self.manager.deleteStudent(sid):
                print(f"Successfully deleted student {sid}!")
        except KeyboardInterrupt:
            print("\nExiting delete student dialog...")

    # Print output as table
    def printTable(self, output):
        if output:
            print(tabulate(output, tablefmt="grid"))

    # get all students and print as table!
    def allStudents(self):
        self.printTable(self.manager.getAllStudents())

    # exit app and close connection
    def exitApp(self):
        self.prompt_active = False
        self.closeConnection()

    # ask manager to close connection
    def closeConnection(self):
        if self.manager:
            self.manager.closeConnection()


if __name__ == "__main__":
    try:
        # Start app
        app = StudentApp()
        app.getDBConnection()
        app.displayApp()
    # Catch keyboard interrupts and close connection correctly before exiting
    except KeyboardInterrupt:
        print("\nExiting...")
        app.closeConnection()
