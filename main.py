from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import exc
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, URL, Email
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
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)




##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post" )

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


@app.route("/post/<int:index>")
def show_post(index):
    requested_post = None
    posts = db.session.query(BlogPost).all()
    for blog_post in posts:
        if blog_post.id == index:
            requested_post = blog_post
    return render_template("post.html", post=requested_post)



@app.route("/edit/<int:post_id>" , methods=["GET", "POST"])
def edit_post(post_id):
    try:
        post_to_update = BlogPost.query.get(post_id)
        update_form = CreatePostForm(
            title=post_to_update.title,
            subtitle=post_to_update.subtitle,
            img_url=post_to_update.img_url,
            author=post_to_update.author,
            body=post_to_update.body
        )
        if request.method == 'POST':
            post_to_update.title = request.form["title"]
            post_to_update.subtitle = request.form["subtitle"]
            post_to_update.author = request.form["author"]
            post_to_update.img_url = request.form["img_url"]
            post_to_update.body = request.form["body"]
            post_to_update.date = datetime.now().strftime("%B %d, %Y")

            db.session.commit()
            return redirect(url_for("show_post", index=post_id))


    except Exception as e:
        # Handle any other exceptions
        Blank_form = CreatePostForm(
            title="****",
            subtitle="****",
            img_url="****",
            author="****",
            body="****"
        )
        disable_form_fields(Blank_form)
        error_message = "*No Data Found!"
        return render_template('make-post.html', error=error_message, post_form=Blank_form)


    return render_template("make-post.html", post_form=update_form, is_edit=True)



@app.route("/new-post", methods=["GET", "POST"])
def create_post():
    new_post_form = CreatePostForm()
    if request.method == 'POST':
        try:
            new_post= BlogPost(
            title=request.form["title"],
            subtitle=request.form["subtitle"],
            author=request.form["author"],
            img_url=request.form["img_url"],
            body=request.form["body"],
            date = datetime.now().strftime("%B %d, %Y"),
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


if __name__ == "__main__":
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=5000)