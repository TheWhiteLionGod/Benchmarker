from flask import Flask, render_template, redirect
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

import os
import math
import benchmark as bm

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
bootstrap = Bootstrap5(app)

class CodeForm(FlaskForm):
    program1 = TextAreaField("Program 1", validators=[DataRequired()])
    program2 = TextAreaField("Program 2", validators=[DataRequired()])
    params = TextAreaField('Params')
    submit = SubmitField("Evaluate")


result = {"Func1Times": [], "Func2Times": [], "Func1Average": 0, "Func2Average": 0} 

@app.route("/")
def homepage():
    return render_template("index.html", page="home")

@app.route("/benchmark", methods=['GET', 'POST'])
def benchmark():
    global result
    program = CodeForm()
    if program.validate_on_submit():
        program1 = program.program1.data
        program2 = program.program2.data
        params = program.params.data
        iterations = 0

        # Updating Parameters
        if params == "":
            iterations = 10
            params = """
params = [i for i in range(10)]
"""
        else:
            iterations = len(eval(params))
            params = f"""
params = {params}
"""

        # Benchmarking Results
        result = bm.benchmark(program1, program2, params, iterations)
        return redirect('chart')

    return render_template("benchmark.html", page="benchmark", form=program)

@app.route("/chart")
def chart():
    global result
    return render_template("chart.html", 
                           page="chart",
                           labels=[f"Param Set {i}" for i in range(1, len(result["Func1Times"])+1)], 
                           program1=result["Func1Times"], program2=result["Func2Times"],
                           avg1=result["Func1Average"], avg2=result["Func2Average"]
                           )

if __name__ == '__main__':
    app.run(debug=True, port=5000)