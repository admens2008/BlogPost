from flask import Blueprint, render_template
from models import *
from flask import request, url_for, redirect, flash
from App import db, app
from sqlalchemy import or_
from .forms import PostForm
from werkzeug.utils import secure_filename
from flask_login import login_required, login_user, current_user, logout_user

import os

posts = Blueprint('posts', __name__, template_folder="templates")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@posts.route('/login')
def login():
    return render_template('posts/login.html')

@posts.route('/login', methods=['POST'])
def login_post():
    i = 0
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    pwd = hashlib.md5(password.encode()).hexdigest()
    
    user = User.query.filter_by(email=email).first()
    hashed_password_in_db = user.password if user else None
    if not hashed_password_in_db:
        flash('Invalid email or password')
        return redirect(url_for('posts.login'))
    elif pwd != hashed_password_in_db:
        flash('Invalid email or password')
        return redirect(url_for('posts.login'))
    else:
        login_user(user, remember=True)
        return redirect(url_for('index'))

@posts.route('/signup')
def signup():
    return render_template('posts/signup.html')

@posts.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user:
        flash('User already exist!!!')
        return redirect(url_for('posts.signup'))
    new_user = User(email=email, first_name=first_name, last_name=last_name, password=password)
    db.session.add(new_user)
    new_role = Role.query.filter_by(name='user').first()
    if new_role:
        new_user.roles.append(new_role)
    db.session.commit()
    return redirect(url_for('posts.login'))
    
@posts.route('/<userid>')
def dashboard(userid):
    return redirect(url_for("posts.authenticated", userid=userid))

@posts.route('/profile/<userid>')
@login_required
def profile(userid):
    return render_template("posts/profile.html", userid=userid)

@posts.route('/profile/', methods=['POST'])
@login_required
def profile_post():
    filepath = None
    image = None
    taglist = []
    t_ = None
    p_ = None
    if request.method == 'POST':
        user = User.query.filter_by(userid=current_user.userid).first()
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        About = request.form.get('instagram')
        website = request.form.get('website')
        gitup = request.form.get('gitup')
        facebook = request.form.get('facebook')
        linkedin = request.form.get('linkedin')
        youtube = request.form.get('youtube')
        twitter = request.form.get('twitter')
        try:
            image = request.files['filepath']
        except:
            image = None
        if image != None  and allowed_file(image.filename):
            if user.filepath:
                if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'] + '/static/', user.filepath )):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'] + '/static/', user.filepath))
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/static/', 'userblog_' + filename))
            filepath = 'userblog_' + filename
        user.filepath = user.filepath
        if filepath:
            user.filepath = filepath
        user.first_name = first_name
        user.last_name = last_name
        user.instagram = About
        user.website = website
        user.gitup = gitup
        user.facebook = facebook
        user.linkedin = linkedin
        user.youtube = youtube
        user.twitter = twitter
        db.session.commit()
        flash('Record updated successfully')
        return redirect(url_for("posts.profile", userid=current_user.userid))
    
@posts.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))




@posts.route('/<postid>/delete')
def post_delete(postid):
    post = Post.query.filter_by(postid=postid).first()
    if post:
        db.session.delete(post)
        db.session.commit()
    return redirect(url_for('posts.post_list', userid=current_user.userid))

@posts.route('/reset', methods=['GET'])
def reset():
    return render_template("posts/reset.html")

@posts.route('/reset', methods=['POST'])
def reset_post():
    email = request.form.get('email')
    password = request.form.get('password')
    confirmpassword = request.form.get('confirmpassword')
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User doesnt exist!!")
        return redirect(url_for('posts.reset'))
    if password != confirmpassword:
        flash("Password doesnt match!!")
        return redirect(url_for('posts.reset'))
    if user:
        user.password = password
        db.session.commit()
        logout_user()
    return redirect(url_for('posts.login'))





@posts.route('/<userid>')
def authenticated(userid):
    user = User.query.filter_by(userid=userid).first()
    login_user(user, remember=True)
    return redirect(url_for('posts.post_list'))

# routes to /blog
@posts.route('/create', methods=['POST', 'GET'])
@login_required
def post_create():
    user = None
    if current_user.is_authenticated:
        user = User.query.filter_by(email=current_user.email).first()
    form = PostForm()
    filepath = None
    taglist = []
    t_ = None
    p_ = None
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        image = request.files['filepath']
        try:
            taglist = request.form.getlist("mycheckbox")
        except:
            taglist = []
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/static/', filename))
            filepath = filename
        post = Post(title=title, body=body, filepath=filepath, user_id=user.userid)
        db.session.add(post)
        print(taglist)
        if len(taglist) > 0:
            for tag in taglist:
                t_ = Tag.query.filter_by(title=tag).first()
                post.tags.append(t_)
                user.posts.append(post)
        db.session.commit()
                
        return redirect(url_for('posts.post_list', userid=current_user.userid))
    tags = Tag.query.all()
    return render_template('posts/post_create.html', form=form, tags=tags)


@posts.route('/<userid>/')
def post_list(userid):
    user = None
    if current_user.is_authenticated:
        user = User.query.filter_by(email=current_user.email).first()
    user_ = User.query.filter_by(userid=userid).first()
    i = 0
    q = request.args.get('q')
    if q:
        postlist = Post.query.filter(or_(Post.title.contains(q), Post.body.contains(q)),
                                     Post.user_id == userid)
# postlist = Post.query.filter(Post.title.contains(q) |
                                  #   Post.body.contains(q)) """
    else:
        postlist = Post.query.filter_by(user_id=userid).order_by(Post.created.desc())
    
    page = request.args.get("page")
    #localhost:5000/blog?page=7478
    if page and page.isdigit():
        page = int(page)
    else:
        page = 1
    try:
        pages = postlist.paginate(page=page, per_page=3)
    except:
        if (postlist.count() % 3 != 0):
            count =  int((postlist.count() / 3)) + 1
        else:
            count = (postlist.count() / 3)

        pages = postlist.paginate(page=count, per_page=3)

    
    return render_template('posts/post_list.html', postlist=postlist, i=i, pages=pages, user_=user_)

#route to specific post details
@posts.route('/<slug>/<userid>', methods=['GET'])
def post_details(slug, userid):
    postdetail = Post.query.filter(Post.slug==slug, Post.user_id==userid).first()
    user_ = User.query.filter_by(userid=userid).first()
    return render_template('posts/post_detail.html', postdetail=postdetail, user_=user_)

#route to specific post details
@posts.route('tags/<slug>/<userid>')
def tag_details(slug, userid):
    i = 0
    tags = Tag.query.filter(Tag.slug==slug).first()
    page = request.args.get("page")
    q = request.args.get('q')
    if q:
        postlist = Post.query.join(Post.tags).filter_by(slug=slug).filter(
            (Post.title.contains(q)) | (Post.body.contains(q)), Post.user_id == userid
        )
    else:
        postlist = Post.query.join(Post.tags).filter_by(slug=slug).filter(Post.user_id == userid)
    
    if page and page.isdigit():
        page = int(page)
    else:
        page = 1
    try:
        pages = postlist.paginate(page=page, per_page=3)
    except:
        if (postlist.count() % 3 != 0):
            count =  int((postlist.count() / 3)) + 1
        else:
            count = (postlist.count() / 3)

        pages = postlist.paginate(page=count, per_page=3)
    
    user_ = User.query.filter_by(userid=userid).first()
    return render_template('posts/tag_detail.html', tags=tags, pages=pages, i=i, user_=user_)

@posts.route('/<slug>/<userid>/edit', methods=["POST", "GET"])
@login_required
def post_update(slug, userid):
    post = Post.query.filter(Post.slug==slug, Post.user_id==userid).first()
    taglist = []
    if request.method == 'POST':
        form = PostForm(formdata=request.form, obj=post)
        filepath = None
        image = None
        form.populate_obj(post)
        title = request.form.get('title')
        body = request.form.get('body')
        try:
            taglist = request.form.getlist("mycheckbox")
        except:
            taglist = []
        try:
            image = request.files['filepath']
        except:
            image = None
        if image != None  and allowed_file(image.filename):
            if post.filepath:
                if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'] + '/static/', post.filepath)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'] + '/static/', post.filepath))
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'] + '/static/', filename))
            filepath = filename
        post.title = title
        post.body = body
        post.filepath = post.filepath
        if filepath:
            post.filepath = filepath
        print(taglist)
        for tag in post.tags:
            post.tags.remove(tag)
        if len(taglist) > 0:
            for tag in taglist:
                t_ = Tag.query.filter_by(title=tag).first()
                post.tags.append(t_)
        db.session.commit()
        return redirect(url_for("posts.post_details", slug=post.slug, userid=current_user.userid))
    form = PostForm(obj=post)
    form.filepath.data = post.filepath
    tags = Tag.query.all()
    return render_template("posts/edit.html", post=post, form=form, tags=tags)


def save_image(image):
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename  # Return the filename for storing in your database
    return None
