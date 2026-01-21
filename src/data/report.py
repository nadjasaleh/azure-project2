from azure.storage.blob import BlobServiceClient
from config import config
import pandas as pd
import psycopg2

def report():
    con = None
    try:
        # Get the data from the database
        con = psycopg2.connect(**config())
        cursor = con.cursor()
        SQL = """
                SELECT consultant.name as consultant_name,customer.name as customer_name, shift.start_time, shift.end_time,shift.lunch_break
                FROM shift
                JOIN customer ON customer.id = shift.customer_id
                JOIN consultant on consultant.id =  shift.consultant_id;        
                """
        cursor.execute(SQL)
        data = cursor.fetchall()
        cursor.close()
        # Preprocess the data with pandas
        df = pd.DataFrame(data, columns=["consultant_name","customer_name", "start_time", "end_time", "lunch_break"])
        df['start_time'] = pd.to_datetime(df['start_time'], utc=True)
        df['end_time'] = pd.to_datetime(df['end_time'], utc=True)
        df['year'] = df['start_time'].dt.isocalendar().year
        df['week'] = df['start_time'].dt.isocalendar().week
        df['total_time'] = df['end_time'] - df['start_time']
        df.loc[df['lunch_break'] == True, 'total_time'] -= pd.Timedelta(minutes=45)
        df = df.sort_values(by=['year', 'week'], ascending=[False, False])
        # Create the report
        report_content = ""
        grouped = df.groupby(['year', 'week'], sort=False)
        for (year, week), group in grouped:
            report_content += f"Year {year}, Week {week}\n"
            for index, row in group.iterrows():
                total_seconds = row['total_time'].total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                break_text = "(45 min break)" if row['lunch_break'] else ""
                report_content += f"Consultant: {row['consultant_name']} worked with {row['customer_name']} {hours}.{minutes} min {break_text}\n"
            report_content += "\n"
        # Store the report in azure
        azure_creds = config(section='azure')
        blob_service_client = BlobServiceClient.from_connection_string(azure_creds['connect_str'])
        blob_client = blob_service_client.get_blob_client(container=azure_creds['container_name'], blob="report.txt")
        blob_client.upload_blob(report_content, overwrite=True)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if con is not None:
            con.close()

report()

