import os
import requests
import re
from typing import Dict, Any, List, Tuple
import random

os.environ["OLLAMA_HOST"] = "http://localhost:11434"

def analyze_function_parameters(func1_code: str, func2_code: str) -> Dict[str, Any]:
    """Analyze function signatures to determine parameter types"""
    # Extract function signatures
    func1_sig = re.search(r'def\s+\w+\s*\(([^)]*)\)', func1_code)
    func2_sig = re.search(r'def\s+\w+\s*\(([^)]*)\)', func2_code)
    
    func1_params = func1_sig.group(1).split(',') if func1_sig else []
    func2_params = func2_sig.group(1).split(',') if func2_sig else []
    
    # Clean parameter names
    func1_params = [p.strip().split(':')[0].strip() for p in func1_params if p.strip()]
    func2_params = [p.strip().split(':')[0].strip() for p in func2_params if p.strip()]
    
    # Remove 'self' if present
    func1_params = [p for p in func1_params if p != 'self']
    func2_params = [p for p in func2_params if p != 'self']
    
    # Analyze function content for patterns
    combined_code = (func1_code + func2_code).lower()
    
    is_search_function = any(keyword in combined_code 
                           for keyword in ['search', 'find', 'index', 'target', 'arr', 'array'])
    
    is_math_function = any(keyword in combined_code 
                          for keyword in ['math', 'calculate', 'sum', 'multiply', 'divide', 'add', 'subtract'])
    
    is_string_function = any(keyword in combined_code 
                            for keyword in ['string', 'str', 'text', 'char', 'substring', 'pattern'])
    
    is_sorting_function = any(keyword in combined_code 
                             for keyword in ['sort', 'order', 'merge', 'quick', 'bubble', 'heap'])
    
    return {
        'func1_params': func1_params,
        'func2_params': func2_params,
        'param_count': max(len(func1_params), len(func2_params)),
        'is_search': is_search_function,
        'is_math': is_math_function,
        'is_string': is_string_function,
        'is_sorting': is_sorting_function
    }

def generate_comprehensive_fallback_params(func_info: Dict[str, Any], count: int = 50) -> List[str]:
    """Generate comprehensive fallback parameters based on function analysis"""
    param_count = func_info['param_count']
    params = []
    
    if func_info['is_search'] and param_count == 2:
        # Search function with array and target - generate varied test cases
        base_sizes = [1000000, 500000, 100000, 50000, 10000, 5000, 1000, 500, 100, 50]
        
        for i, size in enumerate(base_sizes * 5):  # Repeat to get 50 params
            if len(params) >= count:
                break
                
            # Create different target scenarios
            scenarios = [
                f"(list(range(1, {size + 1})), {size})",  # Last element
                f"(list(range(1, {size + 1})), 1)",       # First element
                f"(list(range(1, {size + 1})), {size // 2})",  # Middle element
                f"(list(range(1, {size + 1})), {size // 4})",  # Quarter element
                f"(list(range(1, {size + 1})), {3 * size // 4})",  # Three-quarter element
                f"(list(range(1, {size + 1})), -1)",     # Not found
                f"(list(range(1, {size + 1})), {size + 100})",  # Beyond range
                f"(list(range(1, {size + 1})), {random.randint(1, size)})",  # Random
            ]
            
            # Add scenarios cyclically
            for scenario in scenarios:
                if len(params) < count:
                    params.append(scenario)
    
    elif func_info['is_math'] and param_count == 2:
        # Math function with two numbers
        sizes = list(range(1000000, 1000, -20000)) + list(range(1000, 10, -20))
        for i, size in enumerate(sizes):
            if len(params) >= count:
                break
            params.append(f"({size}, {size - random.randint(1, size // 10)})")
    
    elif func_info['is_string'] and param_count == 2:
        # String function
        sizes = [1000000, 500000, 100000, 50000, 10000, 5000, 1000, 500, 100, 50]
        chars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        targets = ['z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q']
        
        for i in range(count):
            size = sizes[i % len(sizes)]
            char = chars[i % len(chars)]
            target = targets[i % len(targets)]
            params.append(f"('{char}' * {size}, '{target}')")
    
    elif func_info['is_sorting'] and param_count == 1:
        # Sorting function with single array parameter
        for i in range(count):
            if i < 10:
                size = 100000 - i * 10000
                params.append(f"(list(range({size}, 0, -1)))")  # Reverse sorted
            elif i < 20:
                size = 50000 - (i - 10) * 5000
                params.append(f"([random.randint(1, 1000) for _ in range({size})])")  # Random
            elif i < 30:
                size = 20000 - (i - 20) * 2000
                params.append(f"(list(range({size})))")  # Already sorted
            else:
                size = 1000 - (i - 30) * 50
                params.append(f"([1] * {size})")  # All same elements
    
    elif param_count == 1:
        # Single parameter function - assume array/list
        sizes = list(range(1000000, 1000, -20000)) + list(range(1000, 10, -20))
        for i, size in enumerate(sizes[:count]):
            params.append(f"(list(range({size})))")
    
    elif param_count == 3:
        # Three parameter function
        for i in range(count):
            size = max(100000 - i * 2000, 100)
            params.append(f"(list(range({size})), {size // 4}, {3 * size // 4})")
    
    else:
        # Generic fallback for unknown parameter patterns
        for i in range(count):
            size = max(100000 - i * 2000, 100)
            if param_count == 2:
                params.append(f"({size}, {size // 2})")
            else:
                param_list = ", ".join([str(size // (j + 1)) for j in range(param_count)])
                params.append(f"({param_list})")
    
    return params[:count]

def parse_ai_parameters(response: str) -> List[str]:
    """Parse parameters from AI response with multiple fallback strategies"""
    params = []
    
    # Strategy 1: Look for params = [...]
    params_match = re.search(r'params\s*=\s*\[(.*?)\]', response, re.DOTALL)
    if params_match:
        content = params_match.group(1)
        # Split by ), ( pattern to separate tuples
        tuples = re.findall(r'\([^)]+\)', content)
        params = tuples
    
    # Strategy 2: Look for just [...] 
    if not params:
        bracket_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
        if bracket_match:
            content = bracket_match.group(1)
            tuples = re.findall(r'\([^)]+\)', content)
            params = tuples
    
    # Strategy 3: Look for individual tuples in the text
    if not params:
        tuples = re.findall(r'\([^)]+\)', response)
        params = tuples
    
    # Clean up the parameters
    cleaned_params = []
    for param in params:
        # Remove extra whitespace and ensure proper formatting
        clean_param = re.sub(r'\s+', ' ', param.strip())
        if clean_param and clean_param.startswith('(') and clean_param.endswith(')'):
            cleaned_params.append(clean_param)
    
    return cleaned_params

def generate_dual_function_benchmark(func1_code: str, func2_code: str, param_count: int = 50) -> Dict[str, Any]:
    """
    Generate formatted functions, parameters, and function calls for benchmarking two functions.
    
    Args:
        func1_code: String representation of the first function
        func2_code: String representation of the second function
        param_count: Number of parameters to generate (default: 50)
    
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
                "temperature": 0.3,  # Lower temperature for more consistent output
                "top_p": 0.8
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"Error calling Ollama API: {e}")
            return ""
    
    # Analyze functions first
    func_info = analyze_function_parameters(func1_code, func2_code)
    print(f"📊 Analysis: {func_info['param_count']} params, Search: {func_info['is_search']}, Math: {func_info['is_math']}, String: {func_info['is_string']}")
    
    # Format functions properly
    format_prompt = f"""
    Format these two Python functions properly with correct indentation and spacing.
    Fix any syntax errors and ensure they are complete, valid Python functions.
    
    Function 1:
    {func1_code}
    
    Function 2:
    {func2_code}
    
    Return only the properly formatted functions with correct syntax. No explanations or comments.
    """
    
    print("🤖 AI is formatting functions...")
    formatted_response = call_ollama(format_prompt)
    
    # Generate parameters with more specific prompt
    params_prompt = f"""
    Generate exactly {param_count} test parameters for benchmarking these Python functions.
    
    Function 1:
    {func1_code}
    
    Function 2:
    {func2_code}
    
    Requirements:
    - Generate exactly {param_count} parameter sets
    - Order from most computationally expensive to least expensive
    - Use realistic data sizes for performance testing
    - For search functions: use large sorted arrays with varied target positions
    - For math functions: use large numbers that test computational limits
    - For string functions: use long strings with different patterns
    
    Format: Return ONLY a Python list like this:
    [(param1, param2), (param1, param2), ...]
    
    No explanations, just the parameter list.
    """
    
    print(f"🤖 AI is generating {param_count} parameters...")
    params_response = call_ollama(params_prompt)
    
    # Try to parse AI parameters
    ai_params = parse_ai_parameters(params_response)
    
    # Generate fallback parameters
    fallback_params = generate_comprehensive_fallback_params(func_info, param_count)
    
    # Use AI parameters if we got enough, otherwise use fallback
    if len(ai_params) >= param_count // 2:  # If we got at least half from AI
        print(f"✅ Using {len(ai_params)} AI-generated parameters")
        final_params = ai_params[:param_count]
    else:
        print(f"⚠️ AI generated only {len(ai_params)} parameters, using smart fallback")
        final_params = fallback_params
    
    # Ensure we have exactly the requested count
    while len(final_params) < param_count:
        # Duplicate and modify existing params if needed
        base_param = final_params[len(final_params) % len(final_params)]
        final_params.append(base_param)
    
    final_params = final_params[:param_count]  # Trim to exact count
    
    # Generate function calls
    func1_name = re.search(r'def\s+(\w+)\s*\(', func1_code)
    func2_name = re.search(r'def\s+(\w+)\s*\(', func2_code)
    
    func1_name = func1_name.group(1) if func1_name else "function1"
    func2_name = func2_name.group(1) if func2_name else "function2"
    
    # Extract formatted functions
    functions = re.findall(r'def\s+\w+.*?(?=def\s+\w+|$)', formatted_response, re.DOTALL)
    
    if len(functions) >= 2:
        formatted_func1 = functions[0].strip()
        formatted_func2 = functions[1].strip()
    else:
        # Fallback formatting
        formatted_func1 = func1_code.strip()
        formatted_func2 = func2_code.strip()
    
    # Clean up formatted functions
    for func in [formatted_func1, formatted_func2]:
        func = re.sub(r'#.*', '', func)  # Remove comments
        func = re.sub(r'```.*?```', '', func, flags=re.DOTALL)  # Remove code blocks
        func = re.sub(r'```.*', '', func)
        func = re.sub(r'\n\s*\n', '\n', func).strip()  # Clean whitespace
    
    # Create parameter string
    params_str = ',\n        '.join(final_params)
    
    # Generate function calls based on parameter count
    param_access = ', '.join([f"params[i][{j}]" for j in range(func_info['param_count'])])
    func1_call = f"result = {func1_name}({param_access})"
    func2_call = f"result = {func2_name}({param_access})"
    
    # Create the output dictionary
    output = {
        "Func1": formatted_func1,
        "Func2": formatted_func2,
        "Params": f"[\n        {params_str}\n    ]",
        "Func1Call": func1_call,
        "Func2Call": func2_call,
        "ParamCount": len(final_params),
        "Analysis": func_info
    }
    
    return output

# Example usage
if __name__ == "__main__":
    func1 = "def binary_search(arr, target): low = 0 high = len(arr) - 1 while low <= high: mid = (low + high) // 2 if arr[mid] == target: return mid elif arr[mid] < target: low = mid + 1 else: high = mid - 1 return -1"
    
    func2 = "def normal_search(arr, target): for v in arr: if v == target: return arr.index(v) return -1"
    
    result = generate_dual_function_benchmark(func1, func2, param_count=50)
    
    print("\n📋 Generated benchmark setup:")
    print("="*60)
    print(f"Generated {result['ParamCount']} parameters")
    print(f"Function analysis: {result['Analysis']}")
    print("\nFunction 1:")
    print(result["Func1"])
    print("\nFunction 2:")
    print(result["Func2"])
    print("\nParameters (showing first 5):")
    params_preview = result["Params"].split(',')[:5]
    print(','.join(params_preview) + "...")
    print(f"\nFunction 1 Call: {result['Func1Call']}")
    print(f"Function 2 Call: {result['Func2Call']}")