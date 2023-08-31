import pymongo
from flask import request
import bcrypt

client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')
userdbtest = client['userdbtest']
users = userdbtest.customers

def insert_data():
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		password = request.form['pass']

		reg_user = {}
		reg_user['name'] = name
		reg_user['email'] = email
		reg_user['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

		if users.find_one({"email":email}) == None:
			users.insert_one(reg_user)
			return True
		else:
			return False



def check_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pass']

        user = users.find_one({"email": email})

        if user is None:
            return False, ""
        else:
            if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
                return True, user["name"]
            else:
                return False, ""

def check_password(username, password):
    user = users.find_one({"name": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        return True
    return False

def update_password(username, new_password):
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    users.update_one({"name": username}, {"$set": {"password": hashed_password}})
