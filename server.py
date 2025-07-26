# server.py
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import pandas as pd
import os
import json
from datetime import datetime

# --- 1. 初始化和数据加载 ---

# 从 .env 文件加载环境变量
load_dotenv()

# 初始化 MCP 服务
mcp = FastMCP("Hotel Data Intelligence Service")

# --- 全局数据加载 ---
CSV_FILENAME = 'master_connect_processed.csv'
DATE_COLUMNS = [
    'biz_date', 'arr_date', 'dep_date', 'expected_dep_date',
    'make_ready_date', 'lease_start_date', 'lease_end_date', 'birth',
    'id_begin', 'id_end', 'create_datetime', 'modify_datetime'
]
# 定义一个更全面的列子集用于查询结果展示
COLUMNS_TO_DISPLAY = [
    'id', 'name', 'nation', 'sex', 'arr_date', 'dep_date', 'rmtype',
    'rmno', 'real_rate_long', 'deposit_amount', 'market', 'remark'
]

hotel_df = None


def load_data(filename):
    """加载并预处理酒店CSV数据。"""
    if not os.path.exists(filename):
        print(f"--- 致命错误：数据文件 '{filename}' 未找到。服务器无法启动。 ---")
        return None
    try:
        print(f"--- 正在从 '{filename}' 加载数据... ---")
        df = pd.read_csv(filename, dtype={'id_no': 'str', 'mobile': 'str'}, low_memory=False)
        for col in DATE_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        print("--- 数据加载并预处理完成。 ---")
        return df
    except Exception as e:
        print(f"--- 致命错误：加载数据时失败: {e} ---")
        return None


# 在服务器启动时执行数据加载
hotel_df = load_data(CSV_FILENAME)


# --- 2. 定义 MCP 工具 (LLM 优化版) ---

@mcp.tool()
def get_table_info() -> str:
    """
    获取关于酒店数据表的概览信息。在进行复杂查询前，首先使用此工具来了解数据结构。

    返回:
        一个 JSON 格式的字符串，包含:
        - 'total_records': 表中的记录总数。
        - 'column_names': 所有列名的列表。
        - 'column_data_types': 一个字典，键是列名，值是该列的数据类型 (如 'object' 表示文本, 'int64' 表示整数, 'float64' 表示小数, 'datetime64[ns]' 表示日期)。
        - 'data_sample': 表中前3条记录的样本数据，以展示数据格式。
    """
    if hotel_df is None:
        return "错误: 数据未加载。"

    info = {
        "total_records": len(hotel_df),
        "column_names": hotel_df.columns.tolist(),
        "column_data_types": hotel_df.dtypes.astype(str).to_dict(),
        "data_sample": json.loads(hotel_df.head(3).to_json(orient='records', force_ascii=False))
    }
    # 使用 json.dumps 进行格式化输出
    return json.dumps(info, indent=2, ensure_ascii=False)


@mcp.tool()
def query_by_text(column: str, value: str) -> str:
    """
    在指定的文本列中进行模糊搜索。适用于查找姓名、国籍、房型等。

    Args:
        column (str): 要进行查询的列名。必须是文本类型的列。例如: 'name', 'nation', 'rmtype', 'remark'。
        value (str): 要搜索的文本关键词。此为模糊匹配，不区分大小写。例如: 搜索 '王' 可以找到 '王**'。

    返回:
        一个 JSON 格式的字符串，其中包含一个匹配记录的列表。若无结果，则列表为空。
    """
    if hotel_df is None:
        return "错误: 数据未加载。"
    if column not in hotel_df.columns:
        return f"错误: 列名 '{column}' 不存在。"

    try:
        results_df = hotel_df[hotel_df[column].astype(str).str.contains(value, case=False, na=False)]
        return results_df[COLUMNS_TO_DISPLAY].to_json(orient='records', indent=2, force_ascii=False)
    except Exception as e:
        return f"查询过程中发生错误: {e}"


@mcp.tool()
def query_by_date_range(date_column: str, start_date: str, end_date: str) -> str:
    """
    在指定的日期列中，根据一个时间范围进行精确查询。

    Args:
        date_column (str): 要进行查询的日期列名。例如: 'arr_date', 'dep_date', 'create_datetime'。
        start_date (str): 范围的开始日期，必须是 'YYYY-MM-DD' 格式。
        end_date (str): 范围的结束日期，必须是 'YYYY-MM-DD' 格式。

    返回:
        一个 JSON 格式的字符串，其中包含一个匹配记录的列表。若无结果，则列表为空。
    """
    if hotel_df is None:
        return "错误: 数据未加载。"
    if date_column not in hotel_df.columns:
        return f"错误: 列名 '{date_column}' 不存在。"
    if not pd.api.types.is_datetime64_any_dtype(hotel_df[date_column]):
        return f"错误: 列 '{date_column}' 不是有效的日期类型。"

    try:
        s_date = pd.to_datetime(start_date)
        e_date = pd.to_datetime(end_date)
        mask = (hotel_df[date_column] >= s_date) & (hotel_df[date_column] <= e_date)
        results_df = hotel_df.loc[mask]
        return results_df[COLUMNS_TO_DISPLAY].to_json(orient='records', indent=2, force_ascii=False)
    except Exception as e:
        return f"查询过程中发生错误: {e}"


@mcp.tool()
def query_by_numerical_range(column: str, min_value: float | None = None, max_value: float | None = None) -> str:
    """
    在指定的数值列中，根据一个范围进行查询。可以只提供最小值或最大值。

    Args:
        column (str): 要进行查询的数值列名。例如: 'real_rate_long', 'deposit_amount', 'id'。
        min_value (float, optional): 范围的下限（大于或等于此值）。如果省略，则无下限。
        max_value (float, optional): 范围的上限（小于或等于此值）。如果省略，则无上限。

    返回:
        一个 JSON 格式的字符串，其中包含一个匹配记录的列表。若无结果，则列表为空。
    """
    if hotel_df is None:
        return "错误: 数据未加载。"
    if column not in hotel_df.columns:
        return f"错误: 列名 '{column}' 不存在。"
    if not pd.api.types.is_numeric_dtype(hotel_df[column]):
        return f"错误: 列 '{column}' 不是有效的数值类型。"
    if min_value is None and max_value is None:
        return "错误: 必须提供 min_value 或 max_value 中的至少一个。"

    try:
        mask = pd.Series(True, index=hotel_df.index)
        if min_value is not None:
            mask &= (hotel_df[column] >= min_value)
        if max_value is not None:
            mask &= (hotel_df[column] <= max_value)
        results_df = hotel_df.loc[mask]
        return results_df[COLUMNS_TO_DISPLAY].to_json(orient='records', indent=2, force_ascii=False)
    except Exception as e:
        return f"查询过程中发生错误: {e}"


@mcp.tool()
def get_statistics(column: str, group_by_column: str | None = None, aggregation: str = 'mean') -> str:
    """
    对数据进行统计分析。此工具有两种模式：
    1. 单列分析: 只提供 `column` 参数时，对该列进行统计。数值列返回描述性统计（均值、方差等），分类列返回频数统计。
    2. 分组聚合: 同时提供 `column` 和 `group_by_column` 时，按 `group_by_column` 对 `column` 进行聚合计算。

    Args:
        column (str): 需要分析或计算的列名。例如 'real_rate_long', 'nation'。
        group_by_column (str, optional): 用于分组的分类列名。例如: 'rmtype', 'sex'。
        aggregation (str, optional): 分组时使用的聚合函数。可选值: 'mean', 'sum', 'count', 'median', 'max', 'min'。默认为 'mean'。

    返回:
        一个 JSON 格式的字符串，包含统计结果。
    """
    if hotel_df is None:
        return "错误: 数据未加载。"
    if column not in hotel_df.columns:
        return f"错误: 列名 '{column}' 不存在。"

    try:
        # 模式2: 分组聚合分析
        if group_by_column:
            if group_by_column not in hotel_df.columns:
                return f"错误: 分组列 '{group_by_column}' 不存在。"
            result = hotel_df.groupby(group_by_column)[column].agg(aggregation)
            return result.to_json(orient='index', force_ascii=False)

        # 模式1: 单列统计分析
        else:
            if pd.api.types.is_numeric_dtype(hotel_df[column]):
                # 数值列的描述性统计
                return hotel_df[column].describe().to_json(orient='index')
            else:
                # 分类列的频数统计
                return hotel_df[column].value_counts().to_json(orient='index')
    except Exception as e:
        return f"分析过程中发生错误: {e}"


# --- 3. 启动服务器 ---

if __name__ == "__main__":
    if hotel_df is not None:
        print("\n--- Hotel Data Intelligence Service (v5.0) 准备就绪，正在启动... ---")
        mcp.run(transport="sse")
    else:
        print("\n--- 服务器启动失败，因为数据未能加载。---")