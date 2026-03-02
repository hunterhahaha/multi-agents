import subprocess
from langchain.tools import tool

@tool
def python_code_box(code: str) -> str:
    """
    功能：
    一个沙盒环境，用来运行ai生成的python代码。
    输入：
    code：要运行的python代码，纯字符串。
    输出：
    运行结果的stdout。
    异常：
    如果代码运行过程中发生异常，会返回异常信息。
    """
    try:
        result = subprocess.run(
            ["python", "-c", f"{code}"],
            capture_output=True, 
            text=True,
            timeout=30,
        )
        # 捕获异常
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        return result.stdout
    # 处理超时报错
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out, limit 30s."