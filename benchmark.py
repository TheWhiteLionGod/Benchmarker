import time
import math
import ast

def benchmark(func1: str, func2: str, params_code: str, iterations: int) -> dict:
    func1Times = []
    func2Times = []

    func1Compiled = compile(func1, "<string>", "exec")
    func2Compiled = compile(func2, "<string>", "exec")

    local_vars = {}
    exec(params_code, {}, local_vars)
    params = local_vars["params"]

    for i in range(iterations):
        local_scope = {"params": params[i]}

        start = time.perf_counter()
        exec(func1Compiled, local_scope)
        func1Times.append(time.perf_counter() - start)

        start = time.perf_counter()
        exec(func2Compiled, local_scope)
        func2Times.append(time.perf_counter() - start)

    func1Avg = sum(func1Times) / len(func1Times)
    func2Avg = sum(func2Times) / len(func2Times)
    return {
        "Func1Times": func1Times,
        "Func2Times": func2Times,
        "Func1Average": round(-math.log10(func1Avg) * 10, 3),
        "Func2Average": round(-math.log10(func2Avg) * 10, 3)
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
