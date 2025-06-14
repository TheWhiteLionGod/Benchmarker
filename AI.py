import os
import ollama
import re
import json

os.environ["OLLAMA_HOST"] = "https://4aa8-68-194-75-55.ngrok-free.app"

def generate_test_code(code_input: str):
    client = ollama.Client()

    prompt = f"""
You are a Python code evaluator. Given the following function:

{code_input}

Your job is to:
1. Create a variable 'params' as a list of test cases, where each test case is a tuple of arguments, like:
   params = [(arg1, arg2), (arg1, arg2)]

2. Output a line that calls the function like:
   result = <function_name>(params[i][0], params[i][1], ...)

Rules:
- Do NOT explain anything.
- Do NOT use markdown or code fences.
- Only return raw Python code.
- Use the variable name 'result' for the function call.
- Use 'params[i][0]', 'params[i][1]', etc., so it can be run in a loop.
"""

    try:
        response = client.generate(
            model="deepseek-r1:14b",
            prompt=prompt,
            stream=False
        )
        raw_output = response.get("response", "")
        return extract_test_info(raw_output)

    except Exception as e:
        return {"error": str(e)}

def extract_test_info(response_text: str):
    # Remove backticks, <think>, and clean whitespace
    cleaned = re.sub(r"`{3}(?:python)?|<think>|</think>", "", response_text, flags=re.IGNORECASE).strip()

    # Extract params assignment: find the 'params =' line and grab everything after it up to a blank line or end
    params_match = re.search(r"(params\s*=\s*\[.*?\])", cleaned, re.DOTALL)
    params_str = params_match.group(1).strip() if params_match else ""

    # Now convert params list-of-lists style to list-of-tuples style string:
    # Remove newlines and excessive whitespace inside params_str
    params_str = re.sub(r"\s+", " ", params_str)

    # Replace inner [ ] with ( ) for tuples, but only one level inside the main list
    # Example: params = [ [1,2], [3,4] ] --> params = [(1,2), (3,4)]
    def brackets_to_tuples(match):
        inner = match.group(1)
        return f"({inner})"

    # Replace all occurrences of square brackets containing numbers inside the main list
    params_str = re.sub(r"\[\s*([^\[\]]+?)\s*\]", brackets_to_tuples, params_str)

    # Also collapse multiple spaces
    params_str = re.sub(r"\s+", " ", params_str)

    # Extract result line (the function call)
    result_line = None
    for line in cleaned.splitlines():
        if line.strip().startswith("result ="):
            result_line = line.strip()
            break

    return {
        "params_code": params_str,
        "result_line": result_line or "",
        "full_code": cleaned
    }

# ================
# TEST INPUT
# ================
test_code = """
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
"""

output = generate_test_code(test_code)

print(json.dumps(output, indent=2))
