from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, DateField, \
    TimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, NumberRange
from wtforms.fields import SelectMultipleField, SelectField

from app.models import User, Question, Interview, Grade


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    def validate_password(self, password):
        user = User.query.filter_by(password_hash=password.data).first()
        if user is not None:
            raise ValidationError('Please use a different password.')


class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email')
    password = PasswordField('Password', validators=[DataRequired()])
    admin = BooleanField('Admin status', default=False)
    submit = SubmitField('Submit')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=256)])
    submit = SubmitField('Submit')


# ------------------------FORMS_FOR_INTERVIEW---------------------------------------------------------------------------


class QuestionForm(FlaskForm):
    question_description = TextAreaField('Question:', validators=[DataRequired()])
    answer = StringField('Answer:', validators=[DataRequired()])
    max_grade = IntegerField('Max Grade:', validators=[DataRequired(), NumberRange(min=1, max=10)], default=10)
    short_description = StringField('Short description:', validators=[DataRequired()])
    submit = SubmitField('Submit')


class InterviewForm(FlaskForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    candidate_name = StringField('Candidate Name:', validators=[DataRequired()])
    question_list = SelectMultipleField('Choose Questions (Use CTRL/Command For Choose Many Questions):',
                                        choices=Question.get_selection_list())
    interviewers = SelectMultipleField('Choose Interviewers (Use CTRL/Command For Choose Many Interviewers):',
                                       choices=User.get_selection_list())
    link = StringField('Enter Link For Interview Call')
    date = DateField('Date of Interview')
    time = TimeField('Time of Interview')
    short_description = TextAreaField('Short Description', validators=[DataRequired()])
    submit = SubmitField('Submit')

    @classmethod
    def new(cls):
        form = cls()
        form.interviewers.choices = User.get_selection_list()
        form.question_list.choices = Question.get_selection_list()
        return form


class GradeForm(FlaskForm):
    interviewers = SelectField('Choose Interviewers:', choices=User.get_selection_list())
    interviews = SelectField('Choose Interview:', choices=Interview.get_selection_list())
    question_list = SelectField('Choose Questions:', choices=Question.get_selection_list())
    grade = IntegerField('Choose Grade', validators=[DataRequired(), NumberRange(min=0, max=10)], default=10)
    submit = SubmitField('Submit')

    @classmethod
    def new(cls):
        form = cls()
        form.interviewers.choices = User.get_selection_list()
        form.question_list.choices = Question.get_selection_list()
        form.interviews.choices = Interview.get_selection_list()
        return form
