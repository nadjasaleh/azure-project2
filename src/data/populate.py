from faker import Faker
from config import config
import psycopg2
import random
from datetime import timedelta

fake = Faker()
Faker.seed(333)

def clean_database(con: psycopg2.extensions.connection):
    print("--- FRESH START: Cleaning database ---")
    tables = ['shift','consultant','customer']
    with con.cursor() as cur:
        for table in tables:
            cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
    con.commit()

def populate_consultant(con: psycopg2.extensions.connection, n: int):
    print(f'Populating {n} consultants')
    with con.cursor() as cur:
        for _ in range(n):
            cur.execute("""
                INSERT INTO consultant (name, email) 
                VALUES (%s, %s);
            """, (fake.unique.name(), fake.unique.email()))
    con.commit()

def populate_customer(con: psycopg2.extensions.connection, n: int):
    print(f'Populating {n} customers')
    with con.cursor() as cur:
        for _ in range(n):
            cur.execute("""
                INSERT INTO customer (name)
                VALUES (%s)
            """, (fake.company(),))
    con.commit()

def populate_shift(con: psycopg2.extensions.connection, n: int):
    print(f'Populating {n} shifts')
    with con.cursor() as cur:
        cur.execute("SELECT id FROM customer;") 
        customer_ids = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT id FROM consultant;") 
        consultant_ids = [row[0] for row in cur.fetchall()]
        
        if not customer_ids:
            print("Error: No customers.")
            return
        if not consultant_ids:
            print("Error: No consultants.")
            return

        for _ in range(n):
            start_time = fake.date_time_between(start_date='-5y', end_date='-1w')
            end_time = fake.date_time_between(start_date=start_time + timedelta(hours=1), end_date=start_time + timedelta(hours=12))
            lunch_break = fake.pybool(truth_probability=80)
            consultant_id = random.choice(consultant_ids)
            customer_id = random.choice(customer_ids)

            cur.execute("""
                INSERT INTO shift (start_time, end_time, lunch_break, consultant_id, customer_id) 
                VALUES (%s, %s, %s, %s, %s)
            """, (start_time, end_time, lunch_break, consultant_id, customer_id))
    con.commit()

def print_database(con: psycopg2.extensions.connection):
    print("\n--- CONSULTANTS ---")
    with con.cursor() as cur:
        cur.execute("""
            SELECT id, name, email
            FROM consultant
            ORDER BY id;
        """)
        for row in cur.fetchall():
            print(row)

    print("\n--- CUSTOMERS ---")
    with con.cursor() as cur:
        cur.execute("""
            SELECT id, name
            FROM customer
            ORDER BY id;
        """)
        for row in cur.fetchall():
            print(row)

    print("\n--- SHIFTS (joined view) ---")
    with con.cursor() as cur:
        cur.execute("""
            SELECT s.id,
                   s.start_time,
                   s.end_time,
                   s.lunch_break,
                   c.name AS consultant,
                   cu.name AS customer
            FROM shift s
            JOIN consultant c ON c.id = s.consultant_id
            JOIN customer cu ON cu.id = s.customer_id
            ORDER BY s.id;
        """)
        for row in cur.fetchall():
            print(row[0],row[1],row[2],'(',row[2]-row[1],')',row[3],row[4],row[5])

def main():
    con = None
    try:
        con = psycopg2.connect(**config())
        if con:
            clean_database(con)
            populate_consultant(con, 20) 
            populate_customer(con, 5)
            populate_shift(con, 40)
            print_database(con)
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        if con is not None:
            con.close()

if __name__=="__main__":
    main()