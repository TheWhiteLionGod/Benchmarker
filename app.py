from flask import Flask, render_template, redirect, jsonify
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired

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


result = {"Func1Times": [], "Func2Times": [], "Func1Average": 0, "Func2Average": 0} 

def get_ai_feedback(func_code, func_name, execution_times, ollama_host=None):
    """
    Get AI feedback on function performance using CodeGemma
    
    Args:
        func_code: The function source code as string
        func_name: Name of the function
        execution_times: List of execution times
        ollama_host: Ollama server URL
    
    Returns:
        AI feedback as string
    """
    ollama_host = os.environ["OLLAMA_HOST"] if ollama_host is None else ollama_host

    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)
    
    # Create prompt for CodeGemma
    prompt = f"""
Analyze this Python function for performance and provide constructive feedback:

Function: {func_name}
```python
{func_code}
```

Performance Metrics:
- Average execution time: {avg_time:.6f} seconds
- Minimum execution time: {min_time:.6f} seconds  
- Maximum execution time: {max_time:.6f} seconds
- Total test runs: {len(execution_times)}

Please provide:
1. Performance assessment (fast, average, slow)
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
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: Failed to get response from Ollama (Status: {response.status_code})"    
            
    except requests.RequestException as e:
        return f"Error connecting to Ollama: {str(e)}"

def get_comparative_feedback(func1_code, func2_code, func1_times, func2_times, ollama_host=None):
    """
    Get comparative AI feedback for two functions
    """
    ollama_host = os.environ["OLLAMA_HOST"] if ollama_host is None else ollama_host

    avg1 = sum(func1_times) / len(func1_times)
    avg2 = sum(func2_times) / len(func2_times)
    
    comparative_prompt = f"""
Compare these two Python functions for performance:

Function 1:
```python
{func1_code}
```
Average execution time: {avg1:.6f} seconds

Function 2:
```python
{func2_code}
```
Average execution time: {avg2:.6f} seconds

Please provide:
1. Which function performs better and why
2. Performance difference analysis ({abs(avg1-avg2):.6f} seconds difference)
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
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return "Error getting comparative feedback"
            
    except Exception as e:
        return f"Error getting comparative feedback: {str(e)}"

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

        # Updating Parameters
        if params == "":
            params = """
params = [i for i in range(10)]
"""
        else:
            params = f"""
params = {params}
"""

        # Benchmarking Results
        
        # Run benchmark
        result = bm.benchmark(program1, program2, params)
        
        # Get AI feedback for both functions
        print("Getting AI feedback...")
        result["AI_Feedback1"] = get_ai_feedback(program1, "Function 1", result["Func1Times"])
        result["AI_Feedback2"] = get_ai_feedback(program2, "Function 2", result["Func2Times"])
        result["Comparative_Feedback"] = get_comparative_feedback(program1, program2, result["Func1Times"], result["Func2Times"])
        
        # Store original code for display
        result["Program1Code"] = program1
        result["Program2Code"] = program2
        
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
                           labels=[f"Param Set {i}" for i in range(1, len(result["Func1Times"])+1)],
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
    """API endpoint to get AI feedback separately if needed"""
    global result
    return jsonify({
        "ai_feedback1": result.get("AI_Feedback1", "Not available"),
        "ai_feedback2": result.get("AI_Feedback2", "Not available"),
        "comparative_feedback": result.get("Comparative_Feedback", "Not available")
    })

if __name__ == '__main__':
    app.run(debug=False, port=5000)