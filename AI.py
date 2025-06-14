import os
import requests
import re
from typing import Dict, Any

os.environ["OLLAMA_HOST"] = "http://localhost:11434"

def generate_benchmark_params(func_code: str) -> Dict[str, Any]:
    """
    Generate test parameters and function call using AI for benchmarking.
    
    Args:
        func_code: String representation of the function code
    
    Returns:
        Dictionary with function code, parameters, and function call
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
    
    # AI prompt to generate parameters and function call
    prompt = f"""
    Analyze this Python function and generate:
    1. Good test parameters for benchmarking (10 different test cases)
    2. A function call line using the parameters

    Function:
    {func_code}

    Generate parameters that test different scenarios:
    - Edge cases
    - Different input sizes
    - Best, average, and worst case scenarios
    - Parameters sorted from most time-consuming to least

    For binary search, use a large sorted array (like range(1, 1000001)) with different target values.
    No comments bro pls pls pls pls pls pls pls
    also make sure you dont haave enters slash breaks in your code pls like dont do
    \n

    Output format:
    params = [(param1, param2), (param3, param4), ...]
    result = function_name(params[i][0], params[i][1])

    Only output the params list and the result line, nothing else.
    """
    
    print("🤖 AI is generating parameters...")
    ai_response = call_ollama(prompt)
    
    # Extract function name from the code
    func_name_match = re.search(r'def\s+(\w+)\s*\(', func_code)
    func_name = func_name_match.group(1) if func_name_match else "unknown_function"
    
    # Parse AI response to extract params and result line
    params_match = re.search(r'params\s*=\s*\[(.*?)\]', ai_response, re.DOTALL)
    result_match = re.search(r'result\s*=\s*(.+)', ai_response)
    
    if not params_match:
        # Fallback for binary search if AI parsing fails
        if "binary_search" in func_code:
            params_str = """
            (list(range(1, 1000001)), 500000),
            (list(range(1, 1000001)), 999999),
            (list(range(1, 1000001)), 1),
            (list(range(1, 1000001)), 1000000),
            (list(range(1, 1000001)), 750000),
            (list(range(1, 1000001)), 250000),
            (list(range(1, 1000001)), 567890),
            (list(range(1, 1000001)), 123456),
            (list(range(1, 1000001)), 876543),
            (list(range(1, 1000001)), -1)
            """
        else:
            params_str = "([], 0), ([1], 1), ([1,2,3], 2)"
    else:
        params_str = params_match.group(1)
    
    if not result_match:
        result_line = f"result = {func_name}(params[i][0], params[i][1])"
    else:
        result_line = result_match.group(0)
    
    # Create the output dictionary
    output = {
        "Func1": func_code.strip(),
        "Func2": "",  # Empty as requested
        "Params": f"[{params_str}]",
        "FunctionCall": result_line
    }
    
    return output

# Example usage
if __name__ == "__main__":
    binary_search_code = """def binary_search(arr, target): 
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
    return -1"""
    
    result = generate_benchmark_params(binary_search_code)
    print("\n📋 Generated benchmark setup:")
    print(result)