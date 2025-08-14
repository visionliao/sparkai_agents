# server.py
import numpy as np
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import traceback

from analyzer import ProjectFinancials

# --- 1. 配置与初始化 (No changes here) ---

load_dotenv()
CSV_FILE_PATH = 'master_connect_processed.csv'
mcp = FastMCP("公寓长租数据高级查询服务")

main_df: Optional[pd.DataFrame] = None
REFERENCE_DATE = datetime.now()
DISPLAY_COLUMNS = [
    'id', 'master_id', 'sta', 'name', 'age', 'rmno', 'arr_date', 'dep_date',
    'full_rate_long', 'remark', 'nation', 'sex'
]

# --- 2. 核心数据加载与辅助函数 (No changes here) ---

def load_data(file_path: str) -> Optional[pd.DataFrame]:
    # ... (与之前相同)
    if not os.path.exists(file_path):
        print(f"错误: 数据文件 '{file_path}' 未找到。")
        return None
    try:
        df = pd.read_csv(file_path, low_memory=False)
        date_columns = ['arr_date', 'dep_date', 'lease_start_date', 'lease_end_date', 'birth']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        print(f"成功加载并预处理数据，共 {len(df)} 条记录。")
        return df
    except Exception as e:
        print(f"加载数据文件时发生严重错误: {e}")
        return None


# 【新增】一个健壮的类型转换辅助函数
def convert_to_native_types(obj: Any) -> Any:
    """
    递归地将对象中的Numpy类型转换为Python原生类型，以确保JSON序列化安全。
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (dict, list)):
        if isinstance(obj, dict):
            return {k: convert_to_native_types(v) for k, v in obj.items()}
        else:
            return [convert_to_native_types(i) for i in obj]
    # 对所有字符串进行清洗，处理空值
    elif pd.isna(obj):
        return None  # 使用 None 代表 JSON 中的 null
    elif isinstance(obj, str):
        # 强制UTF-8编码，忽略错误字符，这是最稳妥的方式
        return obj.encode('utf-8', 'ignore').decode('utf-8')
    return obj


def format_df_for_output(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    【最终修复版】
    将DataFrame格式化为适合API返回的列表。
    此版本通过一个专门的类型转换步骤来确保数据安全。
    """
    if df.empty:
        return []

    display_df = df.copy()

    # 1. 计算和格式化列 (与之前相同)
    if 'birth' in display_df.columns and not display_df['birth'].isnull().all():
        ages = (REFERENCE_DATE - display_df['birth']).dt.days / 365.25
        display_df['age'] = ages.apply(lambda x: int(x) if pd.notna(x) else None)
    else:
        display_df['age'] = None
    for col in ['arr_date', 'dep_date']:
        if col in display_df.columns:
            display_df[col] = display_df[col].dt.strftime('%Y-%m-%d').fillna('')

    # 2. 转换为字典列表
    final_columns = [col for col in DISPLAY_COLUMNS if col in display_df.columns]
    records = display_df[final_columns].to_dict('records')

    # 3. 【关键修复】对生成的字典列表进行深度类型转换
    safe_records = convert_to_native_types(records)

    return safe_records

# --- 3. 内部统计分析辅助函数 (No changes here) ---

def _analyze_age(df: pd.DataFrame) -> List[Dict[str, Any]]:
    # ... (implementation from previous step)
    unique_guests_df = df.dropna(subset=['birth']).drop_duplicates(subset=['profile_id'])
    if unique_guests_df.empty: return []
    unique_guests_df['age'] = ((REFERENCE_DATE - unique_guests_df['birth']).dt.days / 365.25).astype(int)
    bins = [0, 18, 25, 35, 45, 55, 65, 120]; labels = ['18岁及以下', '19-25岁', '26-35岁', '36-45岁', '46-55岁', '56-65岁', '65岁以上']
    unique_guests_df['age_group'] = pd.cut(unique_guests_df['age'], bins=bins, labels=labels, right=False)
    age_counts = unique_guests_df['age_group'].value_counts().sort_index(); age_percentage = unique_guests_df['age_group'].value_counts(normalize=True).sort_index() * 100
    return [{"group": group, "count": int(count), "percentage": f"{age_percentage[group]:.2f}%"} for group, count in age_counts.items()]

def _analyze_nationality(df: pd.DataFrame, top_n: int = 15) -> List[Dict[str, Any]]:
    # ... (implementation from previous step)
    unique_guests_df = df.drop_duplicates(subset=['profile_id'])
    if unique_guests_df.empty: return []
    nation_counts = unique_guests_df['nation'].value_counts(); nation_percentage = unique_guests_df['nation'].value_counts(normalize=True) * 100
    return [{"nation": nation, "count": int(count), "percentage": f"{nation_percentage[nation]:.2f}%"} for nation, count in nation_counts.head(top_n).items()]

def _analyze_gender(df: pd.DataFrame) -> List[Dict[str, Any]]:
    # ... (implementation from previous step)
    valid_gender_df = df[df['sex'].isin(['男性', '女性'])].drop_duplicates(subset=['profile_id'])
    if valid_gender_df.empty: return []
    gender_counts = valid_gender_df['sex'].value_counts(); gender_percentage = valid_gender_df['sex'].value_counts(normalize=True) * 100
    return [{"gender": gender, "count": int(count), "percentage": f"{gender_percentage[gender]:.2f}%"} for gender, count in gender_counts.items()]


# --- 4. 【升级】工具函数，包含详细描述 ---

@mcp.tool()
def advanced_search(
    name: Optional[str] = None,
    room_number: Optional[str] = None,
    status: Optional[str] = None,
    nation: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_rent: Optional[float] = None,
    max_rent: Optional[float] = None,
    remark_keyword: Optional[str] = None,
    include_analysis: bool = False
) -> Dict[str, Any]:
    """
    对住客数据进行全面的多条件组合查询，并可选择性地返回统计分析。

    此工具是系统中最强大的查询功能。你可以提供一个或多个筛选条件，系统会返回所有
    满足这些条件的记录。所有筛选条件都以"与"(AND)逻辑组合。如果想了解结果集的人口
    统计学特征，请将 `include_analysis` 设为 True。

    Args:
        name (Optional[str]): 按住客姓名进行模糊搜索 (不区分大小写)。例如: 'wang'。
        room_number (Optional[str]): 按房号进行精确匹配。例如: '1508'。
        status (Optional[str]): 按住客状态进行精确筛选。必须是以下值之一:
                                'I' (In-House, 在住),
                                'R' (Reservation, 预订),
                                'O' (Checked-Out, 已离店),
                                'X' (Cancelled, 已取消)。
        nation (Optional[str]): 按国籍进行模糊搜索 (不区分大小写)。例如: '中国'。
        min_age (Optional[int]): 筛选住客的最小年龄 (包含此年龄)。
        max_age (Optional[int]): 筛选住客的最大年龄 (包含此年龄)。
        min_rent (Optional[float]): 筛选月租金的最低值 (包含此值)。
        max_rent (Optional[float]): 筛选月租金的最高值 (包含此值)。
        remark_keyword (Optional[str]): 在备注字段中进行模糊搜索 (不区分大小写)。例如: '宠物' 或 'VIP'。
        include_analysis (bool): 是否返回对查询结果的统计分析。默认为 False 以提高性能。
                                 设为 True 可获取年龄、国籍和性别分布。

    Returns:
        一个包含查询结果的字典对象，其结构如下:
        {
          "count": int,  // 符合条件的记录总数
          "results": [   // 包含住客记录的列表
            {
              "id": int,
              "name": str,
              "age": int,
              "nation": str,
              ... // 其他住客信息字段
            }
          ],
          "analysis": null | { // 如果 include_analysis=True 且有结果，则包含此对象
              "based_on": str, // 描述分析所基于的独立住客数量
              "age_distribution": [{"group": str, "count": int, "percentage": str}],
              "nationality_distribution": [{"nation": str, "count": int, "percentage": str}],
              "gender_distribution": [{"gender": str, "count": int, "percentage": str}]
            }
        }
    """
    if main_df is None:
        return {"error": "数据未加载，查询功能不可用。", "count": 0, "results": [], "analysis": None}

    results_df = main_df.copy()

    # --- 【核心修改部分】 ---
    # 对所有基于字符串的模糊搜索增加健壮性处理

    # 处理 'name' 筛选
    if name:
        if 'name' in results_df.columns:
            # 将该列强制转换为字符串类型，以防其中混有数字等非字符串数据
            # na=False 会让原始的空值(NaN)不参与匹配，这是安全的。
            results_df = results_df[results_df['name'].astype(str).str.contains(name, case=False, na=False)]

    # 处理 'nation' 筛选 (解决你当前问题的关键)
    if nation:
        # 1. 首先检查 'nation' 列是否存在，防止 KeyError
        if 'nation' in results_df.columns:
            # 2. 然后，将列转换为字符串类型，防止 TypeError
            results_df = results_df[results_df['nation'].astype(str).str.contains(nation, case=False, na=False)]

    # 处理 'remark_keyword' 筛选
    if remark_keyword:
        if 'remark' in results_df.columns:
            results_df = results_df[results_df['remark'].astype(str).str.contains(remark_keyword, case=False, na=False)]

    # --- 其他筛选逻辑保持不变 ---

    if room_number:
        if 'rmno' in results_df.columns:
            results_df = results_df[results_df['rmno'].astype(str) == room_number]

    if status and status.upper() in ['R', 'I', 'O', 'X']:
        if 'sta' in results_df.columns:
            results_df = results_df[results_df['sta'] == status.upper()]

    # 年龄筛选
    if min_age is not None or max_age is not None:
        if 'birth' in results_df.columns and pd.api.types.is_datetime64_any_dtype(results_df['birth']):
            ages = (REFERENCE_DATE - results_df['birth']).dt.days / 365.25
            # 使用 .loc 赋值以避免 SettingWithCopyWarning
            results_df = results_df.loc[ages.notna()]
            ages = ages.dropna()
            if min_age is not None:
                results_df = results_df.loc[ages >= min_age]
            if max_age is not None:
                results_df = results_df.loc[ages <= max_age]

    # 租金筛选
    if 'full_rate_long' in results_df.columns:
        if min_rent is not None:
            results_df = results_df[results_df['full_rate_long'] >= min_rent]
        if max_rent is not None:
            results_df = results_df[results_df['full_rate_long'] <= max_rent]

    # --- 返回结构保持不变 ---
    response = {
        "count": len(results_df),
        "results": format_df_for_output(results_df),
        "analysis": None
    }

    if include_analysis and not results_df.empty:
        unique_results_df = results_df[
            results_df['profile_id'] != 0] if 'profile_id' in results_df.columns else results_df
        response["analysis"] = {
            "based_on": f"{len(unique_results_df.drop_duplicates(subset=['profile_id'])) if 'profile_id' in unique_results_df.columns else len(unique_results_df)} unique guests from {len(results_df)} records",
            "age_distribution": _analyze_age(unique_results_df),
            "nationality_distribution": _analyze_nationality(unique_results_df),
            "gender_distribution": _analyze_gender(unique_results_df)
        }

    return response


@mcp.tool()
def get_statistical_summary(
        name: Optional[str] = None,
        room_number: Optional[str] = None,
        status: Optional[str] = None,
        nation: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        min_rent: Optional[float] = None,
        max_rent: Optional[float] = None,
        remark_keyword: Optional[str] = None
) -> Dict[str, Any]:
    """
    根据筛选条件对住客数据进行统计分析，但不返回具体的住客记录。

    注意：当使用上面的全面查询工具失败后，可尝试使用这个工具再次尝试查询统计结果

    此工具专门用于获取宏观的人口统计学特征。你可以提供一个或多个筛选条件，
    系统将对所有满足条件的记录进行分析，并返回年龄、国籍和性别的分布情况。
    这比调用 advanced_search(include_analysis=True) 更高效，因为它不处理和传输
    单条记录数据。

    例如可以使用这个工具获取到公寓目前的在住的统计信息

    Args:
        name (Optional[str]): 按住客姓名进行模糊搜索。
        room_number (Optional[str]): 按房号进行精确匹配。
        status (Optional[str]): 按住客状态进行精确筛选 ('I', 'R', 'O', 'X')。
        nation (Optional[str]): 按国籍进行模糊搜索。
        min_age (Optional[int]): 筛选住客的最小年龄。
        max_age (Optional[int]): 筛选住客的最大年龄。
        min_rent (Optional[float]): 筛选月租金的最低值。
        max_rent (Optional[float]): 筛选月租金的最高值。
        remark_keyword (Optional[str]): 在备注字段中进行模糊搜索。

    Returns:
        一个包含统计分析结果的字典对象，其结构如下:
        {
          "count": int,  // 符合条件的记录总数
          "analysis": null | { // 如果有结果，则包含此对象
              "based_on": str, // 描述分析所基于的独立住客数量
              "age_distribution": [{"group": str, "count": int, "percentage": str}],
              "nationality_distribution": [{"nation": str, "count": int, "percentage": str}],
              "gender_distribution": [{"gender": str, "count": int, "percentage": str}]
            }
        }
    """
    if main_df is None:
        return {"error": "数据未加载，分析功能不可用。", "count": 0, "analysis": None}

    # --- 筛选逻辑与 advanced_search 完全相同 ---
    results_df = main_df.copy()
    if name:
        if 'name' in results_df.columns:
            results_df = results_df[results_df['name'].astype(str).str.contains(name, case=False, na=False)]
    if nation:
        if 'nation' in results_df.columns:
            results_df = results_df[results_df['nation'].astype(str).str.contains(nation, case=False, na=False)]
    if remark_keyword:
        if 'remark' in results_df.columns:
            results_df = results_df[results_df['remark'].astype(str).str.contains(remark_keyword, case=False, na=False)]
    if room_number:
        if 'rmno' in results_df.columns:
            results_df = results_df[results_df['rmno'].astype(str) == room_number]
    if status and status.upper() in ['R', 'I', 'O', 'X']:
        if 'sta' in results_df.columns:
            results_df = results_df[results_df['sta'] == status.upper()]
    if min_age is not None or max_age is not None:
        if 'birth' in results_df.columns and pd.api.types.is_datetime64_any_dtype(results_df['birth']):
            ages = (REFERENCE_DATE - results_df['birth']).dt.days / 365.25
            results_df = results_df.loc[ages.notna()]
            ages = ages.dropna()
            if min_age is not None:
                results_df = results_df.loc[ages >= min_age]
            if max_age is not None:
                results_df = results_df.loc[ages <= max_age]
    if 'full_rate_long' in results_df.columns:
        if min_rent is not None:
            results_df = results_df[results_df['full_rate_long'] >= min_rent]
        if max_rent is not None:
            results_df = results_df[results_df['full_rate_long'] <= max_rent]

    # --- 构建仅包含统计信息的返回结构 ---
    count = len(results_df)
    analysis_results = None

    if not results_df.empty:
        unique_results_df = results_df[
            results_df['profile_id'] != 0] if 'profile_id' in results_df.columns else results_df
        analysis_results = {
            "based_on": f"{len(unique_results_df.drop_duplicates(subset=['profile_id'])) if 'profile_id' in unique_results_df.columns else len(unique_results_df)} unique guests from {count} records",
            "age_distribution": _analyze_age(unique_results_df),
            "nationality_distribution": _analyze_nationality(unique_results_df),
            "gender_distribution": _analyze_gender(unique_results_df)
        }

    return {
        "count": count,
        "analysis": analysis_results
    }

@mcp.tool()
def find_related_guests_by_id(record_id: int) -> Dict[str, Any]:
    """
    通过单条记录的ID，查找所有关联的住客记录（如同一个预订下的家庭成员）。

    此工具用于当你已经知道一个住客的 `id`，并想查找与他/她住在同一个房间或
    在同一份合约下的所有其他人的情况。它通过匹配 `master_id` 来实现这一功能。

    Args:
        record_id (int): 数据库中任意一条住客记录的唯一 `id`。

    Returns:
        一个包含查询结果的字典对象，其结构如下:
        {
          "count": int,      // 找到的关联记录总数 (包含原始记录)
          "results": [       // 包含所有关联住客记录的列表
            {
              "id": int,
              "name": str,
              ...
            }
          ]
        }
    """
    # (Function implementation is the same)
    if main_df is None: return {"error": "数据未加载。", "count": 0, "results": []}
    target_master_id_series = main_df.loc[main_df['id'] == record_id, 'master_id']
    if not target_master_id_series.empty:
        target_master_id = target_master_id_series.iloc[0]
        results = main_df[main_df['master_id'] == target_master_id]
        return {"count": len(results), "results": format_df_for_output(results)}
    else:
        return {"count": 0, "results": []}


@mcp.tool()
def find_highest_rent_guest() -> Dict[str, Any]:
    """
    找出当前在住(In-House)的、支付月租金最高的住客。

    此工具用于快速定位当前最有价值的客户。它只考虑状态为 'I' (In-House) 的住客，
    并比较他们的 `full_rate_long` 字段。如果有多位住客支付相同的最高租金，
    此工具会返回所有这些住客。

    Returns:
        一个包含查询结果和元数据的字典，其结构如下:
        {
          "count": int,        // 找到的租金最高住客的数量
          "results": [         // 包含这些住客记录的列表
            {
              "id": int,
              "name": str,
              "full_rate_long": float,
              ...
            }
          ],
          "metadata": {        // 包含关于查询的额外信息
            "description": str,
            "highest_rent": float // 具体的最高租金金额
          }
        }
    """
    # (Function implementation is the same)
    if main_df is None: return {"error": "数据未加载。", "count": 0, "results": [], "metadata": None}
    in_house_df = main_df[main_df['sta'] == 'I']
    if in_house_df.empty: return {"count": 0, "results": [], "metadata": {"description": "当前无在住客人。"}}
    max_rent = in_house_df[in_house_df['full_rate_long'] > 0]['full_rate_long'].max()
    if pd.isna(max_rent): return {"count": 0, "results": [], "metadata": {"description": "在住客中未找到有效租金记录。"}}
    highest_rent_guests_df = in_house_df[in_house_df['full_rate_long'] == max_rent]
    return {
        "count": len(highest_rent_guests_df),
        "results": format_df_for_output(highest_rent_guests_df),
        "metadata": {
            "description": f"查询到 {len(highest_rent_guests_df)} 位住客拥有当前最高的月租金。",
            "highest_rent": float(max_rent)
        }
    }

# --- 1. 查询现在的系统时间 ---
@mcp.tool()
def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前系统时间，并按指定格式返回
    """
    return datetime.now().strftime(format_str)


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

@mcp.tool()
def financial_analyzer(need: str, time: str):
    """
    这是一个综合性的运营数据查询工具
    使用这个工具你需要选择两个参数
    首先是要查询的数据项，这个必须从下面给出的数据项中选择，每次只能选择一个
    能查询的数据项有：
        '入住率'
        '平均租金'
        '住宅总租金收入'
        '总收入'
        '人力成本'
        '维修维保费'
        '营销推广费'
        '行政及办公费用'
        '能耗费-公区'
        '能耗费-客房'
        '大物业管理费'
        '经营税金'
        '保险费'
        '总运营支出'
        '净营业收入'
        'NOI利润率'
    第二个是要查询的时间，把用户需要查询的时间以'YYYY-MM'的格式传入，每次只能传入一个时间

    使用示例：
        假设我要查询2025年5月的入住率
        执行查询
        print(financial_analyzer("入住率", "2025-05"))
        让后就可得到结果：查询结果: '开业首年_8月' 的 '入住率' 为 56.00%

    """


    file_path = '北京中天创业园_月度数据表.csv'
    analyzer = ProjectFinancials(file_path)
    result = analyzer.get_data(metric=need, time_period=time)
    return result


# --- 5. 服务器启动入口 (No changes here) ---
if __name__ == "__main__":
    main_df = load_data(CSV_FILE_PATH)
    print(financial_analyzer("入住率", "开业首年_8月"))
    if main_df is not None:
        print("数据服务已准备就绪。正在启动 MCP 服务器...")
        #print(advanced_search(include_analysis=True, nation="日本"))
        mcp.run(transport="sse")
    else:
        print("由于数据加载失败，服务器将不会启动。")
