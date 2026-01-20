from flask import Flask
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

# http://127.0.0.1:5000/show_shifts

if __name__ == "__main__":
    app.run()