import os
import re
import time
import ollama

# Set custom Ollama API location
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

# Binary search implementation
def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

# Generate test case lines from CodeGemma or other LLMs
def generate_test_code(code_input: str):
    client = ollama.Client()

    prompt = """
ONLY return exactly 2 lines:

1. params = [(arr, 1000000), (arr, 500000), ...]
2. result = binary_search(params[i][0], params[i][1])

⚠️ No explanations. No placeholders like target1.
⚠️ No markdown. Keep everything on one line.
"""

    try:
        response = client.generate(
            model="codegemma:instruct",
            prompt=prompt + "\n\n" + code_input,
            stream=False
        )
        raw_output = re.sub(r"<.*?>", "", response.get("response", ""))
        return extract_test_info(raw_output)
    except Exception as e:
        return {"error": str(e)}

# Extract and clean param/result lines
def extract_test_info(text: str):
    params_line = ""
    result_line = ""
    for line in text.strip().splitlines():
        if line.strip().startswith("params =") and not params_line:
            params_line = line.strip()
        elif line.strip().startswith("result =") and not result_line:
            result_line = line.strip()
        if params_line and result_line:
            break

    if not params_line:
        raise ValueError("Missing 'params =' line")
    if not result_line:
        raise ValueError("Missing 'result =' line")

    return {
        "params_code": params_line,
        "result_line": result_line,
        "full_code": text.strip()
    }

# Sort parameters based on time taken for binary_search
def sort_params_by_runtime(params):
    results = []
    for p in params:
        start = time.perf_counter()
        binary_search(*p)
        end = time.perf_counter()
        elapsed = end - start
        results.append((elapsed, p))

    results.sort(reverse=True)  # slowest first
    return [pair for _, pair in results]

# ===============================
# Main Execution
# ===============================
if __name__ == "__main__":
    arr = list(range(1, 1000001))  # Large sorted array

    code_input = """
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

    result = generate_test_code(code_input)

    if "params_code" not in result:
        print("❌ Error:", result.get("error", "Unknown"))
        exit()

    print("\n🔍 AI Generated:")
    print(result["params_code"])
    print(result["result_line"])

    try:
        # Extract params list string and evaluate with 'arr' defined
        param_str = result["params_code"].split("=", 1)[1].strip()
        raw_params = eval(param_str, {"arr": arr})

        # Filter out invalid entries such as ellipsis
        params = [p for p in raw_params if isinstance(p, tuple) and len(p) == 2]

    except Exception as e:
        print("❌ Failed to parse params:", e)
        exit()

    # Sort parameters by runtime (slowest to fastest)
    sorted_params = sort_params_by_runtime(params)

    print("\n✅ Sorted Params (Slowest → Fastest):")
    print("params = [")
    for p in sorted_params:
        print(f"    {p},")
    print("]")
