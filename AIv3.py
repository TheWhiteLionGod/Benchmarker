import os
import requests
import re
from typing import Dict, Any

os.environ["OLLAMA_HOST"] = "https://4aa8-68-194-75-55.ngrok-free.app/"

def generate_dual_function_benchmark(func1_code: str, func2_code: str) -> Dict[str, Any]:
    """
    Generate formatted functions, parameters, and function calls for benchmarking two functions.
    
    Args:
        func1_code: String representation of the first function
        func2_code: String representation of the second function
    
    Returns:
        Dictionary with both formatted functions, parameters, and function calls
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
    
    # Format functions properly
    format_prompt = f"""
    Format these two Python functions properly with correct indentation and spacing:
    
    Function 1:
    {func1_code}
    
    Function 2:
    {func2_code}
    
    Return only the properly formatted functions, nothing else.
    """
    
    print("🤖 AI is formatting functions...")
    formatted_response = call_ollama(format_prompt)
    
    # Generate parameters
    params_prompt = f"""
    Analyze these two Python functions and generate 10 test parameters for benchmarking.
    
    Function 1:
    {func1_code}
    
    Function 2:
    {func2_code}
    
    Generate parameters that will test both functions with the same inputs:
    - Use a large sorted array (like list(range(1, 1000001))) for comprehensive testing
    - Include different target values that test various scenarios
    - Order parameters from most time-consuming to least time-consuming
    - Focus on testing search performance with different positions and edge cases
    
    Return ONLY in this exact format:
    params = [(arr, target1), (arr, target2), (arr, target3), ...]
    
    Where arr should be a large sorted array and targets should be strategically chosen.
    """
    
    print("🤖 AI is generating parameters...")
    params_response = call_ollama(params_prompt)
    
    # Generate function calls
    func1_name = re.search(r'def\s+(\w+)\s*\(', func1_code)
    func2_name = re.search(r'def\s+(\w+)\s*\(', func2_code)
    
    func1_name = func1_name.group(1) if func1_name else "function1"
    func2_name = func2_name.group(1) if func2_name else "function2"
    
    calls_prompt = f"""
    Create function call code for these two functions:
    
    Function 1: {func1_name}
    Function 2: {func2_name}
    
    Generate code that:
    1. Unpacks parameters from params list
    2. Calls each function with the unpacked parameters
    
    Format like this:
    arr, target = params[i]
    result = function_name(arr, target)
    
    Generate this for both functions.
    """
    
    print("🤖 AI is generating function calls...")
    calls_response = call_ollama(calls_prompt)
    
    # Extract parameters from AI response
    params_match = re.search(r'params\s*=\s*\[(.*?)\]', params_response, re.DOTALL)
    
    if not params_match:
        # Fallback parameters ordered from most to least time consuming
        params_str = """(list(range(1, 1000001)), 999999),
        (list(range(1, 1000001)), 876543),
        (list(range(1, 1000001)), 567890),
        (list(range(1, 1000001)), 500000),
        (list(range(1, 1000001)), 432100),
        (list(range(1, 1000001)), 250000),
        (list(range(1, 1000001)), 123456),
        (list(range(1, 1000001)), 10001),
        (list(range(1, 1000001)), 1000000),
        (list(range(1, 1000001)), 1),
        (list(range(1, 1000001)), -1)"""
    else:
        params_str = params_match.group(1)
    
    # Extract formatted functions
    functions = re.findall(r'def\s+\w+.*?(?=def\s+\w+|$)', formatted_response, re.DOTALL)
    
    if len(functions) >= 2:
        formatted_func1 = functions[0].strip()
        formatted_func2 = functions[1].strip()
    else:
        # Fallback formatting
        formatted_func1 = func1_code.strip()
        formatted_func2 = func2_code.strip()
    
    # Extract or generate function calls
    call_lines = re.findall(r'result\s*=\s*.+', calls_response)
    
    if len(call_lines) >= 2:
        func1_call = call_lines[0]
        func2_call = call_lines[1]
    else:
        # Generate function calls
        func1_call = f"arr, target = params[i]\nresult = {func1_name}(arr, target)"
        func2_call = f"arr, target = params[i]\nresult = {func2_name}(arr, target)"
    
    # Create the output dictionary
    output = {
        "Func1": formatted_func1,
        "Func2": formatted_func2,
        "Params": f"[{params_str}]",
        "Func1Call": func1_call,
        "Func2Call": func2_call
    }
    
    return output

# Example usage
if __name__ == "__main__":
    func1 = "def binary_search(arr, target): low = 0 high = len(arr) - 1 while low <= high: mid = (low + high) // 2 if arr[mid] == target: return mid elif arr[mid] < target: low = mid + 1 else: high = mid - 1 return -1"
    
    func2 = "def normal_search(arr, target): for v in arr: if v == target: return arr.index(v) return -1"
    
    result = generate_dual_function_benchmark(func1, func2)
    
    print("\n📋 Generated benchmark setup:")
    print("="*50)
    print("Function 1:")
    print(result["Func1"])
    print("\nFunction 2:")
    print(result["Func2"])
    print("\nParameters:")
    print(result["Params"])
    print("\nFunction 1 Call:")
    print(result["Func1Call"])
    print("\nFunction 2 Call:")
    print(result["Func2Call"])