import sqlite3,json, urllib2
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash


api_str = 'https://www.googleapis.com/books/v1/volumes?q=isbn:'

DATABASE = 'db.db'
DEBUG = True 
SECRET_KEY = "development key"
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

def init_db():  #initiates the db from sql file
    with closing(connect_db()) as db:
        with app.open_resource('book.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

connect_db()
init_db()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
        
@app.route('/') #index redirects to login page
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST']) #login page
def login():
    error = None
    if request.method == 'POST':
        cur1 = g.db.execute('select loginname,loginpw from Users where loginname=?',
                            [request.form['username']])
        users = cur1.fetchall()
        if not users:
            error="Invalid username"
        elif request.form['password'] != users[0][1]:
            error="Invalid password"
        else:
            session['username'] = request.form['username']
            session['logged_in'] = True
            flash('You are logged in as {}'.format(session['username']))
            return redirect(url_for('current_books'))
    return render_template('login.html', error=error)

@app.route('/logout') #logout redirects to index which redirects to login
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST']) #register multiple users
def register():
    if request.method == 'POST':
        cur1 = g.db.execute('select loginname from Users')
        dblist = [row[0] for row in cur1.fetchall()]
        if request.form['username'] in dblist:
            flash('Username already exists')
            return redirect(url_for('login'))
        g.db.execute('insert into Users (loginname,loginpw) values (?,?)',
                     [request.form['username'],
                      request.form['password']])
        g.db.commit()
        flash('New user was created, log in!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard') #dashboards which show current books
def current_books():
    cur1 = g.db.execute('select ISBN, Title, Author, Pages, '\
                        'avgReview,Thumb,userID from Books b '\
                        'inner join Users u on b.userID = u.ID '\
                        'where u.loginname=?',[session['username'].decode()])
    books = [dict(isbn=row[0],
                  title=row[1],
                  author=row[2],
                  pages=row[3],
                  rev=row[4],
                  thumb=row[5]) for row in cur1.fetchall()]
    return render_template('current_books.html', books=books)

@app.route('/book/add', methods=['GET','POST']) #additional books
def add():
    if request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
        response = urllib2.urlopen(api_str + request.form['isbn'])
        data = json.loads(response.read())
        successful = False
        try:
            g.db.execute('insert into Books (ISBN,Title,Author,Pages,'\
                         'avgReview,Thumb,userID) '\
                         'values (?,?,?,?,?,?,(select ID from Users where loginname=?))',
                         [request.form['isbn'],
                         data['items'][0]['volumeInfo']['title'].decode(),
                         data['items'][0]['volumeInfo']['authors'][0].decode(),
                         data['items'][0]['volumeInfo']['pageCount'],
                         data['items'][0]['volumeInfo']['averageRating'],
                         data['items'][0]['voelumeInfo']\
                         ['imageLinks']['smallThumbnail'],
                         session['username']])
            g.db.commit()
            successful = True
        except KeyError:
            flash('You\'ve entered an incorrect ISBN. Try again.')
            return redirect(url_for('add'))
        if successful:    
            flash('{} by {} was successfulfully added to your library.'.format(
                        data['items'][0]['volumeInfo']['title'].decode(),
                        data['items'][0]['volumeInfo']['authors'][0].decode()))
        return redirect(url_for('current_books'))
    return render_template('add.html')

@app.route('/book/delete/<isbn>', methods=['GET','POST']) #deletion of books
def delete(isbn):
    if request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
    g.db.execute.delete(isbn)
    g.db.commit()
    return redirect(url_for('current_books'))
    
if __name__ == '__main__':
    app.run()