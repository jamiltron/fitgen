import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from random import randint

# configuration
DATABASE = './fitgen.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'password'

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
        try:
            limit = request.form['num_exercises']
            query = build_query(muscle_dict[request.form['muscles']],
                        type_include, equip_exclude, limit)
            exc = query_db(query, one=False)
            entries = []
            for x in exc:
                entries.append(x['workout_name'])
        except:
            entries=["error_raised"]
    return render_template('show_exercises.html', entries=entries)
    
def build_query(muscles=[], types=[], equip=[], limit=1):
    query = "SELECT workout_name FROM exercises WHERE ("
    
    for i in range(0, len(muscles)):       
        if i != 0:
            query += " OR "
        query += "muscles='" + muscles[i] + "'"
    query += ')'
    if len(types) > 0:
        query += " AND ("
        for i in range(0, len(types)):           
            if i != 0:
                query += " OR "
            query += "workout_type='" + types[i] + "'"
        query += ')'
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
