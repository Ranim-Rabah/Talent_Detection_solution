from flask import Flask,render_template
from auth import auth
from dash import dash
from scraping import scraping
from waitress import serve
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.register_blueprint(auth)
app.register_blueprint(dash)
app.register_blueprint(scraping)

@app.route('/home', methods = ['GET', 'POST'])
def homefun():
    return render_template("base.html")

if __name__ == '__main__':
    app.run(debug=True)