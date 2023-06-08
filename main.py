import base64
from datetime import datetime
from functools import wraps
from flask import abort
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from sqlalchemy import exc, LargeBinary
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, URL, Email, Length, EqualTo, Optional
from flask_ckeditor import CKEditor, CKEditorField


## Delete this code:
# import requests
# posts = requests.get("https://api.npoint.io/43644ec4f0013682fc0d").json()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['CKEDITOR_PKG_TYPE'] = 'full-all'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CONFIGURE TABLE
class BlogPost(db.Model):
    __tablename__ = 'blog_post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    #author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    author_link = relationship("User", back_populates="post")
    comments=relationship("Comments",back_populates="comment_for_blog")

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100),nullable=False)
    name = db.Column(db.String(1000),nullable=False)
    image_data = db.Column(LargeBinary,nullable=False)

    phn_no = db.Column(db.String(25), nullable=True)
    skype = db.Column(db.String(50), nullable=True)
    facebook = db.Column(db.String(200), nullable=True)
    twitter = db.Column(db.String(200), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    instagram = db.Column(db.String(200), nullable=True)

    post = relationship("BlogPost", back_populates="author_link")
    comments=relationship("Comments",back_populates="comment_author")

class Comments(db.Model):
    __tablename__ = 'comments'
    id=db.Column(db.Integer, primary_key=True)
    comment_text= db.Column(db.String(250))

    author_id=db.Column(db.Integer, db.ForeignKey("user.id"))
    comment_author= relationship("User",back_populates="comments")

    blog_id =db.Column(db.Integer,  db.ForeignKey("blog_post.id"))
    comment_for_blog=relationship("BlogPost",back_populates="comments")



with app.app_context():
    db.create_all()


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
def admin_only(pass_funtion):
    @wraps(pass_funtion)
    def wrapper(*args,**kwargs):
        if current_user.is_authenticated:
            if current_user :
                print("True")
            else:
                print("False")
            if current_user.id==1:
                return pass_funtion(*args,**kwargs)
            else:
                abort(403)
        else:
            return redirect(url_for('login', need_login="Need to Login First!"))
    return wrapper

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    # author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post" )

class Comment(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")

def disable_form_fields(form):
    for field in form:
        field.render_kw = {"disabled": "disabled"}


def sentMail(to_mail, cc_mail, msg):
    import smtplib
    from email.message import EmailMessage

    email = "your.ex.daddy8@gmail.com"
    password = "lpgfzommjqmtjlda"

    message = EmailMessage()
    message["Subject"] = "Mail from Website Contact Form"
    message["From"] = email
    message["To"] = to_mail
    message["Cc"] = cc_mail
    message.set_content(msg)

    try:
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=email, password=password)
            connection.send_message(message)
            return True
            print("-------MSG sent------------")
    except Exception as e:
        print(e)
        return False


# sentMail("mamunurrashid.s.bd@gmail.com","mamun.kfz@gmail.com","Happy codding")

@app.route('/')
@app.route('/index')
def get_all_posts():
    posts=db.session.query(BlogPost).all()


    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:index>",methods=["post","get"])
def show_post(index):
    requested_post = None
    cmnt=Comment()
    posts = db.session.query(BlogPost).all()
    for blog_post in posts:
        if blog_post.id == index:
            requested_post = blog_post
            try:
                if cmnt.validate_on_submit():
                    print("Validate Comment")
                    new_comment=Comments(
                        comment_text=cmnt.comment.data,
                        author_id=current_user.id,
                        blog_id=blog_post.id

                    )
                    db.session.add(new_comment)
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                error_message = e.args[0]
                print(error_message)
                if "AnonymousUserMixin' object has no attribute 'id'" in error_message:
                    return redirect(url_for('login', Unauthorized_error="You're need to Login or Register first."))
                else:
                    return f'<h1 style="color: red;">SERVER ERROR:  {error_message}</h1>'



    return render_template("post.html", post=requested_post,comment_form=cmnt)

# @app.route("/comment",methods=["post","get"])
# def comment_post():
#     id=request.args.get("post_id")
#
#     return redirect(url_for("show_post", index=id))



@app.route("/edit/<int:post_id>" , methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    try:
        post_to_update = BlogPost.query.get(post_id)
        update_form = CreatePostForm(
            title=post_to_update.title,
            subtitle=post_to_update.subtitle,
            img_url=post_to_update.img_url,
            body=post_to_update.body
        )
        if request.method == 'POST':
            post_to_update.title = request.form["title"]
            post_to_update.subtitle = request.form["subtitle"]
            post_to_update.img_url = request.form["img_url"]
            post_to_update.body = request.form["body"]
            post_to_update.date = datetime.now().strftime("%B %d, %Y")

            db.session.commit()
            return redirect(url_for("show_post", index=post_id))


    except Exception as e:
        # Handle any other exceptions
        print(e)
        Blank_form = CreatePostForm(
            title="****",
            subtitle="****",
            img_url="****",
            body="****"
        )
        disable_form_fields(Blank_form)
        error_message = "*No Data Found!"
        return render_template('make-post.html', error=error_message, post_form=Blank_form)


    return render_template("make-post.html", post_form=update_form, is_edit=True)



@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def create_post():
    new_post_form = CreatePostForm()
    if request.method == 'POST':
        try:
            new_post= BlogPost(
            title=request.form["title"],
            subtitle=request.form["subtitle"],
            img_url=request.form["img_url"],
            body=request.form["body"],
            date = datetime.now().strftime("%B %d, %Y"),
            author_id=current_user.id
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
        except exc.IntegrityError as e:
            db.session.rollback()
            error_message = "*Post with the same title already exists."
            return render_template('make-post.html', error=error_message,post_form=new_post_form)

    return render_template("make-post.html", post_form=new_post_form)

@app.route("/delete")
@admin_only
def delete():
    post_id=request.args.get("post_id")
    post_to_delete=BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))



class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        admin_mail="mamunurrashid.s.bd@gmail.com"
        # Process the form data
        name = form.name.data
        email = form.email.data
        phone = form.phone.data
        message = form.message.data

        user_msg=f"{message}\n\nSender Info:\nName: {name}\nCell: {phone}\nMail: {email}"

        mail_status=sentMail(to_mail=admin_mail,cc_mail=email,msg=user_msg)
        if mail_status:
            return render_template('contact.html', not_submited_yet=False,is_sent=True,mail_address=email)
        else:
            return render_template('contact.html', not_submited_yet=False,is_sent=False)



    return render_template('contact.html', form=form ,not_submited_yet=True)


@app.route("/about/")
def about():
    return render_template('about.html')

class ContactRegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(message='* Name is required.')])
    email = StringField('Email Address', validators=[DataRequired(message='* Email is required.'), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(message='* Password is required.'),
        Length(min=8, message='* Password must be at least 8 characters long.'),
        EqualTo('confirm_password', message='* Passwords must match.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='* Please confirm your password.')
    ])
    image = FileField('Profile Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'], '* Support "jpeg, jpg, png" format only ')])



@app.route("/register", methods=["GET", "POST"])
def register():
    logout_user()
    reg_form=ContactRegisterForm()
    error_img = None
    error_email = None
    if reg_form.validate_on_submit():
        try:
            #if reg_form.image.data:
                image=reg_form.image.data
                image_data=image.read()
                image.seek(0)
                New_user= User(

                    email = (reg_form.email.data).lower(),
                    name=reg_form.name.data,
                    password =generate_password_hash(reg_form.password.data, method='pbkdf2:sha256',salt_length=8),
                    image_data = image_data,
                    phn_no = "--",
                    skype = "--",
                    facebook = "--",
                    twitter = "--",
                    linkedin = "--",
                    instagram = "--"
                )
                db.session.add(New_user)
                db.session.commit()
                login_user(New_user)
                return redirect(url_for("get_all_posts"))
            # else:
            #     print("Add Image")
        except Exception as e:
            db.session.rollback()
            error_message = e.args[0]
            print(error_message)
            if "UNIQUE" in error_message.upper():
                error_email = "* Email address already exists."
                return render_template('register.html', error_email=error_email, error_img=error_img,
                                       form=reg_form)

            elif "user.image_data" in error_message or "'NoneType' object has no attribute 'read'" in error_message:
                error_img = "* Required Profile Picture."
                return render_template('register.html', error_email=error_email, error_img=error_img,
                                       form=reg_form)

            else:
                error_img=error_message
                return render_template('register.html', error_email=error_email, error_img=error_img,
                                       form=reg_form)

    return render_template('register.html', error_email=error_email,error_img=error_img,form=reg_form)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
class LoginForm(FlaskForm):

    email = StringField('Email Address', validators=[DataRequired(message='* Email is required.'), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(message='* Password is required.'),
        Length(min=8, message='* Password must be at least 8 characters long.')])

@app.route("/login",methods=["Post","get"])
def login():
    logout_user()
    Unauthorized_error = request.args.get("Unauthorized_error")
    if Unauthorized_error:
        flash(Unauthorized_error)

    need_login=request.args.get("need_login")
    if need_login:
        flash(need_login)

    login_form=LoginForm()
    if login_form.validate_on_submit():
        if request.method == "POST":
            email=(login_form.email.data).lower()
            print(email)
            password = login_form.password.data
            read_DB=db.session.query(User).filter_by(email=email).first()

            if read_DB is not None:
                if check_password_hash(read_DB.password,password):
                    login_user(read_DB)

                    return redirect(url_for("get_all_posts"))
                else:
                    error = "* Incorrect Password. Please try again."
                    print(error)
                    return render_template("login.html", error_pass=error, form=login_form)
            else:
                error = "* No account found. Try again or Sign Up."
                print(error)
                return render_template("login.html", error_email=error, form=login_form)


    return render_template("login.html",form=login_form)

@app.context_processor
def profile_data_injection():
    # Generate the data you want to send to all child templates
    if current_user.is_authenticated and current_user.image_data:

            #image_data = current_user.image_data
            profile_image_url = f"data:image/jpeg;base64,{base64.b64encode(current_user.image_data).decode('utf-8')}"
            data = {
                'status': True,
                "id":current_user.id,
                'profile_image_url': profile_image_url,
                'account_name': current_user.name,
                'email': current_user.email,
                'phn_no': current_user.phn_no,
                'skype': current_user.skype,
                'facebook': current_user.facebook,
                'twitter': current_user.twitter,
                'instagram': current_user.instagram,
                'linkedin': current_user.linkedin,
                # Add more data as needed
            }
            return data
    else:
        data = {
            'status': False
        }
        return data

@app.errorhandler(401)
def unauthorized(error):
    # Handle the unauthorized error here
    # For example, you can redirect the user to the login page with an error message
    return redirect(url_for('login', Unauthorized_error="Unauthorized Access. Please login first."))
@app.errorhandler(403)
def Forbidden(error_access):
    return redirect(url_for('login', Unauthorized_error="Need to ADMIN Access. Please login first."))
@app.route("/profile-edit",methods=["Post","get"])
@login_required
def profile_edit():
    update_form=UpdateForm()
    data = profile_data_injection()
    if data['status']:
        update_form.name.data=data['account_name']
        update_form.email.data=data['email']

        update_form.phn_no.data = data['phn_no']
        update_form.skype.data = data['skype']
        update_form.facebook.data = data['facebook']
        update_form.twitter.data = data['twitter']
        update_form.instagram.data = data['instagram']
        update_form.linkedin.data = data['linkedin']

    if update_form.validate_on_submit():
        print("Validation True")
        if update_form.validate_on_submit():
            userGiven_password = request.form.get('password')
            new_password = request.form.get('new_password')
            print("Validation True")
            if update_form.change_password.data:
                print("CheckBox Checked")
                if not request.form.get('new_password') and not request.form.get('confirm_password'):
                    error_msg = "* Must be required."
                    print(error_msg)
                    return render_template("profile_edit.html", form=update_form, error_pass=error_msg)
                else:
                        #For Change Password and Other Info
                    if check_password_hash(current_user.password,userGiven_password):

                        current_user.name = request.form.get('name')
                        current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256',salt_length=8)
                        current_user.phn_no= request.form.get('phn_no')
                        current_user.skype = request.form.get('skype')

                        current_user.facebook= request.form.get('facebook')
                        current_user.twitter= request.form.get('twitter')
                        current_user.instagram= request.form.get('instagram')
                        current_user.linkedin= request.form.get('linkedin')

                        file = request.files['image_data']
                        if file:
                            image_read = file.read()
                            current_user.image_data = image_read
                            db.session.commit()
                            print("Updated: {email}")
                        else:
                            db.session.commit()
                            print("No file")

                    else:
                        error_msg = "* Password Wrong. Try again."

                        return render_template("profile_edit.html", form=update_form, wrong_pass=error_msg)
            else:
                if check_password_hash(current_user.password, userGiven_password):

                    current_user.name = request.form.get('name')
                    current_user.phn_no = request.form.get('phn_no')
                    current_user.skype = request.form.get('skype')

                    current_user.facebook = request.form.get('facebook')
                    current_user.twitter = request.form.get('twitter')
                    current_user.instagram = request.form.get('instagram')
                    current_user.linkedin = request.form.get('linkedin')


                    file = request.files['image_data']
                    if file:
                        image_read = file.read()
                        current_user.image_data=image_read
                        db.session.commit()
                        print("Updated: {email}")
                    else:
                        db.session.commit()
                        print("No file")



                else:
                    error_msg = "* Password Wrong. Try again."

                    return render_template("profile_edit.html", form=update_form, wrong_pass=error_msg)
        else:
            print(" False 2st One")
        return render_template("profile_edit.html",form=update_form)

    else:
        print("Not validate")
        # failed_field = list(update_form.errors.keys())[0]
        # error_message = update_form.errors[failed_field][0]
        # print(f"The field '{failed_field}' failed validation. Error: {error_message}")

    return render_template("profile_edit.html",form=update_form)

@app.route("/profile-view")
def profile_view():
    pro_view=ViewForm()
    author_id = request.args.get("author")
    author_details=db.session.query(User).get(author_id)

    pro_view.name.data = author_details.name
    pro_view.email.data = author_details.email
    pro_view.phn_no.data = author_details.phn_no
    pro_view.skype.data = author_details.skype
    pro_view.facebook.data = author_details.facebook
    pro_view.twitter.data = author_details.twitter
    pro_view.instagram.data = author_details.instagram
    pro_view.linkedin.data = author_details.linkedin

    img = author_details.image_data
    profile_image = f"data:image/jpeg;base64,{base64.b64encode(img).decode('utf-8')}"

    return render_template("profile_view.html",form=pro_view,img=profile_image)


class UpdateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(message='* Name is required.')])
    phn_no = StringField('Mobile number', validators=[DataRequired(message='* Mobile Number is required.')])
    email = StringField('Email', validators=[DataRequired(message='* Email is required.'), Email()])
    skype = StringField('Skype', validators=[DataRequired(message='* Skype ID is required.')])
    facebook = StringField('Facebook', validators=[DataRequired(message='* Facebook is required.')])
    twitter = StringField('Twitter', validators=[DataRequired(message='* Twitter is required.')])
    linkedin = StringField('Linkedin', validators=[DataRequired(message='* Linkedin is required.')])
    instagram = StringField('Instagram', validators=[DataRequired(message='* Instagram is required.')])

    change_password = BooleanField('Would you like to change your password?')

    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=8, message='* Password must be at least 8 characters long.'),
        EqualTo('confirm_password', message='* Passwords must match.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        Optional(),
        EqualTo('new_password', message='* Passwords must match.')
    ])
    password = PasswordField('Current Password', validators=[
        DataRequired(message='* Current Password is required.'),
        Length(min=8, message='* Password must be at least 8 characters long.')
    ])


class ViewForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(message='* Name is required.')])
    phn_no = StringField('Mobile number', validators=[DataRequired(message='* Mobile Number is required.')])
    email = StringField('Email', validators=[DataRequired(message='* Email is required.'), Email()])
    skype = StringField('Skype', validators=[DataRequired(message='* Skype ID is required.')])
    facebook = StringField('Facebook', validators=[DataRequired(message='* Facebook is required.')])
    twitter = StringField('Twitter', validators=[DataRequired(message='* Twitter is required.')])
    linkedin = StringField('Linkedin', validators=[DataRequired(message='* Linkedin is required.')])
    instagram = StringField('Instagram', validators=[DataRequired(message='* Instagram is required.')])




@app.route("/update",methods=["post","get"])
def update():

    return "updated"

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=5000)