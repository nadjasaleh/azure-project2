from psycopg2.extras import RealDictCursor
from config import config
import psycopg2
import json


def show_shifts():
    con = None
    try:
        con = psycopg2.connect(**config())
        cursor = con.cursor(cursor_factory=RealDictCursor)
        SQL = 'SELECT * FROM shift LIMIT 5;'
        cursor.execute(SQL)
        data = cursor.fetchall()
        cursor.close()
        #return json.dumps({"shift_list": data})
        return json.dumps(data, default=str)
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if con is not None:
            con.close()



def new_shifts(start_time, end_time, lunch_break , consultant_id, customer_id):
    con = None
    try:
        con = psycopg2.connect(**config())
        cursor = con.cursor(cursor_factory=RealDictCursor)
        SQL = """
        INSERT INTO shift (start_time, end_time, lunch_break , consultant_id, customer_id) 
        VALUES (%s,%s,%s,%s,%s);
        """
        cursor.execute(SQL,(start_time, end_time, lunch_break , consultant_id, customer_id))
        con.commit()
        cursor.close()
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        raise error
    finally:
        if con is not None:
            con.close()
