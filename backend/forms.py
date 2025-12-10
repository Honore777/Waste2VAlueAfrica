# backend/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange,URL,Optional
from flask_wtf.file import FileField, FileRequired, FileAllowed

from models import User, RoleEnum, Category

class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    role = SelectField(
        "Role",
        choices=[(role.value, role.value.capitalize()) for role in RoleEnum],
        validators=[DataRequired()]
    )
    submit = SubmitField("Register")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered.")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username already taken.")




# backend/forms.py
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")




class ListingForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=120)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=5)])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    unit = StringField("Unit (kg, pcs, etc.)", validators=[DataRequired(), Length(min=1, max=20)])
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Post Listing")

    def set_choices(self):
        # dynamically populate category choices
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]




## Community forms



class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=120)])
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=5)])

    image=FileField('Upload an image', validators=[FileAllowed(["jpg", "jpeg", "png", "webp"],'images only!')])
    submit = SubmitField("Post")




class EditProfileForm(FlaskForm):
    full_name= StringField('Full Name', validators=[Length(max=120)])
    bio= TextAreaField('Bio', validators=[Length(max=500)])
    location= StringField('Location', validators=[Length(max=120)])
    twitter = StringField("Twitter", validators=[Optional(), URL(), Length(max=255)])
    instagram = StringField("Instagram", validators=[Optional(), URL(), Length(max=255)]) 
    github= StringField("github", validators=[Optional(), URL(), Length(max=255)]) 
    submit= SubmitField('save changes')


ALLOWED_EXT= ["jpg", "jpeg", "png", "webp"]

class AvatarUploadForm(FlaskForm):
    avatar= FileField(
        'Upload Avatar',
        validators=[FileRequired(), FileAllowed(ALLOWED_EXT,'Images only(jpg,jpeg,png,webp)')]
    )

    submit= SubmitField('upload')
    