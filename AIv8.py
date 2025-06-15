import os
import requests
import re

os.environ["OLLAMA_HOST"] = "http://localhost:11434"

def call_ollama(prompt: str) -> str:
    """Call Ollama API with codegemma:instruct model"""
    url = f"{os.environ['OLLAMA_HOST']}/api/generate"
    
    payload = {
        "model": "codegemma:instruct",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Very low temperature for consistent formatting
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

def clean_ai_response(response: str) -> str:
    """Clean up AI response to extract just the code"""
    # Remove markdown code blocks
    response = re.sub(r'```python\s*', '', response)
    response = re.sub(r'```\s*', '', response)
    
    # Remove any explanation text before/after code
    lines = response.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        # Start collecting when we see a def or import
        if line.strip().startswith(('def ', 'import ', 'from ', 'class ')):
            in_code = True
        
        if in_code:
            code_lines.append(line)
    
    # If no code found with above method, just clean the whole response
    if not code_lines:
        # Remove common explanation phrases
        response = re.sub(r'Here\'s.*?code:?\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'The formatted.*?is:?\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'Here are the.*?functions:?\s*', '', response, flags=re.IGNORECASE)
        return response.strip()
    
    return '\n'.join(code_lines).strip()

def format_code(code: str) -> str:
    """
    Format Python code using AI to fix indentation, spacing, and minor syntax errors.
    
    Args:
        code: String containing Python code to format
        
    Returns:
        Formatted and corrected Python code
    """
    
    prompt = f"""Fix and format this Python code:

{code}

Requirements:
- Fix proper indentation (4 spaces per level)
- Add proper spacing around operators
- Fix any minor syntax errors
- Ensure proper line breaks
- Keep the logic exactly the same
- Return ONLY the corrected code, no explanations

"""
    
    print("🤖 AI is formatting the code...")
    ai_response = call_ollama(prompt)
    
    if not ai_response:
        print("⚠️ AI didn't respond, returning original code")
        return code
    
    # Clean up the AI response
    formatted_code = clean_ai_response(ai_response)
    
    # Basic validation - make sure we still have function definitions
    if 'def ' not in formatted_code and 'def ' in code:
        print("⚠️ AI response seems incomplete, returning original code")
        return code
    
    return formatted_code

def format_multiple_functions(func1_code: str, func2_code: str) -> tuple:
    """
    Format two functions separately and return both.
    
    Args:
        func1_code: First function code
        func2_code: Second function code
        
    Returns:
        Tuple of (formatted_func1, formatted_func2)
    """
    
    # Combine both functions for formatting
    combined_code = f"{func1_code}\n\n{func2_code}"
    
    prompt = f"""Fix and format these Python functions:

{combined_code}

Requirements:
- Fix proper indentation (4 spaces per level)
- Add proper spacing around operators and commas
- Fix any minor syntax errors (missing colons, parentheses, etc.)
- Ensure proper line breaks
- Keep the logic exactly the same
- Return ONLY the corrected functions, no explanations or comments

"""
    
    print("🤖 AI is formatting both functions...")
    ai_response = call_ollama(prompt)
    
    if not ai_response:
        print("⚠️ AI didn't respond, returning original code")
        return func1_code, func2_code
    
    # Clean up the AI response
    formatted_code = clean_ai_response(ai_response)
    
    # Try to split the functions
    functions = re.findall(r'def\s+\w+.*?(?=def\s+\w+|$)', formatted_code, re.DOTALL)
    
    if len(functions) >= 2:
        func1_formatted = functions[0].strip()
        func2_formatted = functions[1].strip()
        print("✅ Successfully formatted both functions")
        return func1_formatted, func2_formatted
    elif len(functions) == 1:
        print("⚠️ Only found one function in AI response, formatting individually")
        func1_formatted = format_code(func1_code)
        func2_formatted = format_code(func2_code)
        return func1_formatted, func2_formatted
    else:
        print("⚠️ Couldn't parse functions from AI response, formatting individually")
        func1_formatted = format_code(func1_code)
        func2_formatted = format_code(func2_code)
        return func1_formatted, func2_formatted

# Example usage
if __name__ == "__main__":
    # Test with messy code
    func1 = "def binary_search(arr,target):low=0\nhigh=len(arr)-1\nwhile low<=high:mid=(low+high)//2\nif arr[mid]==target:return mid\nelif arr[mid]<target:low=mid+1\nelse:high=mid-1\nreturn -1"
    
    func2 = "def linear_search(arr,target):\nfor i in range(len(arr)):\nif arr[i]==target:\nreturn i\nreturn -1"
    
    print("Original Function 1:")
    print(repr(func1))
    print("\nOriginal Function 2:")
    print(repr(func2))
    
    # Format both functions
    formatted_func1, formatted_func2 = format_multiple_functions(func1, func2)
    
    print("\n" + "="*50)
    print("FORMATTED RESULTS:")
    print("="*50)
    
    print("\nFormatted Function 1:")
    print(formatted_func1)
    
    print("\nFormatted Function 2:")
    print(formatted_func2)
    
    # Test single function formatting
    print("\n" + "="*50)
    print("SINGLE FUNCTION TEST:")
    print("="*50)
    
    messy_func = "def bubble_sort(arr):n=len(arr)\nfor i in range(n):for j in range(0,n-i-1):if arr[j]>arr[j+1]:arr[j],arr[j+1]=arr[j+1],arr[j]"
    
    print("\nOriginal messy function:")
    print(repr(messy_func))
    
    clean_func = format_code(messy_func)
    
    print("\nFormatted function:")
    print(clean_func)