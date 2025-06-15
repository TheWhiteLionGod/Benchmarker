from flask import Flask, render_template, redirect, jsonify, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired
import threading
import time
import os
import requests
import benchmark as bm

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
bootstrap = Bootstrap5(app)

# Set up Ollama host
os.environ["OLLAMA_HOST"] = "https://1e77-68-194-75-55.ngrok-free.app"

class CodeForm(FlaskForm):
    program1 = TextAreaField("Function 1", validators=[DataRequired()])
    program2 = TextAreaField("Function 2", validators=[DataRequired()])
    params = TextAreaField('Enter Parameters for your Functions(Optional)')
    submit = SubmitField("Evaluate")

result = {"Func1Times": [], "Func2Times": [], "Func1Score": 0, "Func2Score": 0}
ai_feedback_status = {"status": "pending", "progress": 0}

def get_ai_feedback(func_code, func_name, raw_times, score, ollama_host=None):
    """
    Get AI feedback on function performance using CodeGemma
    
    Args:
        func_code: The function source code as string
        func_name: Name of the function
        raw_times: List of raw execution times
        score: Calculated performance score
        ollama_host: Ollama server URL
    
    Returns:
        AI feedback as string
    """
    ollama_host = os.environ["OLLAMA_HOST"] if ollama_host is None else ollama_host

    avg_time = sum(raw_times) / len(raw_times)
    min_time = min(raw_times)
    max_time = max(raw_times)
    
    # Create prompt for CodeGemma
    prompt = f"""
Analyze this Python function for performance and provide constructive feedback:

Function: {func_name}
```python
{func_code}
```

Performance Metrics:
- Performance Score: {score} (higher is better, based on -log10(avg_time) * 10)
- Average execution time: {avg_time:.6f} seconds
- Minimum execution time: {min_time:.6f} seconds  
- Maximum execution time: {max_time:.6f} seconds
- Total test runs: {len(raw_times)}

Please provide:
1. Performance assessment based on the score and execution times
2. Potential bottlenecks or inefficiencies
3. Optimization suggestions
4. Code quality observations
5. Consistency analysis (based on min/max variation)

Keep the feedback concise and actionable.
"""

    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": "codegemma:instruct",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: Failed to get response from Ollama (Status: {response.status_code})"    
            
    except requests.RequestException as e:
        return f"Error connecting to Ollama: {str(e)}"

def get_comparative_feedback(func1_code, func2_code, func1_times, func2_times, func1_score, func2_score, ollama_host=None):
    """
    Get comparative AI feedback for two functions
    """
    ollama_host = os.environ["OLLAMA_HOST"] if ollama_host is None else ollama_host

    avg1 = sum(func1_times) / len(func1_times)
    avg2 = sum(func2_times) / len(func2_times)
    
    # Determine which function is better based on score (higher is better)
    better_func = "Function 1" if func1_score > func2_score else "Function 2"
    score_diff = abs(func1_score - func2_score)
    time_diff = abs(avg1 - avg2)
    
    comparative_prompt = f"""
Compare these two Python functions for performance:

Function 1:
```python
{func1_code}
```
Performance Score: {func1_score} (higher is better)
Average execution time: {avg1:.6f} seconds

Function 2:
```python
{func2_code}
```
Performance Score: {func2_score} (higher is better)
Average execution time: {avg2:.6f} seconds

Analysis:
- {better_func} performs better with a score difference of {score_diff:.3f} points
- Time difference: {time_diff:.6f} seconds
- Score calculation uses -log10(avg_time) * 10, so higher scores indicate faster execution

Please provide:
1. Which function performs better and why
2. Performance difference analysis and significance
3. Trade-offs between the approaches
4. Recommendations for optimization
5. When to use each approach

Keep the analysis concise and practical.
"""

    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": "codegemma:instruct",
                "prompt": comparative_prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return "Error getting comparative feedback"
            
    except Exception as e:
        return f"Error getting comparative feedback: {str(e)}"

def generate_ai_feedback_async():
    """
    Generate AI feedback in background thread
    """
    global result, ai_feedback_status
    
    try:
        ai_feedback_status["status"] = "generating"
        ai_feedback_status["progress"] = 10
        
        # Get AI feedback for function 1
        print("Getting AI feedback for Function 1...")
        result["AI_Feedback1"] = get_ai_feedback(
            result["Program1Code"], "Function 1", result["Func1Times"], result["Func1Score"]
        )
        ai_feedback_status["progress"] = 40
        
        # Get AI feedback for function 2
        print("Getting AI feedback for Function 2...")
        result["AI_Feedback2"] = get_ai_feedback(
            result["Program2Code"], "Function 2", result["Func2Times"], result["Func2Score"]
        )
        ai_feedback_status["progress"] = 70
        
        # Get comparative feedback
        print("Getting comparative feedback...")
        result["Comparative_Feedback"] = get_comparative_feedback(
            result["Program1Code"], result["Program2Code"], 
            result["Func1Times"], result["Func2Times"],
            result["Func1Score"], result["Func2Score"]
        )
        ai_feedback_status["progress"] = 100
        ai_feedback_status["status"] = "complete"
        
        print("AI feedback generation complete!")
        
    except Exception as e:
        ai_feedback_status["status"] = "error"
        ai_feedback_status["error"] = str(e)
        result["AI_Feedback1"] = f"Error generating feedback: {str(e)}"
        result["AI_Feedback2"] = f"Error generating feedback: {str(e)}"
        result["Comparative_Feedback"] = f"Error generating feedback: {str(e)}"

@app.route("/")
def homepage():
    return render_template("index.html", page="home")

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
        result = bm.benchmark(program1, program2, params)
        
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
        ai_thread = threading.Thread(target=generate_ai_feedback_async)
        ai_thread.daemon = True
        ai_thread.start()
        
        return redirect('chart')
    return render_template("benchmark.html", page="benchmark", form=program)

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
    
    return render_template("chart.html",
                           labels=[f"Test {i}" for i in range(1, len(result["Func1Times"])+1)],
                           page="chart",
                           program1=result.get("Func1Times"), 
                           program2=result.get("Func2Times"),
                           avg1=result.get("Func1Score"),
                           avg2=result.get("Func2Score"),
                           ai_feedback1=result.get("AI_Feedback1", "AI feedback not available"),
                           ai_feedback2=result.get("AI_Feedback2", "AI feedback not available"),
                           comparative_feedback=result.get("Comparative_Feedback", "Comparative feedback not available"),
                           program1_code=result.get("Program1Code", ""),
                           program2_code=result.get("Program2Code", "")
                           )

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
    
    if ai_feedback_status.get("status") == "generating":
        return jsonify({"error": "AI feedback is already being generated"}), 400
    
    # Start new AI feedback generation
    ai_thread = threading.Thread(target=generate_ai_feedback_async)
    ai_thread.daemon = True
    ai_thread.start()
    
    return jsonify({"message": "AI feedback refresh started"})

if __name__ == '__main__':
    app.run(debug=False, port=5000)