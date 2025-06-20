# Imports
from flask import Flask, render_template, redirect, jsonify
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired
from threading import Thread
from os import urandom
from atexit import register

from utils.benchmark import benchmark_async
from utils.html_utils import get_html
from utils.ai_utils import generate_ai_feedback_async, warmup_ollama, clear_cache
from utils.flask_utils import *

# Flask App Config
app = Flask(__name__)
app.config['SECRET_KEY'] = urandom(32)
bootstrap = Bootstrap5(app)

first_request = True

# Code Form
class CodeForm(FlaskForm):
    program1 = TextAreaField("Function 1", validators=[DataRequired()])
    program2 = TextAreaField("Function 2", validators=[DataRequired()])
    params = TextAreaField('Enter Parameters for your Functions', validators=[DataRequired()])
    submit = SubmitField("Evaluate")

# Initialize AI system on startup
def init_ai_system():
    """Initialize AI system with warmup and optimizations"""
    print("🚀 Initializing AI system...")
    try:
        # Warm up Ollama in a separate thread to avoid blocking startup
        warmup_thread = Thread(target=warmup_ollama)
        warmup_thread.daemon = True
        warmup_thread.start()
        print("✅ AI system initialization started")
    except Exception as e:
        print(f"⚠️ AI system initialization failed: {e}")

# Cleanup function for app shutdown
def cleanup_on_exit():
    """Clean up resources on app shutdown"""
    print("🧹 Cleaning up AI resources...")
    clear_cache()
    cleanup_old_sessions()

# Register cleanup function
register(cleanup_on_exit)

# Homepage Route
@app.route("/")
def homepage():
    return render_template("index.html", page="home")

# Benchmarking Route
@app.route("/benchmark", methods=['GET', 'POST'])
def benchmark():
    user_id = get_user_id()
    
    program = CodeForm()
    if program.validate_on_submit():
        program1 = program.program1.data
        program2 = program.program2.data
        params = program.params.data

        # Updating Parameters
        if params.strip() == "": params = "[i for i in range(10)]"
        else: params = params.strip()

        # Initialize benchmark status
        update_user_benchmark_status(user_id, "pending", 0, None, program1, program2, params)
        
        # Start benchmark in background thread
        benchmark_thread = Thread(target=benchmark_async, args=(user_id, program1, program2, params, user_data, user_benchmark_status))
        benchmark_thread.daemon = True
        benchmark_thread.start()
        
        # Periodic cleanup
        cleanup_old_sessions()
        
        return redirect('benchmark_status')
    return render_template("benchmark.html", page="benchmark", form=program)

# New benchmark status page
@app.route("/benchmark_status")
def benchmark_status():
    user_id = get_user_id()
    benchmark_status = get_user_benchmark_status(user_id)
    
    # If no benchmark in progress, redirect to benchmark page
    if not benchmark_status or benchmark_status.get("status") == "not_started":
        return redirect('benchmark')
    
    return render_template("benchmark_status.html", page="benchmark")

# Chart Route (modified to handle async results with better error handling)
@app.route("/chart")
def chart():
    user_id = get_user_id()
    
    # Check if user has all required data
    if not user_has_complete_data(user_id): 
        return redirect('benchmark')
    
    result = get_user_result(user_id)
    
    # Get AI feedback with fallback messages
    ai_feedback1_html = get_html(result.get("AI_Feedback1", "AI feedback loading... Please wait or refresh the page."))
    ai_feedback2_html = get_html(result.get("AI_Feedback2", "AI feedback loading... Please wait or refresh the page."))
    comparative_feedback_html = get_html(result.get("Comparative_Feedback", "Comparative feedback loading... Please wait or refresh the page."))
    
    # Check if AI feedback is still being generated and start if needed
    ai_status = get_user_ai_status(user_id)
    if not ai_status or ai_status.get("status") in ["pending", "not_started"]:
        # Initialize AI status if not exists
        if user_id not in user_ai_status:
            user_ai_status[user_id] = {"status": "pending", "progress": 0, "error": None}
        
        # Start AI feedback generation in background
        ai_thread = Thread(target=generate_ai_feedback_async, args=(user_id, user_data, user_ai_status))
        ai_thread.daemon = True
        ai_thread.start()
        print(f"Started AI feedback generation for user {user_id}")
    
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

# API Routes for benchmark status
@app.route("/api/benchmark")
def api_benchmark():
    """API endpoint to get current benchmark status and results"""
    user_id = get_user_id()
    benchmark_status = get_user_benchmark_status(user_id)
    
    return jsonify({
        "status": benchmark_status.get("status", "not_started"),
        "progress": benchmark_status.get("progress", 0),
        "error": benchmark_status.get("error", None),
        "current_test": benchmark_status.get("current_test", 0),
        "total_tests": benchmark_status.get("total_tests", 0),
        "message": benchmark_status.get("message", "")
    })

@app.route("/api/benchmark/restart")
def restart_benchmark():
    """API endpoint to restart benchmark"""
    user_id = get_user_id()
    benchmark_status = get_user_benchmark_status(user_id)
    
    if benchmark_status.get("status") == "running": 
        return jsonify({"error": "Benchmark is already running"}), 400
    
    # Get stored code and params
    program1 = benchmark_status.get("program1", "")
    program2 = benchmark_status.get("program2", "")
    params = benchmark_status.get("params", "")
    
    if not all([program1, program2, params]):
        return jsonify({"error": "No previous benchmark data found"}), 400
    
    # Reset status and start new benchmark
    update_user_benchmark_status(user_id, "pending", 0, None, program1, program2, params)
    
    benchmark_thread = Thread(target=benchmark_async, args=(user_id, program1, program2, params, user_data, user_benchmark_status))
    benchmark_thread.daemon = True
    benchmark_thread.start()
    
    return jsonify({"message": "Benchmark restarted"})

# Enhanced AI feedback API routes with better status reporting
@app.route("/api/feedback")
def api_feedback():
    """API endpoint to get current AI feedback status and results"""
    user_id = get_user_id()
    result = get_user_result(user_id)
    ai_feedback_status = get_user_ai_status(user_id)
    
    # Determine if feedback is available
    has_feedback1 = "AI_Feedback1" in result and result["AI_Feedback1"] and not result["AI_Feedback1"].startswith("Error")
    has_feedback2 = "AI_Feedback2" in result and result["AI_Feedback2"] and not result["AI_Feedback2"].startswith("Error")
    has_comparative = "Comparative_Feedback" in result and result["Comparative_Feedback"] and not result["Comparative_Feedback"].startswith("Error")
    
    return jsonify({
        "status": ai_feedback_status.get("status", "pending"),
        "progress": ai_feedback_status.get("progress", 0),
        "error": ai_feedback_status.get("error", None),
        "ai_feedback1": result.get("AI_Feedback1", "Not available"),
        "ai_feedback2": result.get("AI_Feedback2", "Not available"),
        "comparative_feedback": result.get("Comparative_Feedback", "Not available"),
        "has_feedback1": has_feedback1,
        "has_feedback2": has_feedback2,
        "has_comparative": has_comparative,
        "cache_status": "cached" if any([has_feedback1, has_feedback2, has_comparative]) else "generating"
    })

@app.route("/api/feedback/refresh")
def refresh_feedback():
    """API endpoint to manually refresh AI feedback"""
    user_id = get_user_id()
    ai_feedback_status = get_user_ai_status(user_id)
    
    if ai_feedback_status.get("status") == "generating": 
        return jsonify({"error": "AI feedback is already being generated"}), 400
    
    # Clear any existing feedback to force regeneration
    result = get_user_result(user_id)
    if result:
        result.pop("AI_Feedback1", None)
        result.pop("AI_Feedback2", None)
        result.pop("Comparative_Feedback", None)
    
    # Reset AI status
    if user_id not in user_ai_status:
        user_ai_status[user_id] = {}
    user_ai_status[user_id].update({
        "status": "pending",
        "progress": 0,
        "error": None
    })
    
    # Start new AI feedback generation
    ai_thread = Thread(target=generate_ai_feedback_async, args=(user_id, user_data, user_ai_status))
    ai_thread.daemon = True
    ai_thread.start()
    
    return jsonify({"message": "AI feedback refresh started"})

@app.route("/api/cache/clear")
def clear_ai_cache():
    """API endpoint to clear AI response cache"""
    try:
        clear_cache()
        return jsonify({"message": "AI cache cleared successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to clear cache: {str(e)}"}), 500

@app.route("/api/system/status")
def system_status():
    """API endpoint to get system status"""
    try:
        # Check Ollama connectivity
        from utils.ai_utils import request_ollama
        import os
        
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        test_response = request_ollama("Test", ollama_host)
        ollama_status = "online" if not test_response.startswith("Error") else "offline"
        
        return jsonify({
            "ollama_status": ollama_status,
            "active_users": len(user_data),
            "active_ai_sessions": len(user_ai_status),
            "cache_size": len(getattr(clear_cache, '_cache', {})) if hasattr(clear_cache, '_cache') else 0
        })
    except Exception as e:
        return jsonify({
            "ollama_status": "error",
            "error": str(e),
            "active_users": len(user_data),
            "active_ai_sessions": len(user_ai_status)
        })

# Periodic cleanup task
@app.route("/api/cleanup")
def manual_cleanup():
    """API endpoint to manually trigger cleanup"""
    try:
        cleanup_old_sessions()
        clear_cache()
        return jsonify({"message": "Cleanup completed successfully"})
    except Exception as e:
        return jsonify({"error": f"Cleanup failed: {str(e)}"}), 500

# Initialize AI system when app starts
@app.before_request
def initialize_app():
    """Initialize the application on first request"""
    global first_request
    if not first_request: return
    first_request = False
    
    init_ai_system()

if __name__ == '__main__':
    # Initialize AI system for development
    init_ai_system()
    app.run(debug=True, port=5000, host="0.0.0.0")