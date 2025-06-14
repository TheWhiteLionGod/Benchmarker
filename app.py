from flask import Flask, render_template, redirect
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

import os
import benchmark as bm

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
bootstrap = Bootstrap5(app)

class CodeForm(FlaskForm):
    code = TextAreaField("Program", validators=[DataRequired()])
    submit = SubmitField("Evaluate")


arr = list(range(1, 1000000))
params = [
    (arr, 500000),
    (arr, 567890),
    (arr, 432100),
    (arr, 876543),
    (arr, 123456),
    (arr, 999999),
    (arr, 1),
    (arr, 1000000),
    (arr, 10001),
    (arr, -1) 
]

result = {}

@app.route("/")
def homepage():
    return render_template("index.html", page="home")

@app.route("/benchmark", methods=['GET', 'POST'])
def benchmark():
    global result
    form = CodeForm()
    if form.validate_on_submit():
        code = form.code.data
        result = bm.benchmark(code, code, params, 10)
        return redirect('chart')

    return render_template("benchmark.html", page="benchmark", form=form)

@app.route("/chart")
def chart():
    global result
    return render_template("chart.html", labels=[i for i in result], data=[result[i] for i in result])

if __name__ == '__main__':
    app.run(debug=True, port=5000)