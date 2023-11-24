# COMP 3005 Assignment 4

This is a python app that connects to a database and manipulates it's students table created for a COMP 3005 assignment by Quentin Wolkensperg

## Installation

### Setting Up Database

1. Install `python3` and `postgresql` on your system
2. Run psql prompt i.e `sudo -u postgres psql`
3. Create a database i.e `CREATE DATABASE dbname;`
4. Create `students` table:

   ```sql
   CREATE TABLE students (
     student_id SERIAL PRIMARY KEY,
     first_name VARCHAR NOT NULL
     last_name VARCHAR NOT NULL
     email VARCHAR UNIQUE NOT NULL
     enrollment_date DATE
   ); 
   ```

5. Insert base data:

   ```sql
   INSERT INTO students (first_name, last_name, email, enrollment_date) VALUES
   ('John', 'Doe', 'john.doe@example.com', '2023-09-01'),
   ('Jane', 'Smith', 'jane.smith@example.com', '2023-09-01'),
   ('Jim', 'Beam', 'jim.beam@example.com', '2023-09-02');
   ```

### Installing Program

1. Clone repository
2. Create virtual python environment i.e `python -m venv venv`
3. Activate venv i.e `source venv/bin/activate`
4. Install requirements `pip install -r requirements.txt`
5. Note: if you want to deactivate the venv in your shell just run `deactivate`

## Explaination

The functions themselves are well explained in the comments. The idea of the functionality was created (overly) complex in terms of this assignment to also use this opportunity to make progress on the final project. Communication to the database and user interface are separate classes for correct encapsulation. The StudentManager class does queries to the database and the StudentApp is the user interface. The plan is to have a sort of terminal application. All the required functions are in the StudentManager. Not muc to say with the functions themselves they just use psycopg2 to perform database queries and rely on it (mostly) for outputting error information.
