from flask import Flask, request
from query_services import *

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return {"index":True}


@app.route("/show_shifts/", methods=["GET"])
def get_shift_table():
    try:  
         return show_shifts()
    except:
        return {"error": "no data"}
    


@app.route("/new_shift",methods=["POST"])
def add_new_shifts():
    try:
        data = request.get_json()
        start_time = data["start_time"]
        end_time = data["end_time"]
        lunch_break = data["lunch_break"]
        consultant_id = data["consultant_id"]
        customer_id = data["customer_id"]
        new_shifts(start_time, end_time, lunch_break , consultant_id, customer_id)
        return {"success": "Shift added"}
    except:
        return {"error": "error in adding shift"}



# http://127.0.0.1:5000/show_shifts
# http://127.0.0.1:5000/new_shift


if __name__ == "__main__":
    app.run()