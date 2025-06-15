import time
import math
import ast

def benchmark(func1: str, func2: str, params_code: str) -> dict:
    func1Times = []
    func2Times = []
    try:
        func1Compiled = compile(func1, "", "exec")
    except Exception:
        return 'Function 1 Crashed'
    try:
        func2Compiled = compile(func2, "", "exec")
    except Exception:
        return 'Function 2 Crashed'

    # Create a global environment with common imports
    global_env = {
        '__builtins__': __builtins__,
        'range': range,
        'len': len,
        'list': list,
        'tuple': tuple,
        'dict': dict,
        'set': set,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'round': round,
        'sorted': sorted,
        'reversed': reversed,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
    }
    
    # Try to import common libraries that users might need
    try:
        import numpy as np
        global_env['np'] = np
        global_env['numpy'] = np
        global_env['array'] = np.array
        global_env['arr'] = np.array  # Common shorthand
    except ImportError:
        pass
    
    try:
        import random
        global_env['random'] = random
    except ImportError:
        pass
    
    try:
        import math
        global_env['math'] = math
    except ImportError:
        pass
    
    local_vars = {}
    try:
        exec(params_code, global_env, local_vars)
        params = local_vars["params"]
        iterations = len(params)
    except Exception:
        return 'Invalid Parameters'
    
    for i in range(iterations):
        # Create scope for each function execution with common imports
        local_scope = {"params": params[i]}
        local_scope.update(global_env)  # Add common imports to local scope
        
        start = time.perf_counter()
        try:
            exec(func1Compiled, local_scope)
        except Exception:
            return 'Function 1 Crashed'
        func1Times.append(time.perf_counter() - start)
        
        # Reset local scope for second function
        local_scope = {"params": params[i]}
        local_scope.update(global_env)
        
        start = time.perf_counter()
        try:
            exec(func2Compiled, local_scope)
        except Exception:
            return 'Function 2 Crashed'
        func2Times.append(time.perf_counter() - start)
    
    func1Avg = sum(func1Times) / len(func1Times)
    func2Avg = sum(func2Times) / len(func2Times)
    
    return {
        "Func1Times": func1Times,
        "Func2Times": func2Times,
        "Func1Score": round(-math.log10(func1Avg) * 10, 3),
        "Func2Score": round(-math.log10(func2Avg) * 10, 3)
    }


if __name__ == '__main__':
    func1 = """
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

arr, target = params
result = binary_search(arr, target)
    """

    func2 = """
def normal_search(arr, target):
    for v in arr:
        if v == target:
            return arr.index(v)
    
    return -1

arr, target = params
result = normal_search(arr, target)
    """

    arr = list(range(1, 100000000))

    params = [
        (arr, 500000),
        (arr, 567890),
        (arr, 432100),
        (arr, 876543),
        (arr, 123456),
        (arr, 999999),
        (arr, 1),
        (arr, 1000000),
        (arr, 10001),
        (arr, -1) 
    ]

    results = benchmark(func1, func2, params, iterations=10)
    print(results)
