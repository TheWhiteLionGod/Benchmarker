import os
import time
import inspect
import requests
import json
from functools import wraps

# Set up Ollama host
os.environ["OLLAMA_HOST"] = "https://4aa8-68-194-75-55.ngrok-free.app/"

def time_function(func):
    """Decorator to automatically time function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper

def get_ai_feedback(func, execution_time, ollama_host="https://4aa8-68-194-75-55.ngrok-free.app/"):
    """
    Get AI feedback on function performance using CodeGemma
    
    Args:
        func: The function to analyze
        execution_time: Execution time in seconds
        ollama_host: Ollama server URL
    
    Returns:
        AI feedback as string
    """
    # Get function source code
    try:
        source_code = inspect.getsource(func)
    except:
        source_code = f"Function name: {func.__name__}\nUnable to retrieve source code"
    
    # Create prompt for CodeGemma
    prompt = f"""
Analyze this Python function for performance and provide constructive feedback:

Function Code:
```python
{source_code}
```

Execution Time: {execution_time:.6f} seconds

Please provide:
1. Performance assessment (fast, average, slow)
2. Potential bottlenecks or inefficiencies
3. Optimization suggestions
4. Code quality observations

Keep the feedback concise and actionable.
"""

    # Send request to Ollama
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

def analyze_function_performance(func, *args, **kwargs):
    """
    Analyze a single function's performance
    
    Args:
        func: Function to analyze
        *args, **kwargs: Arguments to pass to the function
    
    Returns:
        Dictionary with result, execution time, and AI feedback
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    
    feedback = get_ai_feedback(func, execution_time)
    
    return {
        "function_name": func.__name__,
        "result": result,
        "execution_time": execution_time,
        "ai_feedback": feedback
    }

def compare_two_functions(func1, func2, *args, **kwargs):
    """
    Compare performance of two functions that do similar tasks
    
    Args:
        func1: First function to compare
        func2: Second function to compare
        *args, **kwargs: Arguments to pass to both functions
    
    Returns:
        Dictionary with comparison results and AI feedback
    """
    # Analyze first function
    analysis1 = analyze_function_performance(func1, *args, **kwargs)
    
    # Analyze second function
    analysis2 = analyze_function_performance(func2, *args, **kwargs)
    
    # Get comparative feedback
    comparative_prompt = f"""
Compare these two Python functions:

Function 1: {func1.__name__}
Execution Time: {analysis1['execution_time']:.6f} seconds
Code:
```python
{inspect.getsource(func1) if hasattr(func1, '__code__') else 'Source unavailable'}
```

Function 2: {func2.__name__}
Execution Time: {analysis2['execution_time']:.6f} seconds
Code:
```python
{inspect.getsource(func2) if hasattr(func2, '__code__') else 'Source unavailable'}
```

Please provide:
1. Which function performs better and why
2. Performance difference analysis
3. Trade-offs between the approaches
4. Recommendations for when to use each
"""

    try:
        response = requests.post(
            f"{os.environ['OLLAMA_HOST']}/api/generate",
            json={
                "model": "codegemma:instruct",
                "prompt": comparative_prompt,
                "stream": False
            },
            timeout=30
        )
        
        comparative_feedback = response.json()["response"] if response.status_code == 200 else "Error getting comparative feedback"
        
    except Exception as e:
        comparative_feedback = f"Error getting comparative feedback: {str(e)}"
    
    return {
        "function1_analysis": analysis1,
        "function2_analysis": analysis2,
        "comparative_feedback": comparative_feedback,
        "performance_winner": func1.__name__ if analysis1['execution_time'] < analysis2['execution_time'] else func2.__name__,
        "time_difference": abs(analysis1['execution_time'] - analysis2['execution_time'])
    }

# Example usage functions
def example_function_1(n):
    """Example function using list comprehension"""
    return [i**2 for i in range(n)]

def example_function_2(n):
    """Example function using traditional loop"""
    result = []
    for i in range(n):
        result.append(i**2)
    return result

def example_function_3(n):
    """Example function with inefficient nested loops"""
    result = []
    for i in range(n):
        for j in range(10):  # Unnecessary nested loop
            if j == 0:
                result.append(i**2)
    return result

if __name__ == "__main__":
    # Example 1: Analyze single function
    print("=== Single Function Analysis ===")
    analysis = analyze_function_performance(example_function_1, 1000)
    print(f"Function: {analysis['function_name']}")
    print(f"Execution Time: {analysis['execution_time']:.6f} seconds")
    print(f"AI Feedback:\n{analysis['ai_feedback']}\n")
    
    # Example 2: Compare two functions
    print("=== Function Comparison ===")
    comparison = compare_two_functions(example_function_1, example_function_2, 1000)
    print(f"Winner: {comparison['performance_winner']}")
    print(f"Time Difference: {comparison['time_difference']:.6f} seconds")
    print(f"Comparative Feedback:\n{comparison['comparative_feedback']}")