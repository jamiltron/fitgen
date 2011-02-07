import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
from contextlib import closing
from random import randint

# configuration
DATABASE = './fitgen.db'
DEBUT = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'password'

# create our little application
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
        try:
            if request.form['muscles'] == 'upper':
                exc = query_db('select workout_name from exercises where muscles = ? or muscles = ?', ['back', 'arms'], one=True)
            elif request.form['muscles'] == 'lower':
                exc = query_db('select workout_name from exercises where id = ?', [1], one=True)
            entries=[exc['workout_name']]
        except:
            entries=["error raised"]
    return render_template('show_exercises.html', entries=entries)
    

if __name__ == '__main__':
    app.run()

