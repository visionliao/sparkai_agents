# utils.py

import os
import datetime
import pandas as pd
from typing import List, Any, Union, Optional

from mcp.server.fastmcp import FastMCP
from python_http_client import dir_path
mcp = FastMCP("公寓数据查询服务")

# --- 1. 查询现在的系统时间 ---
@mcp.tool()
def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前系统时间，并按指定格式返回
    """
    return datetime.datetime.now().strftime(format_str)


# --- 2. 通用计算工具函数 ---
@mcp.tool()
def calculate_expression(expression: str) -> Any:
    """
    工具名称 (tool_name): calculate_expression
    功能描述 (description): 用于执行一个字符串形式的数学计算。适用于需要进行加、减、乘、除、括号等运算的场景。
    【重要提示】: 此工具仅限于基础数学运算 (+, -, *, /, **) 和几个安全函数 (abs, max, min, pow, round)。它无法执行更复杂的代数或微积分运算。
    输入参数 (parameters):
    name: expression
    type: string
    description: 需要被计算的数学表达式。例如: "10 * (5 + 3)"。
    required: true (必需)
    返回结果 (returns):
    type: number | string
    description: 返回计算结果（数字类型）。如果表达式语法错误或计算出错（如除以零），则返回一个描述错误的字符串。
    """
    try:
        # 限制`eval`的上下文，只允许基础的数学计算
        # 创建一个只包含安全函数的字典
        allowed_names = {
            'abs': abs, 'max': max, 'min': min, 'pow': pow, 'round': round,
            # 可以根据需要添加更多安全的数学函数
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return result
    except (SyntaxError, NameError, TypeError, ZeroDivisionError) as e:
        return f"计算错误: {e}"


# --- 3. 查询指定目录下的文件列表 ---
@mcp.tool()
def list_knowledge():
    """
    查询知识文件目录

    调用后将返回当前可访问的知识文件的文件目录
    """
    dir_path = "csv"
    if not os.path.isdir(dir_path):
        return f"错误：目录 '{dir_path}' 不存在或不是一个有效的目录。"

    try:
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
        return files
    except Exception as e:
        return f"读取目录时发生错误: {e}"


# --- 4. 获取CSV文件前N条数据 ---
@mcp.tool()
def get_csv_head(file: str, n: int = 10) -> str:
    """
    读取指定的.csv文件，并返回其前N条数据
    用于了解.csv文件的字段、内容等基本信息，请你在使用下面的查询工具前先使用这个工具了解文件的基本情况，防止使用查询工具时出现错误
    如果知识文件中有指定表的数据字段注释，可以直接查看该文件的完整内容来了解表结构以及字段含义

    Args:
        file (str): .csv文件的名称
        n (int): 需要返回的数据行数。
                 - 传入正整数 (如 10): 返回文件的前 n 条数据。
                 - 传入 -1: 返回文件的【全部】数据。
                 - 默认值为 10。

    Returns:
        Union[pd.DataFrame, str]: 如果成功，返回一个包含前N条数据的Pandas DataFrame；
                                   否则返回错误信息字符串。
    """

    file_path = f"csv/{file}"
    try:
        df = pd.read_csv(file_path)
        return df.head(n).to_string()
    except FileNotFoundError:
        return f"错误：文件 '{file_path}' 未找到。"
    except Exception as e:
        return f"读取或处理文件时发生错误: {e}"


# --- 5. 通用.csv文件查询工具 ---
@mcp.tool()
def query_csv(file: str, query_string: str):
    """
    通过输入查询语句，查询.csv文件并输出符合条件的数据
    查询语法基于Pandas的 `query` 方法
    使用前请先了解所要查询的表的基本结构，如果知识文件中有指定表的数据字段注释，可以直接查看该文件的完整内容来了解表结构以及字段含义
    调用时完全不需要额外的反斜杠 \

    Args:
        file (str): .csv文件的名称
        query_string (str): Pandas `query` 语法查询字符串。
                            例如: "age > 30", "city == '北京'", "`HI-SCORE` > 1000", "数据来源 == 'AI助理' and 创建人 == '林玉'"
                            (如果列名包含特殊字符，用反引号` `包裹)。

    Returns:
        Union[pd.DataFrame, str]: 如果成功，返回一个包含查询结果的Pandas DataFrame；
                                   否则返回错误信息字符串。
    """

    file = f"csv/{file}"
    try:
        df = pd.read_csv(file)
        result_df = df.query(query_string).to_string()
        return result_df
    except FileNotFoundError:
        return f"错误：文件 '{file}' 未找到。"
    except Exception as e:
        return f"查询时发生错误: {e}"


# --- 6. 通用.csv文件查询计数工具 ---
@mcp.tool()
def count_csv_query(file: str, query_string: str):
    """
    通过输入查询语句，查询.csv文件并输出符合条件的数据的数量
    使用前请先了解所要查询的表的基本结构
    调用时完全不需要额外的反斜杠 \

    Args:
        file (str): .csv文件的名称
        query_string (str): Pandas `query` 语法查询字符串。

    Returns:
        Union[int, str]: 如果成功，返回符合条件的行数（整数）；否则返回错误信息字符串。
    """
    result = query_csv(file, query_string)
    if isinstance(result, str) and result.strip():  # strip()确保不是空字符串
        # 计算行数
        #    - .strip() 去掉首尾可能存在的空行
        #    - .split('\n') 按换行符分割成一个列表
        lines = result.strip().split('\n')

        # 减去表头行
        #    通常第一行是列名，所以数据行数 = 总行数 - 1
        #    我们还要确保至少有一行数据（除了表头）
        if len(lines) > 1:
            data_rows = len(lines) - 1
            return data_rows
        else:
            # 如果只有一行或没有行（可能是只有表头或空结果），则数据量为0
            return 0
    elif isinstance(result, list):
        return len(result)
    else:
        # 如果query_csv返回的是错误信息字符串，则直接返回该信息
        print({type(result)})
        return result


if __name__ == "__main__":
    '''
    print("--- 1. 获取当前时间 ---")
    current_time = get_current_time()
    print(f"当前系统时间是: {current_time}")
    print("-" * 20)

    print("\n--- 2. 计算表达式 ---")
    expression = "(100 + 20) / 2 - 5 * 2"
    result = calculate_expression(expression)
    print(f"表达式 '{expression}' 的计算结果是: {result}")

    # 错误表达式示例
    error_expression = "5 / 0"
    error_result = calculate_expression(error_expression)
    print(f"表达式 '{error_expression}' 的计算结果是: {error_result}")
    print("-" * 20)

    print("\n--- 3. 列出当前目录下的文件 ---")
    # 查询当前目录（'.'代表当前目录）
    files = list_knowledge()
    print(f"当前目录下的文件: {files}")
    print("-" * 20)

    # CSV文件路径
    csv_file = '房间状态表包含已入住住客的信息（数据更新时间2025.5.15）.csv'

    print(f"\n--- 4. 获取 '{csv_file}' 的前5条数据 ---")
    csv_head = get_csv_head(csv_file, n=5)
    print(csv_head)
    print("-" * 20)

    y = "当前状态 == '在住'"
    x = count_csv_query(csv_file, y)
    z = query_csv(csv_file, y)
    print(x)
    print(z)
    '''
    mcp.run(transport="sse")
