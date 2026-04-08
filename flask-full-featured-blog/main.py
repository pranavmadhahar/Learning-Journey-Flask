from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase
from flask_mail import Mail
from datetime import datetime
from werkzeug.utils import secure_filename
import json, os, math
local_time = datetime.now()
# print(local_time)

db = SQLAlchemy()

app = Flask(__name__)

#For setting up session
app.secret_key = 'super-secret-key'

local_server = True

#For accessing the params in config.json 
with open('config.json', 'r') as c:
     params = json.load(c)['params']

#For configuring the file uploads
app.config['UPLOAD_FOLDER'] = params['upload_location']

#For setting flask mail
app.config.update(
     MAIL_SERVER = 'smtp.gmail.com',
     MAIL_PORT = '465',
     MAIL_USE_SSL = True,
     MAIL_USERNAME = params['gmail-user'],
     MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)

# DBS
# configure the SQLite database, relative to the app instance folder
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
# initialize the app with the extension
db.init_app(app)

# DBS
# The class will define the tables of the dbs
# Default value of nullable is true 

class Contacts(db.Model):

    sno = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, default=local_time)

class Posts(db.Model):

    sno = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(12), nullable=True)
    date = db.Column(db.DateTime, default=local_time)
    
# FLASK 

#This below code will make available params to all the templates globally & no need to pass params=params in templates.
@app.context_processor
def inject_params():
    return dict(params=params)

# #Defined posts and passed it to index.html, now posts variable can be used in it.
# @app.route("/")
# def home():
#     posts = Posts.query.all()
#     last = math.ceil(len(posts)/int(params['no_of_posts']))
#     #Below line retrieves the current page no from the query parameters in the URL. 
#     #For example, if the URL is /?page=2, page will be 2.
#     page = request.args.get('page')

#     if (not str(page).isnumeric()):
#         page = 1
    
#     page = int(page)

#     posts = posts[(page - 1)*int(params['no_of_posts']) : (page - 1)*int(params['no_of_posts']) + int(params['no_of_posts'])]

#     #Pagination logic
#     #First
#     if (page == 1):
#         prev = '#'
#         next = "/?page=" + str(page + 1)
#     #Last
#     elif(page == last):
#         prev = "/?page=" + str(page - 1)
#         next = '#'
#     #Middle
#     else:
#         prev = "/?page=" + str(page - 1)
#         next = "/?page=" + str(page + 1)
    
#     return render_template("index.html", posts=posts, prev=prev, next=next)


@app.route("/")
def home():
    # Fetch all posts
    all_posts = Posts.query.all()
    
    # Define the number of posts per page
    no_of_posts = int(params['no_of_posts'])
    
    # Calculate total pages
    total_posts = len(all_posts)
    last_page = math.ceil(total_posts / no_of_posts)
    
    # Get the current page, default to 1
    page = request.args.get('page', 1, type=int)
    page = max(1, min(page, last_page))  # Ensure page is within valid range
    
    # Calculate start and end indices for slicing
    start = (page - 1) * no_of_posts
    end = start + no_of_posts
    
    # Slice posts for the current page
    posts = all_posts[start:end]
    
    # Determine previous and next page links
    next = "/?page=" + str(page + 1) if page < last_page else None
    prev = "/?page=" + str(page - 1) if page > 1 else None


    
    return render_template("index.html", posts=posts, prev=prev, next=next)





@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    posts = Posts.query.all()

    if ('user' in session and session['user'] == params['admin_user']):
        return render_template("dashboard.html", posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            session['user'] = username
            return render_template("dashboard.html", posts=posts)
        else:
            # Optionally, you can add a message for incorrect login
            error_message = "Invalid username or password."
            return render_template("login.html", error=error_message)
    
    return render_template("login.html")



@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        print("Session contents:", session)

        if request.method == 'POST':
            f = request.files.get('file1')
            f.save(os.path.join( app.config['UPLOAD_FOLDER'], secure_filename(f.filename) )) #secure_filename fn is used for ensuring safety
            return "Uploaded Successfully"
        else:
            return "No file selected for upload", 400  # Handle case where no file is uploaded
    
    else:
        return "Unauthorized access, Please login for file upload", 403


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    # Check user is logged in
    if 'user' in session and session['user'] == params['admin_user']:
        print("Session contents:", session)

        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')

            print("Form data received:", box_title, tline, slug, content, img_file)

            try:
                # If it's a new post
                if sno == '0':
                    post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file)
                    db.session.add(post)
                    db.session.commit()
                    print("New post created with sno:", post.sno)
                    return redirect('/edit/' + str(post.sno))  # Redirect to the new post's sno
                else:
                    post = Posts.query.filter_by(sno=sno).first()
                    if post:
                        post.title = box_title
                        post.slug = slug
                        post.content = content
                        post.tagline = tline
                        post.img_file = img_file
                        db.session.commit()
                        print("Post updated with sno:", sno)
                    else:
                        print("Post not found for sno:", sno)
                    return redirect('/edit/' + sno)

            except Exception as e:
                print("Error occurred:", e)
                db.session.rollback()  # Rollback in case of error
                return "An error occurred while saving the post."
        else:
            post = Posts.query.filter_by(sno=sno).first()
            return render_template("edit.html", post=post, sno=sno)
    else:
        return "Unauthorized access", 403

@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        # .first() is used because post will return a list and we want its first variable
        post = Posts.query.filter_by(sno=sno).first() 
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')



@app.route("/contact", methods=["GET", "POST"])
def contact():
        if request.method == "POST":
            # 1. Retrieve data from the form submitted by user
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            message = request.form.get('message')
            # 2. Create object as per Class defined earlier
            entry = Contacts(
                 name = name,
                 email = email,
                 phone_num = phone,
                 msg = message,
            )
            # 3. Submit the form to the dbs 
            db.session.add(entry)
            db.session.commit()
            # 4. Send email using flask-Mail
            mail.send_message('New Message from DeCode Base - ' + name, 
                              sender=email, 
                              recipients=[params['gmail-user']],
                              body=message + '\n' + phone
                              )
        return render_template("contact.html")

# @app.route("/post",)
# def post():
#      return render_template("post.html")

# Fetch post from the database & post is passed into the html template. 
@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
     post = Posts.query.filter_by(slug=post_slug).first_or_404()

     return render_template("post.html", post=post)
     


# app.run()
#This will automatically update  changes without reloading app.
if __name__ == '__main__':
    app.run(debug=True)


