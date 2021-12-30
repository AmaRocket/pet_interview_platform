from marshmallow import fields, validate

from app import db, ma
from app.models import *


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        include_relationship = True
        load_instance = True
        exclude = ['id', 'password_hash']

        id = ma.auto_field()
        username = fields.Str(validate=[validate.Length(64)], required=True)
        email = fields.Str(required=True)
        password_hash = fields.Str(validate=[validate.Length(255)], required=True)
        admin = fields.Boolean(default=False, required=True)


class InterviewSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Interview
        include_relationship = True
        load_instance = True

        id = ma.auto_field()
        candidate_name = fields.Str(required=True, validate=[validate.Length(64)])
        question_list = fields.Nested("QuestionSchema", default=[], many=True, required=True)
        interviewers = fields.Nested("UserSchema", default=[], many=True, required=True)
        result_grade = fields.Decimal(rounding="2", required=True)


class QuestionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Question
        include_relationship = True
        load_instance = True

    id = ma.auto_field()
    question_description = fields.Str(required=True, validate=validate.Length(128))
    answer = fields.Str(required=True, validate=validate.Length(64))
    max_grade = fields.Int(required=True)


class PostSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Post
        include_relationship = True
        load_instance = True

        id = ma.auto_field()
        body = fields.Str(required=True, validate=validate.Length(140))


class GradeSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Grade
        include_relationship = True
        load_instance = True

        id = ma.auto_field()
        question_id = fields.Int(required=True)
        interviewer_id = fields.Int(required=True)
        interview_id = fields.Int(required=True)
        question = fields.Nested("QuestionSchema", default=[], required=True)
        interviewer = fields.Nested("UserSchema", default=[], required=True)
        interview = fields.Nested("InterviewSchema", default=[], required=True)
        grade = fields.Int(nullable=True)
