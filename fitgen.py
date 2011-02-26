################################################################################
# fitgen.py                                                                    #
# by Justin Hamilton                                                           #
#                                                                              #
# This is super hacky. I am only able to work on this in my free time, so I am #
# currently trying to get a working 'prototype' up before I refine the code    #
# and make it more  presentable                                                #
################################################################################
import sqlite3
import hashlib
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from random import randint

# configuration
# obviously, change most of these 
DATABASE = './fitgen.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'password'
SALT = "s3cret_s@lt" 
equip_list = ['barbell', 'dumbell', 'kettlebell', 'bench',
              'rack', 'pullup', 'box', 'jumprope', 'bike',
              'rower', 'elliptical', 'climber', 'pool', 'exercise_ball', 
              'medicine_ball', 'leg_press', 'leg_extension', 'glute_ham_chair', 
              'smith_machine']
type_list = ['weights', 'bodyweight', 'cardio']
muscle_dict = {"upper": ['back', 'arms', 'chest'],
               "lower": ['legs'],
               "full": ['back', 'arms', 'chest', 'legs', 'core']}


# build our application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FITGEN_SETTINGS', silent=True)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

@app.before_request
def before_request():
    g.db = connect_db()

@app.after_request
def after_request(response):
    g.db.close()
    return response

@app.route('/cpanel', methods=['GET', 'POST'])
def cpanel():
    """registered user's control panel"""
    global equip_list
    query = ""
    owned_list = []
    return render_template('cpanel.html', error=None)

    try:
        if session['logged_in']:
            for x in equip_list:
                query += x + ','
            query = "SELECT " + query[:len(query) - 1] + " FROM users WHERE login_name='" + \
            str(session['username']) + "';"            
            exc = query_db(query)
            return render_template('cpanel.html')
    except:
        return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if session['logged_in']:
            return redirect(url_for('cpanel'))
    except:
        pass
    error = None
    if request.method == 'POST':
        exc = query_db("SELECT id, password, user_role, email FROM users " +
                       " WHERE login_name='" + request.form['username'] + 
                       "' LIMIT 1;")

        # generate a sha1 hash for password verification, and then add the 
        # user id plus our salt to the password, you may want to use similar
        # but different methods if you go this route for verification
        comp_hash = hashlib.sha1()
        comp_hash.update(str(exc[0]['id']) + request.form['password'] + SALT)
        comp_pass = comp_hash.hexdigest()
        if comp_pass != exc[0]['password']:
            error = 'Invalid username or password'
            # throw away the password information asap, just in case
            del(comp_hash)
            del(comp_pass)
            del(exc[0]['password'])
        else:
            # I should probably integrate the session stack with a user object
            session['logged_in'] = True
            session['username'] = request.form['username']
            session['email'] = exc[0]['email']
            session['role'] = exc[0]['user_role']
            flash('You were logged in')
            # throw away the password info just in case
            del(comp_hash)
            del(comp_pass)
            del(exc[0]['password'])
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/termsofservice')
def termsofservice():
    return render_template('termsofservice.html')

@app.route('/logout')
def logout():
    """pops the user's information off of the session stack and returns
    a flash message stating this has been done"""
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('email', None)
    session.pop('role', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """enters user information into the database"""
    error = None
    if request.method == 'POST':
        # verify passwords
        if request.form['password1'] != request.form['password2']:
            error = "Passwords do not match"
        # verify email
        if request.form['email1'] != request.form['email2']:
            error = "Email does not match"
        
        # if the previous validations pass, check if the username is used
        exc = query_db("SELECT login_name FROM users WHERE login_name='" + 
                       request.form['username'] + "' LIMIT 1;")
        if exc:
            error = "Username already in use"
        
        # see if the email is already registered
        exc = query_db("SELECT email FROM users where email='" + 
                       request.form['email1'] +  "' LIMIT 1;")
        if exc:
            error = "User already registered with that email address"
        # if all succeeds so far, enter the user db
        if error == None:
            exc = query_db("SELECT count(*) FROM users;")
            count = exc[0]['count(*)']
            user_hash = hashlib.sha1()
            user_hash.update(str(count + 1) + request.form['password1'] + SALT)
            user_pass = user_hash.hexdigest()
            try:
                g.db.execute("INSERT INTO users (login_name, email, password, " + 
                             "user_role) values (?, ?, ?, ?)", 
                             [request.form['username'], request.form['email1'], 
                             user_pass, 'user'])
                g.db.commit()
                # delete the password asap
                del(user_hash)
                del(user_pass)
                flash("New user " + request.form['username'] + " registered.")
            except:
                error = "error inserting into database"
    return render_template('register.html', error=error)

@app.route('/workout', methods=['POST'])
def random_workout():    
    """the logic behind the random workout"""
    if request.method == 'POST':
        global equip_list, muscle_dict, type_list
        equip_exclude = []
        type_include = []
        
        # build the list of equipment to exclude
        for x in equip_list:
            try:
                if request.form[x]:
                    pass
            except:
                equip_exclude.append(x)

        # build list of types to include
        for x in type_list:
            try:
                if request.form[x]:
                    type_include.append(x)
            except:
                pass        

        # try to get the query and build the exercises
        try:
            if request.form['force'] == 'both':
                force_str = None
            else:
                force_str = [request.form['force']]
            limit = request.form['num_exercises']
            query = build_query(muscle_dict[request.form['muscles']],
                        type_include, equip_exclude, force_str, limit)
            exc = query_db(query, one=False)
            entries = []
            for x in exc:
                entries.append(x['workout_name'])
        except:
            entries=["error_raised"]
    return render_template('show_exercises.html', entries=entries)
    
def build_query(muscles=[], types=[], equip=[], force=None, limit=1):
    """takes a list of muscles, workout types, equipment to exclude
    and the number of exercises to generate in a workout, returning the 
    sql query neccessary to build a workout"""

    query = "SELECT workout_name FROM exercises WHERE ("    

    # add the muscle selection(s) to the query
    for i in range(0, len(muscles)):       
        if i != 0:
            query += " OR "
        query += "muscles='" + muscles[i] + "'"
    query += " OR muscles='other')"

    # add the workout type to the query
    if len(types) > 0:
        query += " AND ("
        for i in range(0, len(types)):           
            if i != 0:
                query += " OR "
            query += "workout_type='" + types[i] + "'"
        query += ")"

    # add the force, if any, to the query
    if force != None:
        query += " AND (force='" + force + "' OR force='other')"

    # add the equipment filter
    if len(equip) > 0:
        query += " AND ("
        for i in range(0, len(equip)):
            if i != 0:
                query += " AND "
            query += equip[i] + " != 1" 
        query += ') ORDER BY RANDOM() LIMIT ' + str(limit) + ";"
    
    # print the query for shoddy debugging purposes and then
    print query
    return query      

if __name__ == '__main__':
    app.run()
