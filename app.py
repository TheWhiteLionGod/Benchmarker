# Imports
from flask import Flask, render_template, redirect, jsonify
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired
from threading import Thread
from os import urandom

from utils.benchmark import benchmark as bm
from utils.html_utils import get_html
from utils.ai_utils import generate_ai_feedback_async

# Flask App Config
app = Flask(__name__)
app.config['SECRET_KEY'] = urandom(32)
bootstrap = Bootstrap5(app)

# Code Form
class CodeForm(FlaskForm):
    program1 = TextAreaField("Function 1", validators=[DataRequired()])
    program2 = TextAreaField("Function 2", validators=[DataRequired()])
    params = TextAreaField('Enter Parameters for your Functions', validators=[DataRequired()])
    submit = SubmitField("Evaluate")

# Global Variable and Status Management
result = {"Func1Times": [], "Func2Times": [], "Func1Score": 0, "Func2Score": 0}
ai_feedback_status = {"status": "pending", "progress": 0}

# Homepage Route
@app.route("/")
def homepage():
    return render_template("index.html", page="home")

# Benchmarking Route
@app.route("/benchmark", methods=['GET', 'POST'])
def benchmark():
    global result, ai_feedback_status
    program = CodeForm()
    if program.validate_on_submit():
        program1 = program.program1.data
        program2 = program.program2.data
        params = program.params.data

        # Updating Parameters
        if params.strip() == "":
            params = "params = [i for i in range(10)]"
        else:
            # If user didn't include 'params =' at the start, add it
            params = params.strip()
            if not params.startswith('params ='):
                params = f"params = {params}"

        # Run benchmark first (fast operation)
        print("Running benchmark...")
        result = bm(program1, program2, params)
        
        if result == 'Invalid Parameters':
            return render_template("crash.html", page="chart", reason="Parameters Entered are Invalid")
        elif result == 'Function 1 Crashed':
            return render_template("crash.html", page="chart", reason="Function 1 crashed while Testing")
        elif result == 'Function 2 Crashed':
            return render_template("crash.html", page="chart", reason="Function 2 crashed while Testing")
        
        # Store original code for display
        result["Program1Code"] = program1
        result["Program2Code"] = program2
        
        # Initialize AI feedback placeholders
        result["AI_Feedback1"] = "Analyzing function performance..."
        result["AI_Feedback2"] = "Analyzing function performance..."
        result["Comparative_Feedback"] = "Generating comparative analysis..."
        
        # Reset AI feedback status
        ai_feedback_status = {"status": "pending", "progress": 0}
        
        # Start AI feedback generation in background thread
        ai_thread = Thread(target=generate_ai_feedback_async, args=({"result": result, "ai_feedback_status": ai_feedback_status},))
        ai_thread.daemon = True
        ai_thread.start()
        
        return redirect('chart')
    return render_template("benchmark.html", page="benchmark", form=program)

# Chart Route
@app.route("/chart")
def chart():
    global result
    if result.get("Func1Times") is None:
        return redirect('benchmark')
    elif result.get("Func2Times") is None:
        return redirect('benchmark')
    elif result.get("Func1Score") is None:
        return redirect('benchmark')
    elif result.get("Func2Score") is None:
        return redirect('benchmark')
    elif result.get("AI_Feedback1") is None:
        return redirect('benchmark')
    elif result.get("AI_Feedback2") is None:
        return redirect('benchmark')
    elif result.get("Comparative_Feedback") is None:
        return redirect('benchmark')
    elif result.get("Program1Code") is None:
        return redirect('benchmark')
    elif result.get("Program2Code") is None:
        return redirect('benchmark')
    
    ai_feedback1_html = get_html(result.get("AI_Feedback1", "AI feedback not available"))
    ai_feedback2_html = get_html(result.get("AI_Feedback2", "AI feedback not available"))
    comparative_feedback_html = get_html(result.get("Comparative_Feedback", "Comparative feedback not available"))
    
    return render_template("chart.html",
                        labels=[f"Test {i}" for i in range(1, len(result["Func1Times"])+1)],
                        page="chart",
                        program1=result.get("Func1Times"), 
                        program2=result.get("Func2Times"),
                        avg1=result.get("Func1Score"),
                        avg2=result.get("Func2Score"),
                        ai_feedback1=ai_feedback1_html,
                        ai_feedback2=ai_feedback2_html,
                        comparative_feedback=comparative_feedback_html,
                        program1_code=result.get("Program1Code", ""),
                        program2_code=result.get("Program2Code", "")
                        )

# Api Routes
@app.route("/api/feedback")
def api_feedback():
    """API endpoint to get current AI feedback status and results"""
    global result, ai_feedback_status
    return jsonify({
        "status": ai_feedback_status.get("status", "pending"),
        "progress": ai_feedback_status.get("progress", 0),
        "error": ai_feedback_status.get("error", None),
        "ai_feedback1": result.get("AI_Feedback1", "Not available"),
        "ai_feedback2": result.get("AI_Feedback2", "Not available"),
        "comparative_feedback": result.get("Comparative_Feedback", "Not available")
    })

@app.route("/api/feedback/refresh")
def refresh_feedback():
    """API endpoint to manually refresh AI feedback"""
    global ai_feedback_status
    
    if ai_feedback_status.get("status") == "generating": return jsonify({"error": "AI feedback is already being generated"}), 400
    
    # Start new AI feedback generation
    ai_thread = Thread(target=generate_ai_feedback_async, args=({"result": result, "ai_feedback_status": ai_feedback_status},))
    ai_thread.daemon = True
    ai_thread.start()
    
    return jsonify({"message": "AI feedback refresh started"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)