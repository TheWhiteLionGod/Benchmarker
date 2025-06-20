from utils.html_utils import get_html
import os
import requests
from typing import Dict, Any
import concurrent.futures
import threading
import time

# Global cache for AI responses (in-memory session storage)
response_cache = {}
cache_lock = threading.Lock()

# Function to request Ollama for AI feedback with optimizations
def request_ollama(prompt: str, ollama_host: str) -> str:
    # Check cache first
    prompt_hash = hash(prompt)
    with cache_lock:
        if prompt_hash in response_cache:
            return response_cache[prompt_hash]
    
    try:
        # Optimized parameters for faster response
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": "codegemma:instruct",
                "prompt": prompt,
                "stream": False,
                "options": {
                    # Reduce context window for faster processing
                    "num_ctx": 2048,  # Reduced from default 4096
                    "temperature": 0.3,  # Lower temperature for more focused responses
                    "top_p": 0.9,  # Nucleus sampling for efficiency
                    "top_k": 40,  # Limit vocabulary for faster generation
                    "repeat_penalty": 1.1,  # Prevent repetition
                    "num_predict": 400,  # Limit response length for speed
                    # CPU optimization (adjust based on your system)
                    "num_thread": -1,  # Let Ollama auto-detect optimal threads
                    "use_mmap": True,  # Use memory mapping for better performance
                    "use_mlock": True,  # Lock model in memory to avoid swapping
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()["response"]
            # Cache the response
            with cache_lock:
                response_cache[prompt_hash] = result
            return result
        else:
            return f"Error: Failed to get response from Ollama (Status: {response.status_code})"
            
    except requests.RequestException as e:
        return f"Error connecting to Ollama: {str(e)}"

# Optimized AI Feedback with shorter, more focused prompts
def get_ai_feedback(func_code: str, func_name: str, raw_times: list[float], score: float) -> str:
    ollama_host = os.environ.get("OLLAMA_HOST")

    avg_time = sum(raw_times) / len(raw_times)
    
    # Shorter, more focused prompt for faster processing
    prompt = f"""Analyze this Python function performance (keep response under 300 words):

{func_name}:
```python
{func_code}
```

Metrics: Score {score:.2f}, Avg time {avg_time:.4f}s

Provide:
1. Performance assessment
2. Main bottlenecks
3. 2-3 optimization tips
4. Code quality notes

Be concise and actionable."""
    
    return request_ollama(prompt, ollama_host)

# Optimized Comparative Feedback
def get_comparative_feedback(func1_code: str, func2_code: str, func1_times: list[float], func2_times: list[float], func1_score: float, func2_score: float):
    ollama_host = os.environ.get("OLLAMA_HOST")

    avg1 = sum(func1_times) / len(func1_times)
    avg2 = sum(func2_times) / len(func2_times)
    
    better_func = "Function 1" if func1_score > func2_score else "Function 2"
    score_diff = abs(func1_score - func2_score)
    
    # Shorter comparative prompt
    comparative_prompt = f"""Compare these functions (keep under 250 words):

Function 1 (Score: {func1_score:.2f}):
```python
{func1_code}
```

Function 2 (Score: {func2_score:.2f}):
```python  
{func2_code}
```

{better_func} wins by {score_diff:.2f} points.

Provide:
1. Winner and why
2. Key performance differences
3. When to use each
4. Main optimization opportunity

Be concise."""

    return request_ollama(comparative_prompt, ollama_host)

# Parallel AI feedback generation for faster processing
def generate_ai_feedback_async(user_id: str, user_data: Dict[str, Dict[str, Any]], user_ai_status: Dict[str, Dict[str, Any]]):
    """
    Generate AI feedback for a specific user asynchronously with parallel processing
    """
    result = user_data.get(user_id, {})
    ai_feedback_status = user_ai_status.get(user_id, {})
    
    if not result or not ai_feedback_status:
        print(f"Warning: No data found for user {user_id}")
        return
    
    try:
        ai_feedback_status["status"] = "generating"
        ai_feedback_status["progress"] = 0

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all three feedback requests concurrently
            future_feedback1 = executor.submit(
                get_ai_feedback,
                result["Program1Code"], 
                "Function 1", 
                result["Func1Times"], 
                result["Func1Score"]
            )
            
            future_feedback2 = executor.submit(
                get_ai_feedback,
                result["Program2Code"], 
                "Function 2", 
                result["Func2Times"], 
                result["Func2Score"]
            )
            
            future_comparative = executor.submit(
                get_comparative_feedback,
                result["Program1Code"], 
                result["Program2Code"], 
                result["Func1Times"], 
                result["Func2Times"], 
                result["Func1Score"], 
                result["Func2Score"]
            )
            
            # Update progress as tasks complete
            ai_feedback_status["progress"] = 10
            
            # Wait for all tasks to complete with timeout
            try:
                # Get results with timeout
                result["AI_Feedback1"] = get_html(future_feedback1.result(timeout=50))
                ai_feedback_status["progress"] = 40
                
                result["AI_Feedback2"] = get_html(future_feedback2.result(timeout=50))
                ai_feedback_status["progress"] = 70
                
                result["Comparative_Feedback"] = get_html(future_comparative.result(timeout=50))
                ai_feedback_status["progress"] = 100
                
            except concurrent.futures.TimeoutError:
                # Handle timeout gracefully
                ai_feedback_status["status"] = "error"
                ai_feedback_status["error"] = "AI feedback generation timed out"
                
                # Set fallback messages for any that didn't complete
                if "AI_Feedback1" not in result:
                    result["AI_Feedback1"] = "AI feedback timed out. Please try refreshing."
                if "AI_Feedback2" not in result:
                    result["AI_Feedback2"] = "AI feedback timed out. Please try refreshing."
                if "Comparative_Feedback" not in result:
                    result["Comparative_Feedback"] = "Comparative feedback timed out. Please try refreshing."
                return

        ai_feedback_status["status"] = "complete"
        print(f"AI feedback generation complete for user {user_id}!")

    except Exception as e:
        print(f"Error generating AI feedback for user {user_id}: {str(e)}")
        ai_feedback_status["status"] = "error"
        ai_feedback_status["error"] = str(e)
        result["AI_Feedback1"] = f"Error generating feedback: {str(e)}"
        result["AI_Feedback2"] = f"Error generating feedback: {str(e)}"
        result["Comparative_Feedback"] = f"Error generating feedback: {str(e)}"

# Function to clear cache periodically (call this in your cleanup routine)
def clear_cache():
    """Clear the response cache to free memory"""
    with cache_lock:
        response_cache.clear()
    print("AI response cache cleared")

# Function to warm up Ollama (call this during app startup)
def warmup_ollama():
    """Send a simple request to warm up Ollama"""
    ollama_host = os.environ.get("OLLAMA_HOST")
    try:
        warmup_prompt = "Hello, this is a warmup request."
        result = request_ollama(warmup_prompt, ollama_host)
        print(f"Ollama warmup completed\nResponse: {result}")
    except Exception as e:
        print(f"Ollama warmup failed: {e}")