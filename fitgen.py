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
SALT = 's3cret_s@lt' 
SALT2 = 'm0_sec23T'
equip_list = ['barbell', 'dumbell', 'kettlebell', 'bench',
              'rack', 'pullup', 'box', 'jumprope', 'bike',
              'rower', 'elliptical', 'climber', 'pool', 'exercise_ball', 
              'medicine_ball', 'leg_press', 'leg_extension', 
              'glute_ham_chair', 'smith_machine']
type_list = ['weights', 'bodyweight', 'cardio']
muscle_dict = {'upper': ['back', 'arms', 'chest'],
               'lower': ['legs'],
               'full': ['back', 'arms', 'chest', 'legs', 'core']}
equip_dict = {'barbell': 'Barbell + Weights', 'bench': 'Bench',
              'bike': 'Bike', 'box': 'Box', 'dumbell': 'Dumbells', 
              'elliptical': 'Elliptical Machine', 
              'exercise_ball': 'Exercise Ball', 
              'glute_ham_chair': 'Glute Ham Chair',
              'jumprope': 'Jumprope', 'kettlebell': 'Kettlebell',
              'leg_extension': 'Leg Extension Machine', 
              'medicine_ball': 'Medicine Ball', 
              'leg_press': 'Leg Press/Hip Slide', 'rack': 'Power Rack', 
              'pullup': 'Pullup Bar', 'rower': 'Rowing Machine',
              'smith_machine': 'Smith Machine', 
              'climber': 'Stairs/Stair Machine', 'pool': 'Swimming Pool'}

# build our application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FITGEN_SETTINGS', silent=True)

def connect_db():
    """Returns a connection to the database specified in the 
    global variables DATABASE"""
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    """Initializes the database"""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    """Returns the supplied query to the connected database. args allows
    supplying arguments used by g.db's execute function, and one allows
    a limitation of one returned result"""
    curr = g.db.execute(query, args)
    rv = [dict((curr.description[idx][0], value)
               for idx, value in enumerate(row)) for row in curr.fetchall()]
    return (rv[0] if rv else None) if one else rv

def build_query(muscles=[], types=[], equip=[], force=None, limit=1):
    """Takes a list of muscles, workout types, equipment to exclude
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
    if force:
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

@app.before_request
def before_request():
    g.db = connect_db()

@app.after_request
def after_request(response):
    g.db.close()
    return response

@app.route('/cpanel', methods=['GET', 'POST'])
def cpanel():
    """Registered user's control panel, allows the updating of user
    information such as email, password, and owned equipment."""
    global equip_list
    query = ""
    owned_list = []
    error = None

    if request.method == 'POST':
        insert_query = ""
        changed = False
        for x in equip_list:
            # iterate through the equip list, building a list of 
            # equipment values based on if the request form has it
            # checked or not
            if x in request.form:
                insert_query += x + "=1,"
                changed = True
            else:
                insert_query += x + "=0,"
                changed = True
        if changed:
            # add the beginning to the query and chop off the last comma
            insert_query = "UPDATE USERS set " + \
                insert_query[:len(insert_query)-1]
            insert_query += " WHERE login_name='"
            insert_query += str(session['username']) + "';"
            print "INSERT QUERY: " + insert_query
            try:
                g.db.execute(insert_query)
                g.db.commit()
                flash("Equipment updated")
                return redirect(url_for('index'))
            except:
                error = "error inserting into database"

    try:
        if session['logged_in']:
            for x in equip_list:
                query += x + ','
            query = "SELECT " + query[:len(query) - 1] + \
                " FROM users WHERE login_name='" + \
                str(session['username']) + "';"            
            exc = query_db(query)
            for x in exc:
                owned = x
            return render_template('cpanel.html', owned=owned, \
                                       equip_names=equip_dict, error = error)
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
        if len(request.form['password1']) < 8:
            error = "Passwords must be at least 8 characters"
        elif request.form['password1'].isalpha() or \
                request.form['password1'].isnumeric():
            error = "Passwords must have a mix of alpha and numeric characters"
        elif request.form['password1'] != request.form['password2']:
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
            # get the current max user id number
            exc = query_db("SELECT count(*) FROM users;")
            count = exc[0]['count(*)']
            # generate their hash password using their password, salt, and id
            user_hash = hashlib.sha1()
            user_hash.update(str(count + 1) + request.form['password1'] + SALT)
            user_pass = user_hash.hexdigest()
            secret_hash = hashlib.sha1()
            secret_hash.update(str(count+1) + request.form['secret_answer'] + \
                                   SALT2)
            secret_pass = secret_hash.hexdigest()
            try:
                g.db.execute("INSERT INTO users (login_name,email,password, " + 
                             "user_role, secret_question, secret_answer) " + 
                             "values (?, ?, ?, ?, ?, ?)", 
                             [request.form['username'], request.form['email1'], 
                             user_pass, 'user', request.form['secret_question'], 
                              secret_pass])
                g.db.commit()
                # delete the password asap
                del(user_hash)
                del(user_pass)
                del(secret_hash)
                del(secret_pass)
                flash("New user " + request.form['username'] + " registered.")
            except:
                error = "error inserting into database"
    return render_template('register.html', error=error)

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    """asks the user for their username, passes the secret question"""
    if request.method == 'POST':
        # I can probably just query once, I should change this
        query = "SELECT id, secret_question, secret_answer from users "
        query += "WHERE login_name='" + request.form['username'] + "';"
        exc = query_db(query)
        
        if not exc:
            return render_template('forgot.html', error='Invalid username')
        answer = False

        if request.form['answered'] == "True":
            error = None
            if len(request.form['password1']) < 8:
                error = "Passwords must be at least 8 characters"
            elif request.form['password1'].isalpha() or \
                    request.form['password1'].isnumeric():
                error = "Passwords must have a mix of alpha and numeric characters"
            elif request.form['password1'] != request.form['password2']:
                error = "Passwords do not match"       
                    
            if error == None:
                user_hash = hashlib.sha1()
                user_hash.update(str(exc[0]['id']) + request.form['password1'] + \
                                     SALT)
                user_pass = user_hash.hexdigest()

                try:
                    query = "UPDATE users SET password='" + user_pass + \
                        "' where login_name='" + request.form['username'] + "';"
                    print query
                    g.db.execute(query)
                    g.db.commit()
                    # delete the password asap
                    del(user_hash)
                    del(user_pass)
                    del(exc)
                    flash("Password changed")
                    return redirect(url_for('index'))
                except:
                    error = "error inserting into database"                   
                    return render_template('forgot.html')
            else:
                return render_template('forgot.html', error=error)
        else:
            try:
                temp_hash = hashlib.sha1()
                temp_hash.update(str(exc[0]['id']) + request.form['answer'] + SALT2)
                temp_pass = temp_hash.hexdigest()
                if temp_pass == exc[0]['secret_answer']:
                    answer = True
                    del(temp_hash)
                    del(temp_pass)
                    del(exc)
                    return render_template('forgot.html', \
                                               username=request.form['username'], \
                                               answered=answer)
                else:
                    return render_template('forgot.html', error='Invalid answer')
            except:
                return render_template('forgot.html', \
                                           username=request.form['username'], \
                                           question=exc[0]['secret_question'], \
                                           answered=False)
    else:  
        return render_template('forgot.html')

@app.route('/workout', methods=['POST'])
def random_workout():    
    """the logic behind the random workout"""
    if request.method == 'POST':
        global equip_list, muscle_dict, type_list
        equip_exclude = []
        type_include = []
        
        # build the list of equipment to exclude
        try:
            # if the user is logged in, get their saved equipment list
            if session['logged_in']:
                query = "SELECT "
                for x in equip_list:
                    query += x + ","
                query = query[:len(query)-1] + " FROM users WHERE login_name='"
                query += str(session['username']) + "';"
                exc = query_db(query)
                for x in exc:
                    for key in x:
                        if x[key] != 1:
                            equip_exclude.append(key)

        except:
            # if the user is not logged in, base it on checkboxes in index.html
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
                force_str = request.form['force']
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
    
if __name__ == '__main__':
    app.run()
