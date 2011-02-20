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

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        exc = query_db("SELECT id, password FROM users WHERE login_name='" + 
                       request.form['username'] + "' LIMIT 1;")
        comp_hash = hashlib.sha1()
        comp_hash.update(str(exc[0]['id']) + request.form['password'] + SALT)
        comp_pass = comp_hash.hexdigest()
        if comp_pass != exc[0]['password']:
            error = 'Invalid username or password'
            del(comp_hash)
            del(comp_pass)
        else:
            session['logged_in'] = True
            flash('You were logged in')
            del(comp_hash)
            del(comp_pass)
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if request.form['password1'] != request.form['password2']:
            error = "Passwords do not match"
        if request.form['email1'] != request.form['email2']:
            error = "Email does not match"
        
        exc = query_db("SELECT login_name FROM users WHERE login_name='" + 
                       request.form['username'] + "' LIMIT 1;")
        if exc:
            error = "Username already in use"

        exc = query_db("SELECT email FROM users where email='" + request.form['email1'] + 
                       "' LIMIT 1;")
        if exc:
            error = "User already registered with that email address"
        
        if error == None:
            exc = query_db("SELECT count(*) FROM users;")
            count = exc[0]['count(*)']
            user_hash = hashlib.sha1()
            user_hash.update(str(count + 1) + request.form['password1'] + SALT)
            user_pass = user_hash.hexdigest()
            try:
                g.db.execute('INSERT INTO users (login_name, email, password, user_role)' +
                             ' values (?, ?, ?, ?)', [request.form['username'], 
                                                     request.form['email1'], 
                                                     user_pass, 'user'])
                g.db.commit()
                del(user_hash)
                del(user_pass)
                flash("New user " + request.form['username'] + " registered.")
            except:
                error = "error inserting into database"
    return render_template('register.html', error=error)

@app.route('/workout', methods=['POST'])
def random_workout():    
    if request.method == 'POST':
        equip_list = ['barbell', 'dumbell', 'ketllebell', 'bench',
                      'rack', 'pullup', 'box', 'jumprope', 'bike',
                      'rower', 'elliptical', 'climber', 'pool']
        equip_exclude = []
        muscle_dict = {"upper": ['back', 'arms', 'chest'],
                       "lower": ['legs'],
                       "full": ['back', 'arms', 'chest', 'legs', 'core']}
        type_list = ['weights', 'bodyweight', 'cardio']
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
            limit = request.form['num_exercises']
            query = build_query(muscle_dict[request.form['muscles']],
                        type_include, equip_exclude, request.form['force'], limit)
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
    
    for i in range(0, len(muscles)):       
        if i != 0:
            query += " OR "
        query += "muscles='" + muscles[i] + "'"
    query += " OR muscles='other')"
    if len(types) > 0:
        query += " AND ("
        for i in range(0, len(types)):           
            if i != 0:
                query += " OR "
            query += "workout_type='" + types[i] + "'"
        query += ")"
    if force != None:
        query += " AND (force='" + force + "' OR force='other')"
    if len(equip) > 0:
        query += " AND ("
        for i in range(0, len(equip)):
            if i != 0:
                query += " AND "
            query += equip[i] + " != 1" 
        query += ') ORDER BY RANDOM() LIMIT ' + str(limit) + ";"
    print query
    return query      

if __name__ == '__main__':
    app.run()
