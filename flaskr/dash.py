
from flask import render_template,Blueprint,send_file
from pymongo import MongoClient
import pandas as pd
import xlsxwriter

dash = Blueprint('dash', __name__)

@dash.route('/history', methods = ['GET', 'POST'])
def history():
    target_collection_prefix = "Talents : " 
    collection_names = [name for name in db.list_collection_names() if name.startswith(target_collection_prefix)]
    return render_template("dash/history.html", collection_names=collection_names)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['userdbtest']  # Replace with your database name

@dash.route('/download/<collection_name>')
def download_excel(collection_name):
    # Retrieve data from MongoDB collection
    collection = db[collection_name]
    cursor = collection.find({})
    data = list(cursor)

    # Create a DataFrame from MongoDB data
    df = pd.DataFrame(data)

    # Create an Excel writer object
    excel_writer = pd.ExcelWriter('C:/Users/r.rabah/Desktop/front_project - integration/data/data.xlsx', engine='xlsxwriter')

    # Write the DataFrame to the Excel file
    df.to_excel(excel_writer, sheet_name='Sheet1', index=False)

    # Save the Excel file
    excel_writer.close()

    # Send the Excel file to the user for download
    return send_file('C:/Users/r.rabah/Desktop/front_project - integration/data/data.xlsx', as_attachment=True)
