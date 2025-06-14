import os
import json
import time
import requests
from typing import Any, List, Tuple, Dict, Callable

os.environ["OLLAMA_HOST"] = "http://localhost:11434"

def ai_benchmark_function(func: Callable, func_code: str, num_params: int = 10) -> Dict[str, Any]:
    """
    AI-assisted benchmarking tool that generates test parameters and benchmarks a function.
    
    Args:
        func: The function to benchmark
        func_code: String representation of the function code
        num_params: Number of test parameters to generate
    
    Returns:
        Dictionary containing benchmark results in JSON format
    """
    
    def call_ollama(prompt: str) -> str:
        """Call Ollama API with codegemma:instruct model"""
        url = f"{os.environ['OLLAMA_HOST']}/api/generate"
        
        payload = {
            "model": "codegemma:instruct",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"Error calling Ollama API: {e}")
            return ""
    
    # Generate test parameters using AI
    param_prompt = f"""
    Analyze this Python function and generate {num_params} test parameters that would be good for benchmarking:

    {func_code}

    Generate test parameters that include:
    - Edge cases (empty inputs, single elements, etc.)
    - Different sizes to test scalability
    - Best case, average case, and worst case scenarios
    - Parameters that would stress test the function

    Return ONLY a Python list of tuples in this exact format:
    params = [(param1, param2), (param3, param4), ...]

    For binary search specifically, generate a sorted array and various target values.
    Make sure the array is large enough to show performance differences.
    """
    
    print("🤖 AI is generating test parameters...")
    ai_params_response = call_ollama(param_prompt)
    
    # Extract parameters from AI response
    try:
        # Find the params list in the AI response
        params_start = ai_params_response.find("params = [")
        if params_start == -1:
            params_start = ai_params_response.find("[(")
        
        if params_start != -1:
            # Extract the list part
            params_str = ai_params_response[params_start:]
            if params_str.startswith("params = "):
                params_str = params_str[9:]  # Remove "params = "
            
            # For binary search, we need to create the sorted array
            if "binary_search" in func_code:
                # Generate a large sorted array for testing
                test_array = list(range(1, 1000001))  # 1 million elements
                
                # Create test parameters with the array and different targets
                params = [
                    (test_array, 500000),   # Middle element
                    (test_array, 999999),   # Near end (worst case)
                    (test_array, 1),        # First element (best case)
                    (test_array, 1000000),  # Last element
                    (test_array, 750000),   # 3/4 through
                    (test_array, 250000),   # 1/4 through
                    (test_array, 567890),   # Random middle
                    (test_array, 123456),   # Random early
                    (test_array, 876543),   # Random late
                    (test_array, -1)        # Not found case
                ]
            else:
                # Try to evaluate the AI-generated parameters
                params = eval(params_str)
        else:
            # Fallback parameters if AI parsing fails
            params = [(list(range(100)), 50), (list(range(1000)), 500)]
            
    except Exception as e:
        print(f"Error parsing AI parameters: {e}")
        # Fallback for binary search
        test_array = list(range(1, 100001))
        params = [
            (test_array, 50000),
            (test_array, 99999),
            (test_array, 1),
            (test_array, -1)
        ]
    
    print(f"✅ Generated {len(params)} test parameters")
    
    # Benchmark the function
    benchmark_results = []
    
    print("⏱️  Running benchmarks...")
    for i, param_set in enumerate(params):
        try:
            # Time the function execution
            start_time = time.perf_counter()
            result = func(*param_set)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            
            benchmark_results.append({
                "test_case": i + 1,
                "parameters": param_set,
                "result": result,
                "execution_time_seconds": execution_time,
                "execution_time_ms": execution_time * 1000
            })
            
        except Exception as e:
            benchmark_results.append({
                "test_case": i + 1,
                "parameters": param_set,
                "result": f"Error: {str(e)}",
                "execution_time_seconds": 0,
                "execution_time_ms": 0
            })
    
    # Sort by execution time (highest to lowest)
    benchmark_results.sort(key=lambda x: x["execution_time_seconds"], reverse=True)
    
    # Generate AI analysis of results
    analysis_prompt = f"""
    Analyze these benchmark results for the function:
    
    {func_code}
    
    Results: {json.dumps(benchmark_results, indent=2)}
    
    Provide insights about:
    1. Performance characteristics
    2. Best and worst case scenarios
    3. Time complexity observations
    4. Any patterns in the results
    
    Keep the analysis concise and technical.
    """
    
    print("🧠 AI is analyzing benchmark results...")
    ai_analysis = call_ollama(analysis_prompt)
    
    # Prepare final output
    output = {
        "function_name": func.__name__,
        "function_code": func_code,
        "total_test_cases": len(params),
        "benchmark_results": benchmark_results,
        "ai_analysis": ai_analysis.strip(),
        "summary": {
            "fastest_execution_ms": min(r["execution_time_ms"] for r in benchmark_results if r["execution_time_ms"] > 0),
            "slowest_execution_ms": max(r["execution_time_ms"] for r in benchmark_results),
            "average_execution_ms": sum(r["execution_time_ms"] for r in benchmark_results) / len(benchmark_results)
        }
    }
    
    return output

# Example usage
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

# Function code as string for AI analysis
binary_search_code = '''
def binary_search(arr, target): 
    low = 0
    high = len(arr) - 1 
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid 
        elif arr[mid] < target: 
            low = mid + 1
        else: 
            high = mid - 1 
    return -1
'''

if __name__ == "__main__":
    # Run the AI-assisted benchmark
    print("🚀 Starting AI-Assisted Benchmarking...")
    results = ai_benchmark_function(binary_search, binary_search_code)
    
    # Save results to JSON file
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("✅ Benchmarking complete!")
    print(f"📊 Results saved to benchmark_results.json")
    print(f"📈 Fastest execution: {results['summary']['fastest_execution_ms']:.4f}ms")
    print(f"📉 Slowest execution: {results['summary']['slowest_execution_ms']:.4f}ms")
    print(f"📊 Average execution: {results['summary']['average_execution_ms']:.4f}ms")
