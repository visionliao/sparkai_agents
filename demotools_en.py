import datetime
import pandas as pd
from typing import List, Union, Tuple
import re
import uvicorn
from typing import Optional, Dict, Any
from dateutil.relativedelta import relativedelta
from dateparser.date import DateDataParser
from dateparser.search import search_dates

from demo_en.calculate_occupancy import calculate_occupancy_rate, format_result_to_string
from demo_en.room import analyze_room_type_performance, format_analysis_to_string
from demo_en.query_guest_data import load_data_from_xml, get_multiple_query_results_as_string, load_status_rent_data_from_xml, get_guest_statistics, get_filtered_details_as_string
from demo_en.query_checkins import query_checkin_records, format_records_to_string
from demo_en.query_by_room import query_records_by_room, format_string
from demo_en.query_orders import parse_service_orders, search_by_rmno, format_results_string
from demo_en.advanced_query import parse_service_orders, search_orders_advanced, format_to_string, analyze_distribution, format_distribution_report, calculate_summaries, format_summary_report
from demo_en.generate_dashboard import main as generate_dashboard
from demo_en.query_by_room import query_nearby_rooms_status, format_nearby_status
from demo_en.apartment_query import ApartmentQueryTool

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Apartment Data Query")
TOOL = ApartmentQueryTool(filepath='demo_en/room_base_en.csv')

RMTYPE_MAPPING = {
    '1BD': "One Bedroom Deluxe",
    '1BP': "One Bedroom Premier",
    '2BD': "Two Bedrooms Executive",
    '3BR': "Three-bedroom",
    'STD': "Studio Deluxe",
    'STE': "Studio Executive",
    'STP': "Studio Premier"
}

# --- 1. 查询现在的系统时间 ---
@mcp.tool()
def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Get the current system time and return it in the specified format.
    """
    return datetime.datetime.now().strftime(format_str)


#@mcp.tool()
def get_required_date_range(time_description: str) -> str:
    """
    功能描述 (description):
    一个强大的自然语言时间解析器。它能从复杂的句子中智能提取出时间信息（如“上个月”、“8月份”、“本周”、“过去60天”），并将其转换为精确的“YYYY-MM-DD”格式的起止日期范围。

    【执行协议 (Execution Protocol)】:
    1.  **与核心准则 #5 联动**: 根据你的核心行为准则 #5，在处理数据查询时，你需要先制定并告知用户你的计划。
    2.  **计划的第一步**: 本工具是这个计划中【第一步的强制执行动作】。它的作用是为后续所有的数据查询步骤提供必需的、精确的时间范围。
    3.  **立即执行指令**: 因此，在你的回复中，**在“告知用户计划”之后，你【必须】在同一轮次的回复中立即调用本工具**，不能有任何停顿。

    【正确与错误的行为示例】:
    ---
    **场景:** 用户提问 "查询8月份的入住记录"

    ** 正确行为 (遵循协议):**
    1.  **你的回复 (告知计划):** "好的，我将为您查询8月份的入住记录。我的计划是：首先，确定8月的具体日期；然后，查询该时间段的入住记录..."
    2.  **你的行动 (立即调用):** (在同一回复中，紧接着生成工具调用)
        `get_required_date_range(time_description="8月份")`

    ** 错误行为 (违反协议):**
    1.  **你的回复 (告知计划后停止):** "好的，我将为您查询8月份的入住记录。我的计划是：..." (然后停止，等待用户)
    ---

    输入参数 (parameters):
    name: time_description
    type: string
    description: 用户的、可能包含复杂上下文的原始自然语言时间描述。例如: "查询8月整月的入住记录", "上个月的情况怎么样"。
    required: true

    返回结果 (returns):
    type: string
    description: 一个格式化的字符串，包含后续工具所需的精确起止日期。
    """
    try:
        now = datetime.datetime.now()

        # --- 提取信号，而非移除噪音 ---
        # 尝试从整个句子中找出描述日期的子字符串
        # 例如，从 "查询8月整月的入住记录" 中，它会找到 "8月"
        found_dates = search_dates(time_description, languages=['zh', 'en'])

        effective_description = time_description # 默认为原始输入
        if found_dates:
            # 如果找到了，就用找到的第一个日期子字符串作为我们的解析目标
            effective_description = found_dates[0][0]

        # 尝试用正则表达式解析精确的相对时间，如“过去30天”
        match_days = re.match(r"(?:过去|最近)\s*(\d+)\s*天", effective_description)
        match_months = re.match(r"(?:过去|最近)\s*(\d+)\s*个月", effective_description)

        if match_days:
            days = int(match_days.group(1))
            end_date = now.date()
            start_date = end_date - datetime.timedelta(days=days - 1)
            return f"已将'{time_description}'解析为具体时间段：开始日期 '{start_date.strftime('%Y-%m-%d')}'，结束日期 '{end_date.strftime('%Y-%m-%d')}'。"

        if match_months:
            months = int(match_months.group(1))
            end_date = now.date()
            start_date = end_date - relativedelta(months=months) + datetime.timedelta(days=1)
            return f"已将'{time_description}'解析为具体时间段：开始日期 '{start_date.strftime('%Y-%m-%d')}'，结束日期 '{end_date.strftime('%Y-%m-%d')}'。"

        # 使用强大的 dateparser 库进行通用解析
        d = DateDataParser(languages=['zh', 'en']).get_date_data(effective_description)

        if d and d.date_obj:
            parsed_date = d.date_obj.date()
            period = d.period

            start_date, end_date = None, None
            if period == 'month':
                start_date = parsed_date.replace(day=1)
                end_date = start_date + relativedelta(months=1) - datetime.timedelta(days=1)
            elif period == 'year':
                start_date = parsed_date.replace(month=1, day=1)
                end_date = parsed_date.replace(month=12, day=31)
            elif period == 'week':
                start_date = parsed_date - datetime.timedelta(days=parsed_date.weekday())
                end_date = start_date + datetime.timedelta(days=6)
            else:
                start_date = parsed_date
                end_date = parsed_date

            return f"已将'{time_description}'解析为具体时间段：开始日期 '{start_date.strftime('%Y-%m-%d')}'，结束日期 '{end_date.strftime('%Y-%m-%d')}'。"

        # 兜底机制: 如果以上所有智能方法都失败
        else:
            end_date = now.date()
            start_date = end_date - datetime.timedelta(days=6)
            return f"无法从'{time_description}'中解析出明确日期。已应用默认的最近7天范围：开始日期 '{start_date.strftime('%Y-%m-%d')}'，结束日期 '{end_date.strftime('%Y-%m-%d')}'。"

    except Exception as e:
        return f"解析时间'{time_description}'时发生内部错误: {e}"

# --- 2. 通用计算工具函数 ---
@mcp.tool()
def calculate_expression(expression: str) -> Any:
    """
    Tool Name (tool_name): calculate_expression
    Description: Executes a mathematical calculation provided as a string. Suitable for scenarios requiring addition, subtraction, multiplication, division, and parentheses.
    【IMPORTANT】: This tool is limited to basic mathematical operations (+, -, *, /, **) and a few safe functions (abs, max, min, pow, round). It cannot perform more complex algebraic or calculus operations.
    Parameters:
        name: expression
        type: string
        description: The mathematical expression to be calculated. For example: "10 * (5 + 3)".
        required: true
    Returns:
        type: number | string
        description: Returns the calculation result (numeric type). If the expression has a syntax error or a calculation error occurs (e.g., division by zero), it returns a string describing the error.
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
        return f"Calculation error: {e}"

# --- 3. 出租率工具函数 ---
@mcp.tool()
def calculate_occupancy(start: str, end: str, details: str = 'n'):
    """
    Description: A tool to get the occupancy and rental rates for a specified time period.

    Parameters:
        start (Optional[str]): The start date of the time range, must be in 'YYYY-MM-DD' format; e.g., '2025-05-01'.
        end (Optional[str]): The end date of the time range, must be in 'YYYY-MM-DD' format; e.g., '2025-05-01'.
        details (Optional[str]): Choose whether to get detailed records. Optional values are 'y'/'n'. Defaults to 'n'.


    Returns:
        Below is an example of a return value:
        calculate_occupancy("2025-08-01", "2025-08-05", "y")
        Returns:
        '
        --- Daily Occupancy and Booking Details ---
        Date: 2025-08-01 | Occupied Rooms: 150 | Booked Rooms: 0   | Occupancy Status Roomnights occ: 25.91% Application occ: 25.91%
        Date: 2025-08-02 | Occupied Rooms: 151 | Booked Rooms: 0   | Occupancy Status Roomnights occ: 26.08% Application occ: 26.08%
        Date: 2025-08-03 | Occupied Rooms: 151 | Booked Rooms: 0   | Occupancy Status Roomnights occ: 26.08% Application occ: 26.08%
        Date: 2025-08-04 | Occupied Rooms: 154 | Booked Rooms: 0   | Occupancy Status Roomnights occ: 26.60% Application occ: 26.60%
        Date: 2025-08-05 | Occupied Rooms: 155 | Booked Rooms: 0   | Occupancy Status Roomnights occ: 26.77% Application occ: 26.77%

        --- Calculation Results ---
        Query Range: 2025-08-01 to 2025-08-05 (5 days)
        Total Available Room Nights: 2,895
        Actual Occupied Room Nights: 761
        Booked Room Nights: 0
        ------------------
        --- Occupancy Status ---
        Roomnights occ (excluding contracted but not checked-in): 26.29%
        Application occ (including contracted but not checked-in): 26.29%
        ------------------
        '
    """

    FILE_PATH = 'demo/master_base.xml'
    TOTAL_ROOMS = 579

    print("--- Occupancy Rate Calculation ---")

    # 验证日期格式
    try:
        datetime.datetime.strptime(start, '%Y-%m-%d')
        datetime.datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        return "Input error: Incorrect date format. Please use 'YYYY-MM-DD' format."

    start_input = start
    end_input = end
    details_input = details.lower()

    show_details_flag = True if details_input == 'y' else False

    # 函数现在返回两个值：一个字典（数据）和一个字符串（日志）
    result_dict, details_string = calculate_occupancy_rate(
        FILE_PATH, start_input, end_input, TOTAL_ROOMS, show_details=show_details_flag
    )

    # 检查是否有错误发生
    if result_dict is None:
        # 如果出错，details_string 会包含错误信息
        return details_string
    else:
        # --- 将所有输出格式化并存入一个字符串变量 ---
        final_report_string = format_result_to_string(result_dict, details_string)

        return final_report_string


@mcp.tool()
def occupancy_details(start_time: str, end_time: str) -> str:
    """
    description: A tool to retrieve the rental performance (rent, efficiency, vacancy rate) of different room types within a specified time period. It also provides the highest and lowest rent for each room type, along with the corresponding booking ID.

    parameters:
    start_time (Optional[str]): The start date of the time period, must be in YYYY-MM-DD format; for example: '2025-05-01'
    end_time (Optional[str]): The end date of the time period, must be in YYYY-MM-DD format; for example: '2025-05-01'

    returns:
    Below is an example of the returned output for a call:
    occupancy_details("2025-08-01", "2025-08-31")
    Returns:
    '
    --- Room Type Performance Analysis (Period: 2025-08-01 to 2025-08-31) ---

    ==================== Room Type: One-Bedroom Deluxe ====================
    End-of-Period Supply & Occupancy: Total 150 rooms, Occupied 58, of which 58 are paid
    End-of-Period Vacancy Rate   : 61.33%
    ---
    Period Room Nights    : Total Occupied 1,610 nights, Total Paid 1,610 nights
    Period Vacancy Rate : 65.38%
    ---
    Period Revenue      : Total Rent 718,410.88, Avg Daily Rate 446.22, Avg Monthly (30-day) 13,386.54
    Efficiency          : 6.11 per m²/day (based on area of 73 m²)
    ---
    Highest Monthly Rent: 21,029.00 (Booking ID: 2773, Arrival: 2025-01-06, Departure: 2026-01-06)
    Lowest Monthly Rent : 8,250.00 (Booking ID: 2911, Arrival: 2025-05-27, Departure: 2026-05-27)

    ==================== Room Type: One-Bedroom Premier ====================
    End-of-Period Supply & Occupancy: Total 19 rooms, Occupied 6, of which 6 are paid
    End-of-Period Vacancy Rate   : 68.42%
    ---
    Period Room Nights    : Total Occupied 186 nights, Total Paid 186 nights
    Period Vacancy Rate : 68.42%
    ---
    Period Revenue      : Total Rent 114,002.29, Avg Daily Rate 612.92, Avg Monthly (30-day) 18,387.47
    Efficiency          : 6.96 per m²/day (based on area of 88 m²)
    ---
    Highest Monthly Rent: 24,000.00 (Booking ID: 3385, Arrival: 2025-07-22, Departure: 2026-07-22)
    Lowest Monthly Rent : 12,484.80 (Booking ID: 2867, Arrival: 2025-03-04, Departure: 2026-03-04)

    ==================== Room Type: Two-Bedroom Deluxe ====================
    End-of-Period Supply & Occupancy: Total 15 rooms, Occupied 3, of which 3 are paid
    End-of-Period Vacancy Rate   : 80.00%
    ---
    Period Room Nights    : Total Occupied 68 nights, Total Paid 68 nights
    Period Vacancy Rate : 85.38%
    ---
    Period Revenue      : Total Rent 53,570.00, Avg Daily Rate 787.79, Avg Monthly (30-day) 23,633.82
    Efficiency          : 7.29 per m²/day (based on area of 108 m²)
    ---
    Highest Monthly Rent: 24,220.00 (Booking ID: 3311, Arrival: 2025-07-15, Departure: 2026-07-15)
    Lowest Monthly Rent : 20,160.00 (Booking ID: 3677, Arrival: 2025-08-26, Departure: 2025-10-13)

    ==================== Room Type: Three-Bedroom ====================
    End-of-Period Supply & Occupancy: Total 1 rooms, Occupied 0, of which 0 are paid
    End-of-Period Vacancy Rate   : 100.00%
    ---
    Period Room Nights    : Total Occupied 0 nights, Total Paid 0 nights
    Period Vacancy Rate : 100.00%
    ---
    Period Revenue      : Total Rent 0.00, Avg Daily Rate 0.00, Avg Monthly (30-day) 0.00
    Efficiency          : 0.00 per m²/day (based on area of 134 m²)
    ---
    Highest Monthly Rent: N/A (No paid records in period)
    Lowest Monthly Rent : N/A (No paid records in period)

    ==================== Room Type: Studio Deluxe ====================
    End-of-Period Supply & Occupancy: Total 22 rooms, Occupied 7, of which 7 are paid
    End-of-Period Vacancy Rate   : 68.18%
    ---
    Period Room Nights    : Total Occupied 160 nights, Total Paid 160 nights
    Period Vacancy Rate : 76.54%
    ---
    Period Revenue      : Total Rent 37,177.47, Avg Daily Rate 232.36, Avg Monthly (30-day) 6,970.78
    Efficiency          : 5.16 per m²/day (based on area of 45 m²)
    ---
    Highest Monthly Rent: 8,530.00 (Booking ID: 2507, Arrival: 2024-11-05, Departure: 2025-11-05)
    Lowest Monthly Rent : 5,050.20 (Booking ID: 2940, Arrival: 2025-04-01, Departure: 2026-04-01)

    ==================== Room Type: Studio Executive ====================
    End-of-Period Supply & Occupancy: Total 360 rooms, Occupied 119, of which 117 are paid
    End-of-Period Vacancy Rate   : 66.94%
    ---
    Period Room Nights    : Total Occupied 3,152 nights, Total Paid 3,100 nights
    Period Vacancy Rate : 71.76%
    ---
    Period Revenue      : Total Rent 850,342.33, Avg Daily Rate 274.30, Avg Monthly (30-day) 8,229.12
    Efficiency          : 4.57 per m²/day (based on area of 60 m²)
    ---
    Highest Monthly Rent: 13,705.00 (Booking ID: 2849, Arrival: 2025-02-26, Departure: 2026-02-26)
    Lowest Monthly Rent : 6,600.00 (Booking ID: 3232, Arrival: 2025-06-07, Departure: 2026-06-07)

    ==================== Room Type: Studio Premier ====================
    End-of-Period Supply & Occupancy: Total 12 rooms, Occupied 1, of which 1 are paid
    End-of-Period Vacancy Rate   : 91.67%
    ---
    Period Room Nights    : Total Occupied 31 nights, Total Paid 31 nights
    Period Vacancy Rate : 91.67%
    ---
    Period Revenue      : Total Rent 7,192.00, Avg Daily Rate 232.00, Avg Monthly (30-day) 6,960.00
    Efficiency          : 3.46 per m²/day (based on area of 67 m²)
    ---
    Highest Monthly Rent: 6,960.00 (Booking ID: 3267, Arrival: 2025-06-15, Departure: 2026-06-15)
    Lowest Monthly Rent : 6,960.00 (Booking ID: 3267, Arrival: 2025-06-15, Departure: 2026-06-15)

    ==================== Overall Summary ====================
    Overall Avg Daily Rate (All Types): 345.43 (based on 5,155 total paid room nights)
    Overall Efficiency (All Types)  : 5.29 per m²/day (based on total rent / total paid area nights)
    ========================================================
    '
    """

    # 各户型的总房间数 (户型代码: 数量)
    ROOM_TYPE_COUNTS = {
        '1BD': 150,
        '1BP': 19,
        '2BD': 15,
        '3BR': 1,
        'STD': 22,
        'STE': 360,
        'STP': 12
    }

    # 各户型的平均面积 (单位: 平方米) (户型代码: 面积)
    ROOM_TYPE_AREAS = {
        '1BD': 73,
        '1BP': 88,
        '2BD': 108,
        '3BR': 134,
        'STD': 45,
        'STE': 60,
        'STP': 67
    }

    # 各户型代码到具体名称的映射
    ROOM_TYPE_NAMES = {
        '1BD': "One Bedroom Deluxe",
        '1BP': "One Bedroom Premier",
        '2BD': "Two Bedrooms Executive",
        '3BR': "Three-bedroom",
        'STD': "Studio Deluxe",
        'STE': "Studio Executive",
        'STP': "Studio Premier"
    }

    FILE_PATH = 'demo_en/master_base.xml'
    # print("--- 户型经营表现分析工具 ---")

    # 验证日期格式
    try:
        datetime.datetime.strptime(start_time, '%Y-%m-%d')
        datetime.datetime.strptime(end_time, '%Y-%m-%d')
    except ValueError:
        return "Input error: The date format is incorrect. Please use the 'YYYY-MM-DD' format."

    start_date_input = start_time
    end_date_input = end_time

    # 1. 调用计算函数，获取原始数据结果
    results_list = analyze_room_type_performance(
        FILE_PATH,
        start_date_input,
        end_date_input,
        ROOM_TYPE_COUNTS,
        ROOM_TYPE_AREAS
    )

    # 2. 调用格式化函数，将结果存入字符串变量
    final_report_string = format_analysis_to_string(
        results_list,
        start_date_input,
        end_date_input,
        ROOM_TYPE_NAMES
    )

    # 3. 打印字符串变量
    return final_report_string


@mcp.tool()
def query_guest(id: Union[str, List[str]]):
    """
    Function Description (description): A function used to retrieve user information for the specified user ID(s).

    Input Parameters (parameters):
    id (Union[str, List[str]]): User ID(s). You can use IDs obtained from other tools such as occupancy_details.
    Example: '3664' or '3664, 3694' (to query multiple IDs simultaneously) or ['3664', '3694'].

    Return Result (returns):
    Below is an example of a function call and its return value:
    query_guest("3664, 999")
    Returns:
    '
    --- Core data for ID: 3664 ---
    Primary ID     : 3664
    Customer Profile ID: 2522
    Name           : 晏**
    Inferred Gender: Male
    Date of Birth  : 2003-11-02 01:00:00.000002931
    Language Code  : C
    Mobile         : [Empty]
    Email          : 1**********@163.com
    Nationality Code: CN
    Country Code   : CN
    Province/State Code: JX
    Street Address : 江***
    ID Type Code   : 01
    ID Number      : 3****************2
    Hotel ID       : 11
    Customer Profile Type: GUEST
    Number of Stays: 0
    Remark         : 马总朋友，IT协助项目
    Created By     : JACQUELINELIANG
    Creation Time  : 2025-08-11 16:38:58.999997751
    Modified By    : JACQUELINELIANG
    Modification Time: 2025-09-10 15:30:30.000004081
    Stay Status    : I
    Room Number    : A212
    Monthly Rent   : 0
    Arrival Date   : 2025-08-11 16:41:16.999996064
    Departure Date : 2025-10-10 13:59:59.999997068
    ----------------------------

    ============================================================

    --- Record with ID 999 not found ---
    '
    """

    XML_FILE_PATH = 'demo/master_guest.xml'
    XML_STATUS_RENT_PATH = 'demo/master_base.xml'

    guest_df = load_data_from_xml(XML_FILE_PATH)

    if guest_df is not None:
        # 2. 加载状态和租金数据
        status_rent_df = load_status_rent_data_from_xml(XML_STATUS_RENT_PATH)

        # 3. 如果两者都成功加载，则合并数据
        if status_rent_df is not None:
            # 在合并前确保 'id' 列类型一致，避免潜在问题
            guest_df['id'] = pd.to_numeric(guest_df['id'], errors='coerce')
            status_rent_df['id'] = pd.to_numeric(status_rent_df['id'], errors='coerce')

            # print(f"\n正在合并数据...")
            # 使用 left join，保留所有主客户信息，即使没有租金/状态记录
            merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
            #print("数据合并完成。")
        else:
            merged_df = guest_df
            # print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

    final_id_list: List[str] = []
    if isinstance(id, list):
        final_id_list = [str(item).strip() for item in id if str(item).strip()]
    elif isinstance(id, str):
        final_id_list = [item.strip() for item in re.split(r'[\s,]+', id) if item.strip()]

    if not final_id_list:
        return "Input error: Failed to parse a valid user ID from the input."

    if merged_df is not None:
        result_variable = get_multiple_query_results_as_string(merged_df, ','.join(
            final_id_list))  # get_multiple_query_results_as_string expects a comma-separated string

        return result_variable


@mcp.tool()
def query_checkins(start: str, end: str, choice: str = 'ALL'):
    """
    Function Description (description): A function used to retrieve check-in information within a specified time range. The available fields include: check-in date, check-out date, room number, room type, rental fee, status, user ID, remarks, and shift information.
    Input Parameters (parameters):
    start (Optional[str]): The start date of the time range, formatted as YYYY-MM-DD; for example: '2025-05-01'.
    end (Optional[str]): The end date of the time range, formatted as YYYY-MM-DD; for example: '2025-05-01'.
    choice (Optional[str]): The check-in status to query. Available options are:
    '1': I (Checked-in), '2': O (Checked-out), '3': X (Cancelled), '4': R (Reserved), '5': ALL (All statuses, default).
    The default value is 'ALL'.

    Return Result (returns):
    Below is an example of a function call and its return value:
    query_checkins('2025-08-08', '2025-08-12', '1')
    Returns:
    '
    --- Check-in Records Query Results (2025-08-08 to 2025-08-12, Status: I) ---
    Found 7 (deduplicated) records for rooms.

    Arrival Date Departure Date Room No.          Room Type All Associated User IDs      Rent Status                                Remark Handover Info
      2025-08-08     2026-08-08     A608   Studio Executive                    3548  7,011.00      I 年租押二付一/已经支付了11685元的押金/8.8办理入住/包500元水电
      2025-08-09     2025-11-09    B1510 One Bedroom Deluxe                    3617 10,800.00      I
      2025-08-10     2026-08-10    A1008   Studio Executive                    3575  6,600.00      I                   POA11000/月 押2付1 6+6
      2025-08-11     2025-10-11    A1105   Studio Executive              3663, 3734  7,984.20      I                         POA13307 押一付一
      2025-08-11     2025-10-10     A212   Studio Executive                    3664      0.00      I                           马总朋友，IT协助项目
      2025-08-11     2025-11-11     A515   Studio Executive                    3642  8,383.20      I         客户押一付一/已支付一个月押金13972元/带一只小狗入住
      2025-08-12     2026-08-12    A1723 One Bedroom Deluxe                    3660 11,192.40      I                          18654/月，押二付一

    --------------------------------------------------------------------------------
    '
    """
    FILE_PATH = 'demo/master_base.xml'
    # 各户型代码到具体名称的映射
    ROOM_TYPE_NAMES = {
        '1BD': "One Bedroom Deluxe",
        '1BP': "One Bedroom Premier",
        '2BD': "Two Bedrooms Executive",
        '3BR': "Three-bedroom",
        'STD': "Studio Deluxe",
        'STE': "Studio Executive",
        'STP': "Studio Premier"
    }
    # 验证日期格式
    try:
        datetime.datetime.strptime(start, '%Y-%m-%d')
        datetime.datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        return "Input error: The date format is incorrect, please use the 'YYYY-MM-DD' format."

    start_input = start
    end_input = end

    # print(" 1: I (在住) 2: O (结帐) 3: X (取消) 4: R (预订) 5: ALL (所有状态，默认)")
    status_choice = choice

    status_map = {'1': 'I', '2': 'O', '3': 'X', '4': 'R', '5': 'ALL'}
    selected_status = status_map.get(status_choice, 'ALL')

    found_records = query_checkin_records(FILE_PATH, start_input, end_input, status_filter=selected_status)

    final_report_string = format_records_to_string(found_records, start_input, end_input, ROOM_TYPE_NAMES,
                                                   status_filter=selected_status)

    return final_report_string


@mcp.tool()
def query_by_room(rooms: Union[str, List[str]]):
    """
    Function Description (description): A function used to retrieve the historical check-in information for specified room numbers. The available fields include: **check-in date**, **check-out date**, **room number**, **room type**, **rental fee**, **status**, **user ID**, **remarks**, and **shift information**.

    Input Parameters (parameters):
    rooms (Union[str, List[str]]): One or more room numbers to query.
    Recommended standard format (list): `["A312", "A313", "B1510"]`
    Compatible format (string): `"A312"`

    Return Result (returns):
    Below is an example of a function call and its return value:
    query_by_room("A312,A313")
    Returns:
    '
    --- Room Number/Floor Pattern Query Results (A312, A313) ---
    Found 2 relevant records.

    Arrival Date Departure Date Room No.        Room Type     Rent Status  User ID            Remark Handover Info
      2025-06-16     2025-09-16     A313 Studio Executive 9,021.00      I     3296 客户预计需要租赁1个月+15天左右
      2025-06-16     2025-09-16     A313 Studio Executive     0.00      I     3356

    --------------------------------------------------------------------------------
    """

    FILE_PATH = 'demo/master_base.xml'
    # 各户型代码到具体名称的映射
    ROOM_TYPE_NAMES = {
        '1BD': "One Bedroom Deluxe",
        '1BP': "One Bedroom Premier",
        '2BD': "Two Bedrooms Executive",
        '3BR': "Three-bedroom",
        'STD': "Studio Deluxe",
        'STE': "Studio Executive",
        'STP': "Studio Premier"
    }
    final_room_list: List[str] = []

    # 优先处理列表形式，这是我们引导模型生成的标准形式
    if isinstance(rooms, list):
        final_room_list = [str(item).strip() for item in rooms if str(item).strip()]

    # 兼容模型可能返回单个字符串的边缘情况
    elif isinstance(rooms, str):
        # 假设字符串只包含一个房间号，或用逗号/空格分隔的多个房间号
        final_room_list = [r.strip() for r in re.split(r'[\s,]+', rooms) if r.strip()]

    if not final_room_list:
        return "Input error: Failed to parse a valid room number from the input"
    # --- 输入处理结束 ---

    # 1. 调用查询函数 (使用处理后的干净列表)
    found_records = query_records_by_room(FILE_PATH, final_room_list)

    # 2. 调用格式化函数 (使用处理后的干净列表)
    final_report_string = format_string(
        found_records,
        final_room_list,
        ROOM_TYPE_NAMES
    )

    # 3. 打印结果
    return final_report_string


@mcp.tool()
def query_orders(room_number: str):
    """
    Function Description (description):
    A function used to retrieve the historical work order information for specified room numbers. The available fields include:
    work order ID, room number, service item, request description, specific location, priority, room entry instructions/precautions, service status, service personnel, handling result, creation time, and completion time.

    Input Parameters (parameters):
    room_number (str): One or more room numbers.
    Example: 'A513'
    Return Result (returns):

    Below is an example of a function call and its return:
    query_orders('A513')
    Returns:
    '
    --- Found 2 related work orders ---

    【Record 1】
      Order ID:             3658
      Room No.:             A215
      Service Item:         Drainage (B701)
      Specific Location:    None (No Code)
      Requirement Desc.:    卫生间洗脸盆开关故障
      Priority:
      Entry Guidelines:     None
      Service State:        O
      Service Staff:        leonhu
      Resolution:           修复
      Creation Time:        2025-07-28 17:10:25
      Completion Time:      2025-07-29 09:30:15
    -------------------------

    【Record 2】
      Order ID:             3661
      Room No.:             a215
      Service Item:         Other (B801)
      Specific Location:    Living Room (009)
      Requirement Desc.:    A215卫生间洗脸盆下水道塞子坏
      Priority:             低
      Entry Guidelines:     None
      Service State:        O
      Service Staff:        leonhu
      Resolution:           修复
      Creation Time:        2025-07-28 18:21:26
      Completion Time:      2025-07-28 18:26:54
    -------------------------
    '
    """

    XML_FILE_PATH = 'demo/lease_service_order.xml'

    all_orders_data = parse_service_orders(XML_FILE_PATH)
    if all_orders_data is None:
        return "Failed to load work order data"

    found_orders_for_room = search_by_rmno(all_orders_data, room_number)

    result_string = format_results_string(found_orders_for_room)
    return result_string


@mcp.tool()
def advanced_query_service(
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None,
        service_code: Optional[str] = None,
        location_code: Optional[str] = None
) -> str:
    """
    Function Description (description):
    A service function used to query historical work order information based on conditions such as time range, service item, and specific location.
    (The time range refers to the period during which the work order was initiated.)
    The available fields include: work order ID, room number, service item, specific location, request description, priority, entry instructions, service status, service personnel, handling result, creation time, and completion time.

    Input Parameters (parameters):
    start_date_str (Optional[str]): Start date, formatted as 'YYYY-MM-DD'.
    end_date_str (Optional[str]): End date, formatted as 'YYYY-MM-DD'.
    service_code (Optional[str]): Service item code (e.g., 'B501' for Power Socket). Default is None (no restriction).
    location_code (Optional[str]): Specific location code (e.g., '004' for Kitchen). Default is None (no restriction).

    Available service item codes and location codes:
    SERVICE_CODE_MAP = {
        'A01': 'Linen Change', 'A02': 'Furniture Cleaning', 'A03': 'Floor Cleaning', 'A04': 'Appliance Cleaning',
        'A05': 'Sanitary Ware Cleaning', 'A06': 'Guest Supplies Replacement', 'A07': 'Pest Control', 'B1001': 'Elevator',
        'B101': 'Refrigerator', 'B102': 'Microwave', 'B103': 'Dryer', 'B104': 'Television',
        'B105': 'Washing Machine', 'B106': 'Air Purifier', 'B107': 'Dehumidifier', 'B108': 'Range Hood',
        'B110': 'Electric Fan', 'B114': 'Heater', 'B117': 'Projector', 'B119': 'Screen',
        'B120': 'Water Heater', 'B121': 'Dishwasher', 'B122': 'Induction Cooker', 'B123': 'Oven',
        'B124': 'Exhaust Fan', 'B201': 'Smoke Detector', 'B202': 'Manual Alarm',
        'B203': 'Fire Sprinkler', 'B204': 'Emergency Fire Light', 'B301': 'Radiator', 'B302': 'Ventilation Duct',
        'B303': 'Air Conditioner', 'B401': 'Towel Rack', 'B402': 'Faucet', 'B403': 'Interior Door Handle/Lock',
        'B404': 'Window', 'B405': 'Hinge', 'B501': 'Power Socket', 'B502': 'Switch',
        'B503': 'Lighting Fixture', 'B504': 'Light Bulb', 'B505': 'Fly Killer Lamp', 'B506': 'Power Strip',
        'B601': 'Furniture', 'B602': 'Cabinet', 'B603': 'Ceiling', 'B604': 'Floor',
        'B605': 'Wall', 'B606': 'Blinds', 'B607': 'Skirting Board', 'B701': 'Drainage',
        'B702': 'Bathtub', 'B703': 'Mirror', 'B704': 'Tile', 'B705': 'Sink',
        'B706': 'Shower Head', 'B707': 'Toilet', 'B708': 'Washbasin', 'B801': 'Other',
        'B901': 'Network Equipment'
    }

    LOCATION_CODE_MAP = {
        '002': 'Bedroom',
        '004': 'Kitchen',
        '008': 'Bathroom',
        '009': 'Living Room',
        '001': 'Apartment Exterior',
        '003': 'Work Area Corridor',
        '005': 'Back-of-house Area',
        '006': 'Front-of-house Area',
        '011': 'Elevator Hall - Rear',
        '010': 'Elevator Hall - Front',
        '007': 'Parking Lot',
        '012': 'Fire Escape Staircase',
    }

    Return Result (returns):
    str: A formatted string containing all query results.
    If no results are found, a corresponding message will be returned.

    Below is an example of a function call and its return:
    advanced_query_service(start_date_str='2025-07-01', end_date_str='2025-07-02', service_code='B701')
    Returns:
    '''
    Query Criteria: Time Range: [2025-07-01 to 2025-07-02], Service items: [Drainage], Specific location: [Unlimited]--- Found 2 relevant service orders ---

    【Record 1】
      Room No.:     A303
      Service Item: Drainage (B701)
      Location:     N/A (No Code)
      Description:  浴室下水慢
      Created Time: 2025-07-01 10:31:12
      Completed Time: 2025-07-01 12:28:57
    -------------------------

    【Record 2】
      Room No.:     B911
      Service Item: Drainage (B701)
      Location:     N/A (No Code)
      Description:  浴室下水慢
      Created Time: 2025-07-01 12:12:09
      Completed Time: 2025-07-01 12:39:36
    -------------------------
    '''
    """
    XML_FILE_PATH = 'demo_en/lease_service_order.xml'
    SERVICE_CODE_MAP = {
        'A01': 'Linen Change', 'A02': 'Furniture Cleaning', 'A03': 'Floor Cleaning', 'A04': 'Appliance Cleaning',
        'A05': 'Sanitary Ware Cleaning', 'A06': 'Guest Supplies Replacement', 'A07': 'Pest Control', 'B1001': 'Elevator',
        'B101': 'Refrigerator', 'B102': 'Microwave', 'B103': 'Dryer', 'B104': 'Television',
        'B105': 'Washing Machine', 'B106': 'Air Purifier', 'B107': 'Dehumidifier', 'B108': 'Range Hood',
        'B110': 'Electric Fan', 'B114': 'Heater', 'B117': 'Projector', 'B119': 'Screen',
        'B120': 'Water Heater', 'B121': 'Dishwasher', 'B122': 'Induction Cooker', 'B123': 'Oven',
        'B124': 'Exhaust Fan', 'B201': 'Smoke Detector', 'B202': 'Manual Alarm',
        'B203': 'Fire Sprinkler', 'B204': 'Emergency Fire Light', 'B301': 'Radiator', 'B302': 'Ventilation Duct',
        'B303': 'Air Conditioner', 'B401': 'Towel Rack', 'B402': 'Faucet', 'B403': 'Interior Door Handle/Lock',
        'B404': 'Window', 'B405': 'Hinge', 'B501': 'Power Socket', 'B502': 'Switch',
        'B503': 'Lighting Fixture', 'B504': 'Light Bulb', 'B505': 'Fly Killer Lamp', 'B506': 'Power Strip',
        'B601': 'Furniture', 'B602': 'Cabinet', 'B603': 'Ceiling', 'B604': 'Floor',
        'B605': 'Wall', 'B606': 'Blinds', 'B607': 'Skirting Board', 'B701': 'Drainage',
        'B702': 'Bathtub', 'B703': 'Mirror', 'B704': 'Tile', 'B705': 'Sink',
        'B706': 'Shower Head', 'B707': 'Toilet', 'B708': 'Washbasin', 'B801': 'Other',
        'B901': 'Network Equipment'
    }
    LOCATION_CODE_MAP = {
        '002': 'Bedroom',
        '004': 'Kitchen',
        '008': 'Bathroom',
        '009': 'Living Room',
        '001': 'Apartment Exterior',
        '003': 'Work Area Corridor',
        '005': 'Back-of-house Area',
        '006': 'Front-of-house Area',
        '011': 'Elevator Hall - Rear',
        '010': 'Elevator Hall - Front',
        '007': 'Parking Lot',
        '012': 'Fire Escape Staircase',
    }

    ALL_ORDERS_DATA = parse_service_orders(XML_FILE_PATH)
    if ALL_ORDERS_DATA is None:
        return "Failed to load work order data"

    # --- 处理和验证输入 ---
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    except ValueError:
        return "Input error: The date format is incorrect, please use the 'YYYY-MM-DD' format."

    # --- 执行查询并格式化结果 ---
    found_orders = search_orders_advanced(ALL_ORDERS_DATA, start_date, end_date, service_code, location_code)

    # 构建查询条件描述字符串
    criteria_desc = (
        f"Time Range: [{start_date_str or 'Unlimited'} to {end_date_str or 'Unlimited'}], "
        f"Service items: [{SERVICE_CODE_MAP.get(service_code, 'Unlimited')}], "
        f"Specific location: [{LOCATION_CODE_MAP.get(location_code, 'Unlimited')}]"
    )

    return format_to_string(found_orders, criteria_desc)


@mcp.tool()
def query_distribution_report(
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None,
) -> str:
    """
    Function Description (description):
    Retrieves a summary report of work order statistics within a specified time period.

    Input Parameters (parameters):
    start_date_str (Optional[str]): Start date, formatted as 'YYYY-MM-DD'.
    end_date_str (Optional[str]): End date, formatted as 'YYYY-MM-DD'.

    Return Result (returns):
    str: A formatted string containing all query results.
    If no results are found, a corresponding message will be returned.

    Below is an example of a function call and its return:
    query_distribution_report(start_date_str='2025-07-01', end_date_str='2025-07-05')
    Returns:
    '''
    ==================================================

    --- Overall Data Summary ---

    Total Service Orders in Query Range: 14 orders


    --- Top 3 Service Items ---
      1. Unknown Code (): 5 times (35.7%)
      2. Faucet: 4 times (28.6%)
      3. Drainage: 2 times (14.3%)

    --- Top 3 Locations ---
      1. Unknown Location: 9 times (64.3%)
      2. Living Room: 5 times (35.7%)

    --- Top 3 Floor Distribution ---
      1. 5F: 5 times (35.7%)
      2. 12F: 2 times (14.3%)
      3. 6F: 2 times (14.3%)

    --- Top 3 Building Distribution ---
      1. A Block: 11 times (78.6%)
      2. B Block: 3 times (21.4%)

    ==================================================

    ==================================================
    --- Detailed Service Order Distribution Report ---

    [ Block: A Block ]
      [ Floor: 12F ]
        ● Location: Unknown Location
          - Unknown Code (): 1 times
      [ Floor: 2F ]
        ● Location: Living Room
          - Furniture: 1 times
      [ Floor: 3F ]
        ● Location: Unknown Location
          - Drainage: 1 times
      [ Floor: 5F ]
        ● Location: Unknown Location
          - Faucet: 2 times
          - Unknown Code (): 2 times
      [ Floor: 6F ]
        ● Location: Living Room
          - Other: 1 times
        ● Location: Unknown Location
          - Unknown Code (): 1 times
      [ Floor: 8F ]
        ● Location: Living Room
          - Faucet: 2 times

    [ Block: B Block ]
      [ Floor: 12F ]
        ● Location: Living Room
          - Other: 1 times
      [ Floor: 5F ]
        ● Location: Unknown Location
          - Unknown Code (): 1 times
      [ Floor: 9F ]
        ● Location: Unknown Location
          - Drainage: 1 times
    ==================================================
    '''
    """
    XML_FILE_PATH = 'demo_en/lease_service_order.xml'

    ALL_ORDERS_DATA = parse_service_orders(XML_FILE_PATH)
    if ALL_ORDERS_DATA is None:
        return "Failed to load work order data"

    # --- 处理和验证输入 ---
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    except ValueError:
        return "Input error: The date format is incorrect, please use the 'YYYY-MM-DD' format."

    found_orders = search_orders_advanced(ALL_ORDERS_DATA, start_date, end_date, None, None)

    distribution_data = analyze_distribution(found_orders)
    distribution_report = format_distribution_report(distribution_data)

    service_counts, location_counts, floor_counts, building_counts = calculate_summaries(found_orders)
    summary_report = format_summary_report(len(found_orders), service_counts, location_counts, floor_counts,
                                           building_counts)

    return summary_report+distribution_report


@mcp.tool()
def generate_dashboard_service():
    """
    Open a web data dashboard, and after calling it, you will receive a success message.
    """
    generate_dashboard()
    return "Dashboard successfully opened, please visit https://chatbot.sparkai.xin/ to check."


@mcp.tool()
def get_statistical_summary(
        name: Optional[str] = None,
        room_number: Optional[str] = None,
        gender: Optional[str] = None,
        status: Union[str, List[str]] = None,
        nation: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        min_rent: Optional[float] = None,
        max_rent: Optional[float] = None,
        start_arr_date: Optional[Any] = None,
        end_arr_date: Optional[Any] = None,
        remark_keyword: Optional[str] = None,
        room_type: Optional[Union[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Function Description
    Performs statistical analysis on guest stay data based on specified filter conditions.

    For example, this tool can be used to obtain statistics of currently staying guests in the apartment.

    Args:
    name (Optional[str]): Perform a fuzzy search by guest name.
    room_number (Optional[str]): Perform an exact match by room number.
    gender (Optional[str]): Filter by gender.Male or Female
    status (Union[str, List[str]]):
    Filter by guest status. Possible values include:
    'I' (In-House), 'R' (Reservation), 'O' (Checked-Out), 'X' (Cancelled), 'Currently residing on-site' (“Currently Staying”).
        Multiple values can be selected, e.g. status=['I', 'O'].
        Since the data source may be outdated, the number of guests actually staying may differ from the number of records with status 'I'.
        To obtain the current actual in-house statistics, use status='Currently residing on-site' (this parameter cannot be combined with others).
    nation (Optional[str]): Perform a fuzzy search by nationality.
    min_age (Optional[int]): Minimum guest age filter.
    max_age (Optional[int]): Maximum guest age filter.
    min_rent (Optional[float]): Minimum monthly rent filter.
    max_rent (Optional[float]): Maximum monthly rent filter.
    start_arr_date (Optional[Any]): Start date of the time period.
    end_arr_date (Optional[Any]): End date of the time period.
    remark_keyword (Optional[str]): Perform a fuzzy search in the remarks field.

    Returns:
    A dictionary object containing the statistical analysis results, with the following structure:
    {
      "count": int,  # Total number of records matching the conditions
      "analysis": None | {  # Present if results exist
          "based_on": str,  # Description of the independent guest base used for analysis
          "age_distribution": [{"group": str, "count": int, "percentage": str}],
          "nationality_distribution": [{"nation": str, "count": int, "percentage": str}],
          "gender_distribution": [{"gender": str, "count": int, "percentage": str}],
          "rent_analysis": [{"gender": str, "count": int, "percentage": str}]
      }
    }

    Example of invocation:
    Query various statistical data of current residents: get_statistical_summary(status = 'Currently residing on-site')
    Query the statistics of guests who newly checked in in September 2025: get_statistical_summary(status=['I','O','R'], start_arr_date='2025-09-01', end_arr_date='2025-09-30')
    Query the statistical data of current male residents who have pets: get_statistical_summary(gender='Male', status='Currently residing on-site', remark_keyword='宠物')
    Query statistical data of male residents, including the distribution of numbers by dimensions such as age and nationality: get_statistical_summary(gender='Male', status='Currently residing on-site')
    """
    guest_df = load_data_from_xml('demo/master_guest.xml')
    # 加载状态和租金数据
    status_rent_df = load_status_rent_data_from_xml('demo/master_base.xml')

    # 3. 如果状态租金数据成功加载，则执行合并
    if status_rent_df is not None:
        # 确保合并键的数据类型一致
        guest_df['profile_id'] = pd.to_numeric(guest_df['id'], errors='coerce')

        # print(f"\n正在合并数据...")
        # 使用左连接（left join）进行合并
        merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
        # print("数据合并完成。")
    else:
        # 如果第二个文件不存在或加载失败，则继续使用原始数据
        merged_df = guest_df
        # print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

    if 'rmtype' in merged_df.columns:
        print("正在将房间类型代码映射到中文名称...")
        # 使用 .map() 应用字典映射。对于不在字典中的 rmtype，使用 .fillna() 保留其原始值。
        merged_df['rmtype_name'] = merged_df['rmtype'].map(RMTYPE_MAPPING).fillna(merged_df['rmtype'])
        print("映射完成。")

    stats_result = get_guest_statistics(
        merged_df,
        name = name,
        room_number = room_number,
        gender = gender,
        status = status,
        nation = nation,
        min_age = min_age,
        max_age = max_age,
        min_rent = min_rent,
        max_rent = max_rent,
        start_arr_date = start_arr_date,
        end_arr_date = end_arr_date,
        remark_keyword = remark_keyword,
        room_type= room_type
    )

    return stats_result


@mcp.tool()
def get_filtered_details(
        name: Optional[str] = None,
        room_number: Optional[str] = None,
        gender: Optional[str] = None,
        status: Union[str, List[str]] = None,
        nation: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None,
        min_rent: Optional[float] = None,
        max_rent: Optional[float] = None,
        start_arr_date: Optional[Any] = None,
        end_arr_date: Optional[Any] = None,
        remark_keyword: Optional[str] = None,
        room_type: Optional[Union[str, List[str]]] = None
) -> str:
    """
    Retrieve a detailed list of guest personal information based on filter criteria.
    For example, you can use this function to obtain the complete detailed information of all guests currently staying whose monthly rent exceeds 10,000 yuan.

    Args:
    name (Optional[str]): Perform a fuzzy search by guest name.
    room_number (Optional[str]): Perform an exact match by room number.
    gender (Optional[str]): Filter by gender.Male or Female
    status (Union[str, List[str]]):
    Filter by guest status. Possible values include:
    'I' (In-House), 'R' (Reservation), 'O' (Checked-Out), 'X' (Cancelled), 'Currently residing on-site' (“Currently Staying”).
        Multiple values can be selected, e.g. status=['I', 'O'].
        Since the data source may be outdated, the number of guests actually staying may differ from the number of records with status 'I'.
        To obtain the current actual in-house statistics, use status='Currently residing on-site' (this parameter cannot be combined with others).
    nation (Optional[str]): Perform a fuzzy search by nationality.
    min_age (Optional[int]): Minimum guest age filter.
    max_age (Optional[int]): Maximum guest age filter.
    min_rent (Optional[float]): Minimum monthly rent filter.
    max_rent (Optional[float]): Maximum monthly rent filter.
    start_arr_date (Optional[Any]): Start date of the time period.
    end_arr_date (Optional[Any]): End date of the time period.
    remark_keyword (Optional[str]): Perform a fuzzy search in the remarks field.

    Returns:
    Function Description (String Output)
        A single string (str) containing the detailed information of all guests that match the filter conditions.
        Structure of the String:
        The string starts with a header showing the total count of matching records.
        Each guest's information is formatted similarly to the result of a single ID query.
        Guest information is separated by a prominent delimiter (e.g., "==================================================").
        If no records are found, a message such as "--- No matching guest records found ---" will be returned.

    Example of invocation:
    Query a detailed list of all current residents whose remarks contain 'pet': get_filtered_details(status='Currently residing on-site', remark_keyword='宠物')
    Query the detailed information list of all tenants with a monthly rent higher than 10,000 yuan: get_filtered_details(min_rent=10000.0,status='Currently residing on-site')
    Query detailed information of all guests with nationality 'USA': get_filtered_details(nation='USA',status='Currently residing on-site')
    """
    guest_df = load_data_from_xml('demo_en/master_guest.xml')
    # 加载状态和租金数据
    status_rent_df = load_status_rent_data_from_xml('demo_en/master_base.xml')

    # 3. 如果状态租金数据成功加载，则执行合并
    if status_rent_df is not None:
        # 确保合并键的数据类型一致
        guest_df['profile_id'] = pd.to_numeric(guest_df['id'], errors='coerce')

        # print(f"\n正在合并数据...")
        # 使用左连接（left join）进行合并
        merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
        # print("数据合并完成。")
    else:
        # 如果第二个文件不存在或加载失败，则继续使用原始数据
        merged_df = guest_df
        # print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

    if 'rmtype' in merged_df.columns:
        print("正在将房间类型代码映射到中文名称...")
        # 使用 .map() 应用字典映射。对于不在字典中的 rmtype，使用 .fillna() 保留其原始值。
        merged_df['rmtype_name'] = merged_df['rmtype'].map(RMTYPE_MAPPING).fillna(merged_df['rmtype'])
        print("映射完成。")

    details_string_result = get_filtered_details_as_string(
        merged_df,
        name = name,
        room_number = room_number,
        gender = gender,
        status = status,
        nation = nation,
        min_age = min_age,
        max_age = max_age,
        min_rent = min_rent,
        max_rent = max_rent,
        start_arr_date = start_arr_date,
        end_arr_date = end_arr_date,
        remark_keyword = remark_keyword,
        room_type=room_type
    )

    return details_string_result


@mcp.tool()
def nearby_report(room: Optional[str]):
    """
    Function Description
    A tool to retrieve the stay status of rooms surrounding a specified room number. The detailed fields include: check-in date, check-out date, room number, room type, rent, user ID, remarks, and handover information.

    Args:
    room (Optional[str]): The room number to query.
    Compatible format (string): "A312"

    Returns:
    Here’s an example of the return when calling the function:
    nearby_report("A1608")
    Return:
    '
    --- Nearby Room Occupancy Status for Room A1608 (2025-11-12) ---

      - Room A1608: [Occupied (I)]
        Guest ID:    3605
        Stay Period: 2025-09-09 to 2026-01-15
        Room Type:   Studio Executive
        Stay Type:   Long Stay
        Rent:        7,500.00

      - Room A1607: [Occupied (I)]
        Guest ID:    3804
        Stay Period: 2025-09-10 to 2025-12-20
        Room Type:   Studio Executive
        Stay Type:   Long Stay
        Rent:        7,512.60
        Remark:      3个月零10天/押一付一
      - Room A1609: [Currently Vacant]
      - Room A1708: [Currently Vacant]
      - Room A1508: [Currently Vacant]
      - Room A1507: [Currently Vacant]
      - Room A1509: [Currently Vacant]
      - Room A1707: [Currently Vacant]
      - Room A1709: [Currently Vacant]
    '
    Status corresponds to I (Checked In) O (Checked Out) X (Cancelled) R (Reserved)
    """
    FILE_PATH = 'demo_en/master_base.xml'
    # 优先处理列表形式，这是我们引导模型生成的标准形式
    if isinstance(room, list):
        final_room_list = [str(item).strip() for item in room if str(item).strip()]

    # 兼容模型可能返回单个字符串的边缘情况
    elif isinstance(room, str):
        # 假设字符串只包含一个房间号，或用逗号/空格分隔的多个房间号
        final_room_list = [r.strip() for r in re.split(r'[\s,]+', room) if r.strip()]

    if not final_room_list:
        return "Input error: failed to parse a valid room number from the input"

    nearby_query_result = query_nearby_rooms_status(FILE_PATH, room)
    nearby_report = format_nearby_status(nearby_query_result, room)

    return nearby_report

@mcp.tool()
def find_apartments(
        room_number: Optional[str] = None,
        building: Optional[List[str]] = None,
        room_type: Optional[List[str]] = None,
        orientation: Optional[List[str]] = None,
        floor_range: Optional[Tuple[int, int]] = None,
        area_range: Optional[Tuple[float, float]] = None,
        price_range: Optional[Tuple[float, float]] = None,
        lease_term: str = '12个月及以上',
        sort_by: str = 'price',
        sort_order: str = 'asc',
        aggregation: Optional[str] = None,
        limit: int = 10,
        return_fields: Optional[List[str]] = None
) -> dict:
    """
    Function Description
    Queries basic information about apartment rooms, including room area, orientation, room type, reference rent, and other room details that match the specified query conditions.

    Args:
    room_number (str, optional): The exact room number to query (e.g., 'A1001').
    building (list[str], optional): The building(s) (e.g., ['A', 'B']). Input is case-insensitive and trims leading/trailing spaces.
    room_type (list[str], optional): The room type(s) (e.g., ['Studio Executive', 'One Bedroom Deluxe']). Supports fuzzy matching.
    orientation (list[str], optional): The orientation(s) (e.g., ['South', 'South East']).
    floor_range (tuple[int, int], optional): The floor range (min_floor, max_floor).
    area_range (tuple[float, float], optional): The area range (min_area, max_area) in square meters.
    price_range (tuple[float, float], optional): The reference price range (min_price, max_price).
    lease_term (str, optional): The lease term for reference price. Defaults to '12 months and above'. Optional values: '12 months and above', '6-11 months', '2-5 months', '1 month'.
    sort_by (str, optional): Sorting criterion. Defaults to 'price'. Optional values: 'price', 'area', 'floor'.
    sort_order (str, optional): Sorting order. Defaults to 'asc' (ascending). Optional values: 'asc', 'desc'.
    aggregation (str, optional): Aggregation operation. If 'count', only the total number is returned.
    limit (int, optional): The maximum number of results to return. Defaults to 10.
    return_fields (list[str], optional): List of specific fields to return.
        If None, all default fields are returned.
        Optional fields: 'Room_number', 'Building_code', 'Floor', 'Room_type', 'Area (square meters)', 'Orientation', 'Reference rent', 'Rent Explanation'.

    Returns:
    dict: A dictionary containing the query results:
    When aggregation='count':
    {'count': X}
    On success:
    {'total_found': Y, 'displaying': Z, 'apartments': [list of apartments]}
    On failure:
    {'error': 'Specific error message'}

    Example of invocation:
    Check the 5 south-facing 'Studio Executive' with the lowest reference prices: find_apartments(room_type=['Studio Executive'],orientation=['South', 'South East', 'South West'],sort_by='price',sort_order='asc',limit=5)
    Search for a 'one-bedroom' apartment in Building A, above the 15th floor, facing south, with an annual rent under 25,000, and the largest area, and only provide information on the room, reference rent, area, and orientation: find_apartments(building=['A'],floor_range=(15, 100),orientation=['South'],room_type=['One Bedroom'],price_range=(0, 25000),lease_term='12 months and above',sort_by='area',sort_order='desc',return_fields = ['Room_number', 'Area (square meters)', 'Reference rent', 'Orientation'])
    """
    if TOOL.df.empty:
        return {"error": "The query tool failed to initialize. Please check the CSV file path or content."}

    query_params = locals()

    print(f"--- 正在执行查询 (参数: {query_params}) ---")

    # 将打包好的参数字典传递给查询工具
    results = TOOL.query(**query_params)

    return results


if __name__ == "__main__":
    app_instance = mcp.sse_app

    print(get_statistical_summary(status = 'Currently residing on-site', room_type = 'Studio Executive'))
    generate_dashboard()

    # 定义使用的主机和端口
    host = "127.0.0.1"
    port = 8000

    print(f"Starting server with SSE transport on http://{host}:{port}")

    # 使用 uvicorn.run() 来启动服务
    uvicorn.run(
        app=app_instance,
        host=host,
        port=port
    )