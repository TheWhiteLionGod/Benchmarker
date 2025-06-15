import os
import requests
import re
from typing import Dict, Any

os.environ["OLLAMA_HOST"] = "http://localhost:11434"

def analyze_function_parameters(func1_code: str, func2_code: str) -> Dict[str, Any]:
    """Analyze function signatures to determine parameter types"""
    # Extract function signatures
    func1_sig = re.search(r'def\s+\w+\s*\(([^)]*)\)', func1_code)
    func2_sig = re.search(r'def\s+\w+\s*\(([^)]*)\)', func2_code)
    
    func1_params = func1_sig.group(1).split(',') if func1_sig else []
    func2_params = func2_sig.group(1).split(',') if func2_sig else []
    
    # Clean parameter names
    func1_params = [p.strip() for p in func1_params if p.strip()]
    func2_params = [p.strip() for p in func2_params if p.strip()]
    
    # Analyze function content for patterns
    is_search_function = any(keyword in (func1_code + func2_code).lower() 
                           for keyword in ['search', 'find', 'index', 'target', 'arr', 'array'])
    
    is_math_function = any(keyword in (func1_code + func2_code).lower() 
                          for keyword in ['math', 'calculate', 'sum', 'multiply', 'divide'])
    
    is_string_function = any(keyword in (func1_code + func2_code).lower() 
                            for keyword in ['string', 'str', 'text', 'char'])
    
    return {
        'func1_params': func1_params,
        'func2_params': func2_params,
        'param_count': max(len(func1_params), len(func2_params)),
        'is_search': is_search_function,
        'is_math': is_math_function,
        'is_string': is_string_function
    }

def generate_smart_fallback_params(func_info: Dict[str, Any]) -> str:
    """Generate smart fallback parameters based on function analysis"""
    param_count = func_info['param_count']
    
    if func_info['is_search'] and param_count == 2:
        # Search function with array and target
        return """(list(range(1, 1000001)), 999999), (list(range(1, 1000001)), 876543), (list(range(1, 1000001)), 567890), (list(range(1, 1000001)), 500000), (list(range(1, 1000001)), 432100), (list(range(1, 1000001)), 250000), (list(range(1, 1000001)), 123456), (list(range(1, 1000001)), 10001), (list(range(1, 1000001)), 1), (list(range(1, 1000001)), -1)"""
    
    elif func_info['is_math'] and param_count == 2:
        # Math function with two numbers
        return """(1000000, 999999), (500000, 400000), (100000, 90000), (50000, 40000), (10000, 9000), (5000, 4000), (1000, 900), (100, 90), (10, 9), (1, 1)"""
    
    elif func_info['is_string'] and param_count == 2:
        # String function
        return """('a' * 1000000, 'z'), ('b' * 500000, 'y'), ('c' * 100000, 'x'), ('d' * 50000, 'w'), ('e' * 10000, 'v'), ('f' * 5000, 'u'), ('g' * 1000, 't'), ('h' * 500, 's'), ('i' * 100, 'r'), ('j' * 10, 'q')"""
    
    elif param_count == 1:
        # Single parameter function
        return """(list(range(1000000))), (list(range(500000))), (list(range(100000))), (list(range(50000))), (list(range(10000))), (list(range(5000))), (list(range(1000))), (list(range(500))), (list(range(100))), (list(range(10)))"""
    
    elif param_count == 3:
        # Three parameter function
        return """(list(range(100000)), 50000, 75000), (list(range(50000)), 25000, 37500), (list(range(10000)), 5000, 7500), (list(range(5000)), 2500, 3750), (list(range(1000)), 500, 750), (list(range(500)), 250, 375), (list(range(100)), 50, 75), (list(range(50)), 25, 37), (list(range(10)), 5, 7), (list(range(5)), 2, 3)"""
    
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
    Format these two Python functions properly with correct indentation and spacing.
    Also fix any small syntax errors if present.
    
    Function 1:
    {func1_code}
    
    Function 2:
    {func2_code}
    
    Return only the properly formatted functions with correct syntax, nothing else. No comments or explanations.
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
    
    Return ONLY the parameters list in this exact format with NO comments or explanations:
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
    
    # Extract formatted functions and clean them
    functions = re.findall(r'def\s+\w+.*?(?=def\s+\w+|$)', formatted_response, re.DOTALL)
    
    if len(functions) >= 2:
        formatted_func1 = functions[0].strip()
        formatted_func2 = functions[1].strip()
    else:
        # Fallback formatting - just clean up the original
        formatted_func1 = func1_code.strip()
        formatted_func2 = func2_code.strip()
    
    # Remove any comments from formatted functions
    formatted_func1 = re.sub(r'#.*', '', formatted_func1)
    formatted_func2 = re.sub(r'#.*', '', formatted_func2)
    
    # Clean up extra whitespace
    formatted_func1 = re.sub(r'\n\s*\n', '\n', formatted_func1)
    formatted_func2 = re.sub(r'\n\s*\n', '\n', formatted_func2)
    
    # Extract or generate function calls
    func1_call = f"result = {func1_name}(params[i][0], params[i][1])"
    func2_call = f"result = {func2_name}(params[i][0], params[i][1])"
    
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