from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

import os

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
bootstrap = Bootstrap5(app)

class CodeForm(FlaskForm):
    code = TextAreaField("Program", validators=[DataRequired()])
    submit = SubmitField("Evaluate")


@app.route("/")
def homepage():
    return render_template("index.html", page="home")

@app.route("/benchmark", methods=['GET', 'POST'])
def benchmark():
    form = CodeForm()
    if form.validate_on_submit():
        code = form.code.data
        print(code)
    return render_template("benchmark.html", page="benchmark", form=form)

@app.route("/chart")
def chart():
    return render_template("chart.html")

if __name__ == '__main__':
    app.run(debug=True, port=5000)