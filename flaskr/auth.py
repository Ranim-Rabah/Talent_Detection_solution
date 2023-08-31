import db
import json
from flask import render_template,Blueprint,session,redirect,url_for,request

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/signin', methods = ['GET', 'POST'])
def home():
    return render_template("auth/signin.html")


@auth.route('/signup', methods = ['GET', 'POST'])
def signup():
    return render_template("auth/signup.html")


@auth.route('/change_password', methods = ['GET', 'POST'])
def change_password():
    return render_template("auth/change_password.html")


@auth.route('/login', methods = ['GET', 'POST'])
def login():
    status, username = db.check_user()

    if status:
        session['username'] = username
        redirect(url_for('auth.protected'))  

    data = {
        "username": username,
        "status": status
    }
    return json.dumps(data)


from flask import g
@auth.route('/protected')
def protected():
    if 'username' in session:
        g.user = session['username']
        return render_template("base.html", user=g.user)
    return redirect(url_for('auth.login'))


@auth.route('/register', methods = ['GET', 'POST'])
def register():
    status = db.insert_data()
    return json.dumps(status)

@auth.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('auth.home'))

@auth.route('/change', methods=['GET', 'POST'])
def change():
    if request.method == 'POST':
        current_password = request.form['password']
        new_password = request.form['newpassword']
        reentered_password = request.form['renewpassword']

        # Check if the new password and reentered password match
        if new_password != reentered_password:
            return render_template("auth/change_password.html", error="Passwords do not match")

        # Check if the current password matches the user's actual password (you need to implement this)
        if not db.check_password(session['username'], current_password):
            return render_template("auth/change_password.html", error="Current password is incorrect")

        # Check password length requirement
        if len(new_password) < 6:
            return render_template("auth/change_password.html", error="Password must be at least 6 characters long")

        # Update the user's password (you need to implement this)
        db.update_password(session['username'], new_password)

        return render_template("auth/change_password.html", success="Password changed successfully")

    return render_template("auth/change_password.html")

