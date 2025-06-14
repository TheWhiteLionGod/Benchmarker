import os
import ollama
import re
import json

# Set custom Ollama API location
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

def generate_test_code(code_input: str):
    client = ollama.Client()

    prompt = f"""
ONLY return two lines:

1. A single-line variable assignment like:
params = [([1, 2, 3], 2), ([4, 5], 4)]

2. A single-line function call like:
result = binary_search(params[i][0], params[i][1])

⚠️ No explanations, no comments, no extra lines.
⚠️ Do NOT add code fences or markdown (no ```).
⚠️ Do NOT break lines inside the params list.
⚠️ Use this exact format — nothing more.
"""

    try:
        response = client.generate(
            model="deepseek-r1:14b",
            prompt=prompt + "\n\n" + code_input,
            stream=False
        )
        raw_output = response.get("response", "")
        return extract_test_info(raw_output)

    except Exception as e:
        return {"error": str(e)}

def extract_test_info(response_text: str):
    # Remove anything that is NOT one of the two expected lines
    matches = re.findall(r"params\s*=\s*\[.*?\]\s*|result\s*=\s*.*", response_text, re.DOTALL)

    params_line = ""
    result_line = ""

    for match in matches:
        if match.strip().startswith("params ="):
            params_line = re.sub(r"\s+", " ", match.strip())
        elif match.strip().startswith("result ="):
            result_line = re.sub(r"\s+", " ", match.strip())

    return {
        "params_code": params_line,
        "result_line": result_line,
        "full_code": response_text.strip()
    }

# =======================
# Test Example
# =======================
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

# Run it
output = generate_test_code(test_code)
print(json.dumps(output, indent=2))
