from flask import Flask, render_template, session, redirect, url_for, jsonify, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from google.appengine.ext import ndb
from datetime import datetime
import json
import time
import random
import hashlib

# client = MongoClient('mongodb://admin:admin2018@ds251598.mlab.com:51598/protectedu')
# db = client.protectedu
# collection = db.users

app = Flask(__name__)

class User(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    studentid = ndb.StringProperty()
    salt = ndb.StringProperty()

    # @classmethod
    # def query_book(cls, primaryKey):
    #     return cls.query(ancestor=ancestor_key).order(-cls.date)


class PendingUser(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    studentid = ndb.StringProperty()
    salt = ndb.StringProperty()
    vcode = ndb.StringProperty()
    time = ndb.DateTimeProperty(auto_now_add=True)    

    # @classmethod
    # def query(cls, name, vcode):

class MaxID(ndb.Model):
    maxID = ndb.IntegerProperty()



@app.route('/first',methods=['GET'])
def first():
    maxID = MaxID(maxID=1)
    maxID.put()
    return 'success\r\n', 201


@app.route('/find', methods=['GET'])
def find():
    respond = {}

    try:
        data = json.loads(request.args['data'])
    except ValueError, e:
        print 'ValueError'
        respond['result'] = 'false'
        respond['message'] = 'Not json string'
        return json.dumps(respond), 200, {'ContentType':'text/plain'} 
    else:
        pass


    if 'name' not in data or 'email' not in data:
        respond['result'] = 'false'
        respond['message'] = 'No name or email'        
        return json.dumps(respond), 200, {'ContentType':'text/plain'} 

    name = data['name']
    email = data['email']

    user=User.query(User.name==name, User.email==email).fetch(1)

    if user == None or user == []:
        respond['result'] = 'false'
        respond['message'] = 'Cannot find user'  
        return json.dumps(respond), 200, {'ContentType':'text/plain'} 

    print user

    user = user[0]

    print user

    respond['result'] = "true"
    respond['primaryKey'] = user.key.urlsafe()
    respond['studnetID'] = user.studentid
    respond['salt'] = user.salt

    return json.dumps(respond), 200, {'ContentType':'text/plain'} 

@app.route('/retrieve', methods=['GET'])
def retrieve():
    respond = {}

    try:
        data = json.loads(request.args['data'])
    except ValueError, e:
        print 'ValueError'
        respond['result'] = 'false'
        respond['message'] = 'Not json string'
        return json.dumps(respond), 200, {'ContentType':'text/plain'}     
    else:
        pass

    if 'primaryKey' not in data:
        respond['result'] = 'false'
        respond['message'] = 'Not primaryKey'
        return json.dumps(respond), 200, {'ContentType':'text/plain'}    

    primaryKey = data['primaryKey']

    user=ndb.Key(urlsafe=primaryKey).get()
    if user == None:
        respond['result'] = 'false'
        respond['message'] = 'Cannot find user'
        return json.dumps(respond), 200, {'ContentType':'text/plain'} 
   

    respond['result'] = "true"
    respond['primaryKey'] = primaryKey
    respond['name'] = user.name
    respond['email'] = user.email
    respond['studnetID'] = user.studentid
    respond['salt'] = user.salt


    return json.dumps(respond), 200, {'ContentType':'text/plain'} 




@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/verifyid', methods=['GET'])
def verifyID():
    respond = {}

    try:
        data = json.loads(request.args['data'])
    except ValueError, e:
        print 'ValueError'
        respond['result'] = 'false'
        respond['message'] = 'Not json string'
        return json.dumps(respond), 200, {'ContentType':'text/plain'}    
    else:
        pass


    if 'primaryKey' not in data or 'IDHash' not in data:
        respond['result'] = 'false'
        respond['message'] = 'No primaryKey or IDHash'
        return json.dumps(respond), 200, {'ContentType':'text/plain'}  

    primaryKey = data['primaryKey']
    IDHash = data['IDHash']

    user=ndb.Key(urlsafe=primaryKey).get()
    if user == None:
        respond['result'] = 'false'
        respond['message'] = 'Cannot find user'
        return json.dumps(respond), 200, {'ContentType':'text/plain'}  

    print user

    id = user.studentid
    time = timeString()
    salt = str(user.salt)
    hash = hashID(id, time, salt)


    if hash != IDHash:
        if inRange():
            time = timeString(current=0)
            hash = hashID(id, time, salt)
            if hash != IDHash:
                return '{"result":"false", "message":"Incorrect IDHash"}', 200, {'ContentType':'text/plain'}  
        else:
            return '{"result":"false", "message":"Incorrect IDHash"}', 200, {'ContentType':'text/plain'}


    respond = {}
    respond['result'] = "true"
    respond['name'] = user.name
    respond['email'] = user.email 


    return json.dumps(respond), 200, {'ContentType':'text/plain'} 
 


@app.route('/createuser', methods=['GET']) #change back to GET
def createUser():

    respond = {}

    try:
        data = json.loads(request.args['data'])
    except ValueError, e:
        print 'ValueError'
        respond['result'] = 'false'
        respond['message'] = 'Not json string'
        return json.dumps(respond), 200, {'ContentType':'text/plain'} 
    else:
        pass

    print 'Create user data: \n'
    print data

    if 'name' not in data or 'email' not in data:
        respond['result'] = 'false'
        respond['message'] = 'No name or email'
        return json.dumps(respond), 200, {'ContentType':'text/plain'} 

    name = data['name']
    email = data['email']

    if name==None or email==None or '@' not in email:
        respond['result'] = 'false'
        respond['message'] = 'Bad Input'
        return json.dumps(respond), 200, {'ContentType':'text/plain'} 

    id = createStudentID() 
    print 'Successfully create ID'

    vcode = str("%06d"%random.randint(0, 1000000))
    salt = str(hex(random.getrandbits(64)))
    timestamp = time.time()

    newStudent = PendingUser(
        name=name,
        email=email,
        studentid=id,
        salt=salt,
        vcode=vcode)

    primaryKey=newStudent.put().urlsafe()

    respond['result'] = 'true'
    respond['name'] = name
    respond['vcode'] = vcode


    return json.dumps(respond), 201, {'ContentType':'text/plain'} 




@app.route('/verifyuser', methods=['GET'])
def verifyUser():
    respond = {}

    try:
        data = json.loads(request.args['data'])
    except ValueError, e:
        print 'ValueError'
        respond['result'] = 'false'
        respond['message'] = 'Not json string'
        return json.dumps(respond), 200, {'ContentType':'text/plain'} 
    else:
        pass

    if 'vcode' not in data:
        respond['result'] = 'false'
        respond['message'] = 'No vcode'
        return json.dumps(resopnd), 200, {'ContentType':'text/plain'}

    vcode = data['vcode']


    puser = PendingUser.query(PendingUser.vcode==vcode).fetch(1)

    if puser == [] or puser == None:
        respond['result'] = 'false'
        respond['message'] = 'Cannot find such user'
        return json.dumps(respond), 200, {'ContentType':'text/plain'}


    puser = puser[0]



    timelapsed = (datetime.now()-puser.time).total_seconds()


    if puser.vcode != vcode:
        respond['result'] = 'false'
        respond['message'] = 'Cannot find such user'
        return json.dumps(respond), 200, {'ContentType':'text/plain'}

    if timelapsed > 300:
        puser.key.delete()
        respond['result'] = 'false'
        respond['message'] = 'Over the time limit'
        return json.dumps(respond), 200, {'ContentType':'text/plain'}


    user = User(        
        name=puser.name,
        email=puser.email,
        studentid=puser.studentid,
        salt=puser.salt)

    primaryKey = user.put().urlsafe()
    puser.key.delete()

    respond = {}

    respond['result'] =  'true'
    respond['primaryKey'] = primaryKey
    respond['studnetID'] = user.studentid
    respond['salt'] = user.salt



    return json.dumps(respond), 202, {'ContentType':'text/plain'} 



def timeString(current=1):
    t = int(time.time()/60 - (1-current))
    result = []
    for i in range(0, 8):
        result.append(t >> (i*8)&0xff)
    result.reverse()
    result = ''.join(chr(i) for i in result)
    return result    

def inRange():
    return time.time()%60 <= 5


def createStudentID():

    print 'In create student ID'

    maxID = MaxID.query().fetch(1)[0]
    max = maxID.maxID
    maxID.maxID = max+1
    maxID.put()

    print 'Successfully access database'

    id = str("%07d"%max)

    sum = max%10*2
    max /= 10
    for i in range(3):
        sum += max%10
        max /=10
        sum += max%10*2
        max /=10

    id = str(sum%10) + '0' + id
    return id


def hashID(id, time, salt):
    h = hashlib.sha256()
    h.update(id)
    h.update(time)
    h.update(salt)
    return h.hexdigest()





