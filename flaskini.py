
# imports
import os                 # os is used to get environment variables IP & PORT
from flask import Flask   # Flask is the web app that we will customize
from flask import request
from flask import render_template
from database import db
from Models import Question as Question
from Models import User as User
from flask import redirect, url_for

app = Flask(__name__)     # create an app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///QandA_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
#  Bind SQLAlchemy db object to this Flask app
db.init_app(app)
# Setup models
with app.app_context():
    db.create_all()   # run under the app context
# @app.route is a decorator. It gives the function "index" special powers.
# In this case it makes it so anyone going to "your-url/" makes this function
# get called. What it returns is what is shown as the web page
#@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


#@app.route('/')
@app.route('/posts/')
def get_questions():
    a_user = db.session.query(User).filter_by(email='mogli@uncc.edu').one()
    my_posts = db.session.query(Question).all()
    return render_template('viewQuestions.html',posts=my_posts,user=a_user)

@app.route('/posts/<question_id>')
def get_question(note_id):
    a_user = db.session.query(User).filter_by(email='mogli@uncc.edu').one()
    my_question = db.session.query(Question).filter_by(id=note_id).one()

    return render_template('question.html',post=my_question,user=a_user)

@app.route('/posts/new', methods=['GET','POST'])
def new_question():
    #a_user = {'name':'Dave','email':'dramnari@uncc.edu'}

    if request.method == 'POST':
        title = request.form['title']
        text = request.form['noteText']
        from datetime import date
        today = date.today()
        today = today.strftime("%m-%d-%y")
        new_record = Question(title,text,today)
        db.session.add(new_record)
        db.session.commit()
        return redirect(url_for('get_questions'))
    else:
        a_user = db.session.query(User).filter_by(email='mogli@uncc.edu').one()
        return render_template('createQuestion.html',user=a_user)


@app.route('/posts/edit/<question_id>', methods=['GET','POST'])
def update_question(question_id):
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['noteText']
        note = db.session.query(Question).filter_by(id=question_id).one()
        note.title = title
        note.text = text
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('get_questions'))
    else:
        a_user = db.session.query(User).filter_by(email='mogli@uncc.edu').one()
        my_question = db.session.query(Question).filter_by(id=question_id).one()
        return render_template('question.html',question=my_question,user=a_user)

@app.route('/posts/delete/<question_id>', methods=['POST'])
def delete_note(question_id):
    my_question = db.session.query(Question).filter_by(id=question_id).one()
    db.session.delete(my_question)
    db.session.commit()
    return redirect(url_for('get_questions'))

app.run(host=os.getenv('IP', '127.0.0.1'),port=int(os.getenv('PORT', 5000)),debug=True)

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000

# Note that we are running with "debug=True", so if you make changes and save it
# the server will automatically update. This is great for development but is a
# security risk for production.


