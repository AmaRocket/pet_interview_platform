from flask import jsonify, request
from flask_login import login_user, login_required, logout_user, current_user
from flask_restful import Resource

from app import db
from app.forms import LoginForm
from app.models import User, Question, Interview, Grade, Post
from app.schema import *


class MainResource(Resource):

    def get_model_query(self):
        pass

    def edit_object(self):
        pass

    def create_object(self):
        pass

    def get_schema(self):
        pass


    @login_required
    def get(self):
        schema = self.get_schema()
        model_schema = schema(many=True)
        if isinstance(model_schema, UserSchema) and current_user.admin != True:
            return {"error": "You Are Not Admin"}
        args = request.args
        model_objects = self.get_model_query(args=args).all()
        output = model_schema.dump(model_objects)
        return jsonify(output)


    @login_required
    def delete(self):
        if isinstance(self.get_schema()(), UserSchema) and current_user.admin != True:
            return {"error": "You Are Not Admin"}
        args = request.args
        model_object = self.get_model_query(args).first()
        db.session.delete(model_object)
        db.session.commit()
        return {'success': 'True'}

    @login_required
    def patch(self):
        object_schema = self.get_schema()()
        if isinstance(object_schema, UserSchema) and current_user.admin != True:
            return {"error": "You Are Not Admin"}
        args = request.args
        model_object = self.get_model_query(args).first()
        form = request.form
        model_object = self.edit_object(model_object, form)
        output = object_schema.dump(model_object)
        db.session.commit()
        return jsonify(output)

    @login_required
    def post(self):
        if isinstance(self.get_schema()(), UserSchema) and current_user.admin  != True:
            return {"error": "You Are Not Admin"}
        form = request.form
        model_object = self.create_object(form=form)
        db.session.add(model_object)
        db.session.commit()
        return {'result': 'done'}


class UserApi(MainResource):

    def get_model_query(self, args):
        users = User.query
        if args.get("id"):
            users = users.filter_by(id=args.get('id'))
        if args.get("username"):
            users = users.filter_by(username=args.get('username'))
        if args.get('email'):
            users = users.filter_by(email=args.get('email'))

        return users

    def edit_object(self, user, form):
        if form.get("username"):
            user.username = form.get('username')
        if form.get('email'):
            user.email = form.get('email')

        return user

    def create_object(self, form):
        user = User()
        if not form.get("username") or not form.get("password"):
            raise Exception("no username or password")
        user = self.edit_object(user, form)
        return user

    def get_schema(self):
        return