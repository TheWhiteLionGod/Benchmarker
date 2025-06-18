import time
import numpy as np
import math
from typing import Dict, Any

def benchmark(func1: str, func2: str, params_code: str) -> dict:
    """Original synchronous benchmark function"""
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

def benchmark_async(user_id: str, func1: str, func2: str, params_code: str, 
                   user_data: Dict[str, Dict[str, Any]], 
                   user_benchmark_status: Dict[str, Dict[str, Any]]):
    """
    Asynchronous benchmark function that updates status as it progresses
    
    Args:
        user_id: Unique identifier for the user
        func1: Source code for function 1
        func2: Source code for function 2
        params_code: Parameters code to execute
        user_data: Dictionary containing all user data
        user_benchmark_status: Dictionary containing all user benchmark status data
    """
    
    # Get user-specific status
    status = user_benchmark_status.get(user_id, {})
    
    if not status:
        print(f"Warning: No benchmark status found for user {user_id}")
        return
    
    try:
        # Update status to running
        status["status"] = "running"
        status["progress"] = 5
        status["message"] = "Compiling functions..."
        
        func1Times = []
        func2Times = []
        
        # Compile functions
        try:
            func1Compiled = compile(func1, "", "exec")
            status["progress"] = 10
        except Exception as e:
            status["status"] = "error"
            status["error"] = f"Function 1 compilation error: {str(e)}"
            print(f"Function 1 compilation error for user {user_id}: {str(e)}")
            return
            
        try:
            func2Compiled = compile(func2, "", "exec")
            status["progress"] = 15
        except Exception as e:
            status["status"] = "error"
            status["error"] = f"Function 2 compilation error: {str(e)}"
            print(f"Function 2 compilation error for user {user_id}: {str(e)}")
            return

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
        
        # Parse parameters
        status["message"] = "Parsing parameters..."
        local_vars = {}
        try:
            exec(params_code, global_env, local_vars)
            params = local_vars["params"]
            iterations = len(params)
            status["total_tests"] = iterations
            status["progress"] = 20
        except Exception as e:
            status["status"] = "error"
            status["error"] = f"Invalid parameters: {str(e)}"
            print(f"Parameter parsing error for user {user_id}: {str(e)}")
            return
        
        # Run benchmarks
        status["message"] = "Running benchmark tests..."
        
        for i in range(iterations):
            status["current_test"] = i + 1
            status["message"] = f"Running test {i + 1} of {iterations}..."
            
            # Calculate progress (20% to 90% for tests)
            test_progress = 20 + int((i / iterations) * 70)
            status["progress"] = test_progress
            
            # Create scope for each function execution with common imports
            local_scope = {"params": params[i]}
            local_scope.update(global_env)  # Add common imports to local scope
            
            # Test Function 1
            start = time.perf_counter()
            try:
                exec(func1Compiled, local_scope)
            except Exception as e:
                status["status"] = "error"
                status["error"] = f"Function 1 crashed on test {i + 1}: {str(e)}"
                print(f"Function 1 runtime error for user {user_id} on test {i + 1}: {str(e)}")
                return
            func1Times.append(time.perf_counter() - start)
            
            # Reset local scope for second function
            local_scope = {"params": params[i]}
            local_scope.update(global_env)
            
            # Test Function 2
            start = time.perf_counter()
            try:
                exec(func2Compiled, local_scope)
            except Exception as e:
                status["status"] = "error"
                status["error"] = f"Function 2 crashed on test {i + 1}: {str(e)}"
                print(f"Function 2 runtime error for user {user_id} on test {i + 1}: {str(e)}")
                return
            func2Times.append(time.perf_counter() - start)
        
        # Calculate results
        status["message"] = "Calculating results..."
        status["progress"] = 90
        
        func1Avg = sum(func1Times) / len(func1Times)
        func2Avg = sum(func2Times) / len(func2Times)
        
        # Store results in user_data
        result = {
            "Func1Times": func1Times,
            "Func2Times": func2Times,
            "Func1Score": round(-math.log10(func1Avg) * 10, 3),
            "Func2Score": round(-math.log10(func2Avg) * 10, 3),
            "Program1Code": func1,
            "Program2Code": func2,
            # Initialize AI feedback placeholders
            "AI_Feedback1": "Analyzing function performance...",
            "AI_Feedback2": "Analyzing function performance...",
            "Comparative_Feedback": "Generating comparative analysis..."
        }
        
        user_data[user_id] = result
        
        # Update final status
        status["status"] = "complete"
        status["progress"] = 100
        status["message"] = "Benchmark completed successfully!"
        status["current_test"] = iterations
        
        print(f"Benchmark completed for user {user_id}")
        
        # Initialize AI status for this user
        from utils.flask_utils import user_ai_status
        user_ai_status[user_id] = {
            "status": "pending",
            "progress": 0,
            "error": None
        }
        
    except Exception as e:
        print(f"Unexpected error during benchmark for user {user_id}: {str(e)}")
        status["status"] = "error"
        status["error"] = f"Unexpected error: {str(e)}"


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

    params_code = """
arr = list(range(1, 100_000))
params = [
    (arr, 500),
    (arr, 5678),
    (arr, 4321),
    (arr, 8765),
    (arr, 1234),
    (arr, 9999),
    (arr, 1),
    (arr, 10000),
    (arr, 1001),
    (arr, -1) 
]
"""

    results = benchmark(func1, func2, params_code)
    print(results)