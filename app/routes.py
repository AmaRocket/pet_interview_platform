from flask import render_template, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from app import app, db, login
from app.forms import LoginForm, RegistrationForm, EditProfileForm, UserForm, QuestionForm, InterviewForm, GradeForm, \
    GradeRateForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post, Question, Interview, Grade
from datetime import datetime
from app.forms import EmptyForm, PostForm


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required  # hide page from anonymous users
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


# ------------------------LOGIN/LOGOUT/REGISTER-------------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)  # after user execute login_user
        next_page = request.args.get('next')  # from Flask-Login u receive next argument
        if not next_page or url_parse(
                next_page).netloc != '':  # To determine URL relative or absolute, using the url_parse () function
            # then check if netloc component is installed or not.
            next_page = url_for('index')
            return redirect(next_page)
        return redirect(url_for('index'))  # after all redirect to login page
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# Hide From Users
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data,
                    admin=True)  # Set ADMIN=TRUE For Create Admin On Start
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------USER---------------------------------------------------------------------------

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():  # if return True copy data from form to user object and writing object to db
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.check_password = form.password.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.password.data = current_user.password_hash
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/users')
@login_required
def users():
    form = UserForm
    query = User.query.all()

    return render_template('users.html', query=query, form=form, user=user)


@app.route('/add-user', methods=['GET', 'POST'])
@login_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    admin=form.admin.data
                    )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("User Added")
        return redirect('/add-user')
    return render_template('add_user.html', title='Add-User', form=form)



@app.route('/users/<username>/delete', methods=['POST', 'GET'])
@login_required
def user_delete(username):
    if current_user.is_authenticated and current_user.admin == True:
        try:
            user = User.query.filter_by(username=username).first_or_404()
            db.session.delete(user)
            db.session.commit()
            flash('User removed')
            return redirect(url_for('user'))
        except:
            return 'Error'
    else:
        return redirect(url_for('permission_denied'))


# ----------------last seen---------------------------------------------------------------------------------------------
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------FOLLOW/UNFOLLOW---------------------------------------------------------------


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------INTERVIEW---------------------------------------------------------------------


@app.route('/questions')
@login_required
def questions():
    form = QuestionForm()
    page = request.args.get('page', 1, type=int)
    questions = Question.query.order_by(Question.timestamp.desc()).paginate(
        page, app.config['QUESTION_PER_PAGE'], False)
    next_url = url_for('questions', page=questions.next_num) \
        if questions.has_next else None
    prev_url = url_for('questions', page=questions.prev_num) \
        if questions.has_prev else None
    return render_template('questions.html', questions=questions.items, title="Questions", next_url=next_url,
                           prev_url=prev_url, form=form)


@app.route('/add-question', methods=["GET", "POST"])
@login_required
def add_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(question_description=form.question_description.data,
                            answer=form.answer.data,
                            max_grade=form.max_grade.data,
                            short_description=form.short_description.data
                            )
        db.session.add(question)
        db.session.commit()
        flash('Question Created Successfuly')
        return redirect('/add-question')
    return render_template('_add_question.html', form=form)


@app.route('/questions/<id>/delete', methods=['POST', 'GET'])
@login_required
def question_delete(id):
    if current_user.is_authenticated and current_user.admin == True:
        try:
            question = Question.query.filter_by(id=id).first_or_404()
            db.session.delete(question)
            db.session.commit()
            flash('Question Removed')
            return redirect(url_for('questions'))
        except:
            return render_template('404.html')
    else:
        return render_template('404.html')



@app.route('/interviews')
@login_required
def interviews():
    page = request.args.get('page', 1, type=int)
    interview = Interview.query.order_by(Interview.timestamp.desc()).paginate(
        page, app.config['INTERVIEW_PER_PAGE'], False)
    next_url = url_for('interviews', page=interview.next_num) \
        if interview.has_next else None
    prev_url = url_for('interviews', page=interview.prev_num) \
        if interview.has_prev else None
    return render_template("interviews.html", title='Interview', interview=interview.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/add-interview', methods=["GET", "POST"])
@login_required
def add_interview():
    form = InterviewForm().new()
    if form.validate_on_submit():
        question_list = []
        interviewers = []
        for question_id in form.question_list.data:
            question = Question.query.filter_by(id=question_id).first()
            question_list.append(question)
        for interviewer_id in form.interviewers.data:
            user = User.query.filter_by(id=interviewer_id).first()
            interviewers.append(user)
        interview = Interview(candidate_name=form.candidate_name.data,
                              question_list=question_list,
                              interviewers=interviewers,
                              date=form.date.data,
                              time=form.time.data,
                              link=form.link.data,
                              short_description=form.short_description.data
                              )
        all_objects = [interview]
        for user in interviewers:
            for question in question_list:
                grade = Grade(
                    question=question,
                    interviewer=user,
                    interview=interview
                )
                all_objects.append(grade)
        db.session.add_all(all_objects)
        db.session.commit()
        flash('Interview Created Successfuly')
        return redirect(url_for('interviews'))
    return render_template('_add_interview.html', form=form)


@app.route('/interviews/<id>/delete', methods=['POST', 'GET'])
@login_required
def interview_delete(id):
    if current_user.is_authenticated and current_user.admin == True:
        try:
            interview = Interview.query.filter_by(id=id).first_or_404()
            db.session.delete(interview)
            db.session.commit()
            flash('Interview removed')
            return redirect(url_for('interviews'))
        except:
            return render_template('404.html')
    else:
        return render_template('404.html')


@app.route('/my-interviews')
@login_required
def my_interviews():
    interviews = Interview.query.all()
    list_interview = []
    for interview in interviews:
        if current_user in interview.interviewers:
            list_interview.append(interview)
    return render_template('my_interviews.html', list_interview=list_interview, interviews=interviews)


@app.route('/my-interviews/<id>', methods=['GET', 'POST'])
def interview_detail(id):
    interview = Interview.query.filter_by(id=id).first_or_404()
    grades = Grade.query.filter_by(interview_id=id)
    interview.result_grade = interview.get_result_grade()
    db.session.commit()
    return render_template('interview_detail.html', interview=interview, grades=grades)


@app.route('/grades')
@login_required
def grades():
    form = GradeForm()
    page = request.args.get('page', 1, type=int)
    grade = Grade.query.order_by(Grade.timestamp.desc()).paginate(
        page, app.config['GRADE_PER_PAGE'], False)
    next_url = url_for('grades', page=grade.next_num) \
        if grade.has_next else None
    prev_url = url_for('grades', page=grade.prev_num) \
        if grade.has_prev else None
    return render_template("grades.html", title='Grade', grade=grade.items, form=form,
                           next_url=next_url, prev_url=prev_url)


@app.route('/add-grade', methods=['POST', 'GET'])
@login_required
def add_grade():
    form = GradeForm().new()
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.interviewers.data).first()
        interview = Interview.query.filter_by(id=form.interviews.data).first()
        question = Question.query.filter_by(id=form.question_list.data).first()

        grade = Grade(
            interviewer=user,
            # interviewer=current_user,
            question=question,
            interview=interview,
            # grade=1
            grade=form.grade.data
        )

        db.session.add(grade)

        interview.result_grade = interview.get_result_grade()
        db.session.commit()
        flash('Grade Added Successfuly')
        return redirect(url_for('my_interviews'))

    return render_template('_add_grade.html', form=form)


@app.route('/my-interviews/<id>/rate/<question_id>', methods=["POST", "GET"])
@login_required
def rate_question(id, question_id):
    form = GradeRateForm()
    question = Question.query.filter_by(id=question_id).first_or_404()
    if form.validate_on_submit():
        grade_select = Grade.query.filter_by(question_id=question_id,
                                             interview_id=id,
                                             interviewer_id=current_user.id).first_or_404()
        if 0 < int(form.grade.data) <= int(grade_select.question.max_grade):
            grade_select.grade = form.grade.data
            # db.session.add(result_grade)
            print(grade_select)

            db.session.commit()
        else:
            flash("You gave it more points than the question deserves. Try again. ")
        return redirect(f'/my-interviews/{id}')
    return render_template('rate_question.html', form=form, question=question)
