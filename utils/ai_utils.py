from utils.html_utils import get_html
import os
import requests
from typing import Dict, Any

# Function to request Ollama for AI feedback
def request_ollama(prompt: str, ollama_host: str) -> str:
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

# Getting AI Feedback of Function Code
def get_ai_feedback(func_code: str, func_name: str, raw_times: list[float], score: float) -> str:
    ollama_host = os.environ.get("OLLAMA_HOST")

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
    
    # Request Ollama for feedback
    return request_ollama(prompt, ollama_host)


# Comparative Feedback
def get_comparative_feedback(func1_code: str, func2_code: str, func1_times: list[float], func2_times: list[float], func1_score: float, func2_score: float):
    ollama_host = os.environ.get("OLLAMA_HOST")

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

    # Request Ollama for comparative feedback
    return request_ollama(comparative_prompt, ollama_host)

# Generating Ai Feedback Asyncronously so Page Loads Quicker without Feedback
def generate_ai_feedback_async(user_id: str, user_data: Dict[str, Dict[str, Any]], user_ai_status: Dict[str, Dict[str, Any]]):
    """
    Generate AI feedback for a specific user asynchronously
    
    Args:
        user_id: Unique identifier for the user
        user_data: Dictionary containing all user data
        user_ai_status: Dictionary containing all user AI status data
    """
    # Get user-specific data
    result = user_data.get(user_id, {})
    ai_feedback_status = user_ai_status.get(user_id, {})
    
    # Safety check - ensure user data exists
    if not result or not ai_feedback_status:
        print(f"Warning: No data found for user {user_id}")
        return
    
    try:
        ai_feedback_status["status"] = "generating"
        ai_feedback_status["progress"] = 10

        # Get AI feedback for function 1
        print(f"Getting AI feedback for Function 1 (user: {user_id})...")
        result["AI_Feedback1"] = get_ai_feedback(
            result["Program1Code"], 
            "Function 1", 
            result["Func1Times"], 
            result["Func1Score"]
        )
        result["AI_Feedback1"] = get_html(result.get("AI_Feedback1", "AI feedback not available"))
        ai_feedback_status["progress"] = 40
        
        # Get AI feedback for function 2
        print(f"Getting AI feedback for Function 2 (user: {user_id})...")
        result["AI_Feedback2"] = get_ai_feedback(
            result["Program2Code"], 
            "Function 2", 
            result["Func2Times"], 
            result["Func2Score"]
        )
        result["AI_Feedback2"] = get_html(result["AI_Feedback2"])
        ai_feedback_status["progress"] = 70
        
        # Get comparative feedback
        print(f"Getting comparative feedback (user: {user_id})...")
        result["Comparative_Feedback"] = get_comparative_feedback(
            result["Program1Code"], 
            result["Program2Code"], 
            result["Func1Times"], 
            result["Func2Times"], 
            result["Func1Score"], 
            result["Func2Score"]
        )
        result["Comparative_Feedback"] = get_html(result["Comparative_Feedback"])
        
        ai_feedback_status["progress"] = 100
        ai_feedback_status["status"] = "complete"
        print(f"AI feedback generation complete for user {user_id}!")

    except Exception as e:
        print(f"Error generating AI feedback for user {user_id}: {str(e)}")
        ai_feedback_status["status"] = "error"
        ai_feedback_status["error"] = str(e)
        result["AI_Feedback1"] = f"Error generating feedback: {str(e)}"
        result["AI_Feedback2"] = f"Error generating feedback: {str(e)}"
        result["Comparative_Feedback"] = f"Error generating feedback: {str(e)}"