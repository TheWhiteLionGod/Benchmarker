import time

def benchmark(func1: str, func2: str, params: list, iterations: int) -> dict:
    """
    params - [(param1, param2), (param1, param2)]
    """

    func1Times: list = []
    func2Times: list = []

    func1Compiled = compile(func1, "<string>", "exec")
    func2Compiled = compile(func2, "<string>", "exec")

    startTime: float = time.time()
    for i in range(iterations):
        exec(func1Compiled)
        func1Times.append(time.time() - startTime)
        
        exec(func2Compiled)
        func2Times.append(time.time() - startTime)
    
    return {
        "Func1": func1Times,
        "Func2": func2Times
    }