from flask_sqlalchemy import Model
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from wtforms import ValidationError

from app import db, app
from app import login

from hashlib import md5  # for downloading avatar

# ----------------------------SUPPORTING-TABLES-OF-RELATIONS------------------------------------------------------------

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

interview_question = db.Table(
    'interview_question',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id')),
    db.Column('interview_id', db.Integer, db.ForeignKey('interview.id'))
)

interview_user = db.Table(
    'interview_user',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('interview_id', db.Integer, db.ForeignKey('interview.id'))
)


# -----------------------------------------------------------------------------------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    admin = db.Column(db.Boolean)  # make False when admin will be created
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    """ RELATIONS"""
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship(
        'User', secondary=followers,  # secondary - configures association table that used for this association User
        primaryjoin=(followers.c.follower_id == id),  # condition assoc object(follower user) with association table
        secondaryjoin=(followers.c.followed_id == id),  # condition that binds object(follower user) to assoc table.
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic')  # determine how this link will be available

    def __repr__(self):
        return f"{self.username}"

    # User settings
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):  # function for default avatar Gravatar
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    # For Blog
    # CRUD RELATIONS WITH USERS
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    # For interview
    @staticmethod
    def get_selection_list():  # get choose list
        res = []
        try:
            for i in User.query.all():
                res.append((f"{i.id}", f"{i.username}"))
            return res
        except AttributeError:
            return []


# ----------------------Flask-Login user loader function----------------------------------------------------------------

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# -----------------------------------------------------------------------------------------------------------------------


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"{self.body}"


# -----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------INTERVIEW----------------------------------------------------

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_description = db.Column(db.Text)
    answer = db.Column(db.String(64))
    max_grade = db.Column(db.Integer)
    short_description = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f"{self.short_description}"

    @staticmethod
    def get_selection_list():
        result = []
        for i in Question.query.all():
            result.append((f"{i.id}", f"{i.short_description}"))
        return result


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(64), nullable=False)
    result_grade = db.Column(db.Float(precision=2))
    link = db.Column(db.String)
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    short_description = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    """ RELATIONS """
    question_list = db.relationship('Question',
                                    secondary=interview_question,
                                    backref=db.backref('interview', lazy=True),
                                    lazy='subquery')
    interviewers = db.relationship('User',
                                   secondary=interview_user,
                                   backref=db.backref('interview', lazy=True),
                                   lazy='subquery')

    def __repr__(self):
        return f'{self.candidate_name} {self.result_grade}'

    @staticmethod
    def get_selection_list():
        result = []
        for i in Interview.query.all():
            result.append((f"{i.id}", f"{i.candidate_name}"))
        return result

    # def avatar(self, size):  # function for default avatar Gravatar
    #     digest = md5(self.email.lower().encode('utf-8')).hexdigest()
    #     return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
    #         digest, size)


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    interviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    grade = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    """ RELATIONS """
    interview = db.relationship("Interview", backref="grade")
    question = db.relationship("Question", backref="grade")
    interviewer = db.relationship("User", backref="grade")

    def __repr__(self):
        return f"{self.interviewer}   rated    {self.interview} - {self.grade}, for {self.question}"

    def max_grade(question, grade):
        max_grade = Question.query.filter_by(id=question.data.get('question')).first().max_grade
        if grade.data > max_grade:
            raise ValidationError('Grade bigger that maximum for this question')