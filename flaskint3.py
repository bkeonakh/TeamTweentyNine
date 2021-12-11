# imports
import os                 # os is used to get environment variables IP & PORT
from flask import Flask   # Flask is the web app that we will customize
from flask import render_template
from flask import request
from flask import redirect, url_for
from flask import session
from database import db
from models import Post as Post
from models import User as User
from forms import RegisterForm
import bcrypt
from forms import LoginForm
from models import Comment as Comment
from forms import RegisterForm, LoginForm, CommentForm
from base64 import b64encode
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './static/upload_images'
ALLOWED_EXTENSIONS = {'png','jpg','jpeg'}
app = Flask(__name__)     # create an app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_note_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
app.config['SECRET_KEY'] = 'SE3155'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#  Bind SQLAlchemy db object to this Flask app
db.init_app(app)
# Setup models
with app.app_context():
    db.create_all()   # run under the app context

@app.route('/')
@app.route('/index')
def index():
    if session.get('user'):
        all_posts = db.session.query(Post).all()
        all_users = db.session.query(User).filter_by(id = Post.user_id).all()
        return render_template("index.html", posts=all_posts, user=session['user'], users=all_users)
    return render_template("index.html")

#All Posts
@app.route('/posts')
def get_posts():
    if session.get('user'):
        my_posts = db.session.query(Post).filter_by(user_id=session['user_id']).all()
        return render_template('posts.html', posts=my_posts, user=session['user'])
    else:
        return redirect(url_for('login'))



#Single Post
@app.route('/posts/<post_id>')
def get_post(post_id):
    if session.get('user'):
        my_post = db.session.query(Post).filter_by(id=post_id
                                                   #, user_id=session['user_id']
                                                   ).one()
        form = CommentForm()

        return render_template('post.html', post=my_post,user=session['user'], form=form)
    else:
        return redirect(url_for('login'))

#Edit Function
@app.route('/posts/edit/<post_id>', methods=['GET','POST'])
def update_post(post_id):
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            text = request.form['postText']
            post = db.session.query(Post).filter_by(id=post_id).one()
            post.title = title
            post.text = text
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('get_posts'))
        else:
            my_post = db.session.query(Post).filter_by(id=post_id).one()
            return render_template('new.html', post=my_post, user=session['user'])
    else:
        return redirect(url_for('login'))

#Delete Function
@app.route('/posts/delete/<post_id>', methods=['POST'])
def delete_post(post_id):
    if session.get('user'):
        my_post = db.session.query(Post).filter_by(id=post_id).one()
        db.session.delete(my_post)
        db.session.commit()
        return redirect(url_for('get_posts'))
    else:
        return redirect(url_for('login'))



#New Post
@app.route('/posts/new', methods=['GET', 'POST'])
def new_post():
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            text = request.form['postText']
            

            from datetime import date
            today = date.today()
            today = today.strftime("%m-%d-%Y")
            new_record = Post(title, text, today, session['user_id'])
            db.session.add(new_record)
            db.session.commit()
            return redirect(url_for('get_posts'))
        else:
            from datetime import date
            today = date.today()
            today = today.strftime("%m-%d-%Y")
            return render_template('new.html', user=session['user'], today=today)
    else:
        return redirect(url_for('login'))

#Register
@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()

    if request.method == 'POST' and form.validate_on_submit():
        # salt and hash password
        h_password = bcrypt.hashpw(
            request.form['password'].encode('utf-8'), bcrypt.gensalt())
        # get entered user data
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        # create user model
        new_user = User(first_name, last_name, request.form['email'], h_password)
        # add user to database and commit
        db.session.add(new_user)
        db.session.commit()
        # save the user's name to the session
        session['user'] = first_name
        session['user_id'] = new_user.id  # access id value from user model of this newly added user
        # show user dashboard view
        return redirect(url_for('get_posts'))
    return render_template('register.html', form=form)

#Login
@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    # validate_on_submit only validates using POST
    if login_form.validate_on_submit():
        # we know user exists. We can use one()
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        # user exists check password entered matches stored password
        if bcrypt.checkpw(request.form['password'].encode('utf-8'), the_user.password):
            # password match add user info to session
            session['user'] = the_user.first_name
            session['user_id'] = the_user.id
            # render view
            return redirect(url_for('get_posts'))

        # password check failed
        # set error message to alert user
        login_form.password.errors = ["Incorrect username or password."]
        return render_template("login.html", form=login_form)
    else:
        # form did not validate or GET request
        return render_template("login.html", form=login_form)

    # something went wrong - display register view
    return render_template('register.html', form=form)

#Logout
@app.route('/logout')
def logout():
    # check if a user is saved in session
    if session.get('user'):
        session.clear()

    return redirect(url_for('index'))

#Comments
@app.route('/posts/<post_id>/comment', methods=['POST'])
def new_comment(post_id):
    if session.get('user'):
        comment_form = CommentForm()
        # validate_on_submit only validates using POST
        if comment_form.validate_on_submit():
            # get comment data
            comment_text = request.form['comment']
            new_record = Comment(comment_text, int(post_id), session['user_id'])
            db.session.add(new_record)
            db.session.commit()

        return redirect(url_for('get_post', post_id=post_id))

    else:
        return redirect(url_for('login'))


@app.route('/search', methods=['GET', 'POST'])
def search_post():
    if request.method == 'POST':
        search_value = request.form['searchbar']
        search = "%{0}%".format(search_value)
        #my_post = db.session.query(Post).filter_by(title=search_value).one()
        my_posts = db.session.query(Post).filter(Post.title.contains(search_value)).all()
        #return get_post(my_post.id)
        return render_template('posts.html', posts=my_posts,user=session['user'])

@app.route('/latest', methods=['GET', 'POST'])
def latest():
    if request.method == 'GET':
        my_posts = db.session.query(Post).order_by(Post.id.desc()).all()
        return render_template('index.html', posts=my_posts,user=session['user'])

app.run(host=os.getenv('IP', '127.0.0.1'),port=int(os.getenv('PORT', 5000)),debug=True)

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000

# Note that we are running with "debug=True", so if you make changes and save it
# the server will automatically update. This is great for development but is a
# security risk for production.
