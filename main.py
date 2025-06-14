from flask import Flask, render_template
from flask_bootstrap import Bootstrap5

app = Flask(__name__)
bootstrap = Bootstrap5(app)

@app.route("/")
def homepage():
    return render_template("index.html", page="home")

@app.route("/benchmark")
def benchmark():
    return render_template("benchmark.html", page="benchmark")

if __name__ == '__main__':
    app.run(debug=True, port=5000)