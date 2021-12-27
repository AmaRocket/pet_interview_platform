from app import app, db
from app.models import User, Post, Question, Interview, Grade


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Question': Question, 'Interview': Interview, 'Grade': Grade}


if __name__ == "__main__":
    app.run("0.0.0.0", 5000, debug=True)
