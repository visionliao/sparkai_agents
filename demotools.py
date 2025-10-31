import os
import datetime
import pandas as pd
from typing import List, Any, Union, Optional
import re
import uvicorn
from typing import Optional, Dict, Any
from dateutil.relativedelta import relativedelta
from dateparser.date import DateDataParser
from dateparser.search import search_dates

from demo.calculate_occupancy import calculate_occupancy_rate, format_result_to_string
from demo.room import analyze_room_type_performance, format_analysis_to_string
from demo.query_guest_data import load_data_from_xml, get_multiple_query_results_as_string, load_status_rent_data_from_xml, get_guest_statistics, get_filtered_details_as_string
from demo.query_checkins import query_checkin_records, format_records_to_string
from demo.query_by_room import query_records_by_room, format_string
from demo.query_orders import parse_service_orders, search_by_rmno, format_results_string
from demo.advanced_query import parse_service_orders, search_orders_advanced, format_to_string, analyze_distribution, format_distribution_report, calculate_summaries, format_summary_report
from demo.generate_dashboard import main as generate_dashboard
from demo.query_by_room import query_nearby_rooms_status, format_nearby_status

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("公寓数据查询")

# --- 1. 查询现在的系统时间 ---
@mcp.tool()
def get_current_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前系统时间，并按指定格式返回

    返回结果 (returns):
    下面是一个调用返回示例：
    get_current_time()
    返回：
    2025-10-22 16:24:21
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

# --- 3. 出租率工具函数 ---
@mcp.tool()
def calculate_occupancy(start: str, end: str, details: str = 'n'):
    """
    功能描述 (description): 一个用于获取指定时间内的入住率以及出租率的工具

    输入参数 (parameters):
    start (Optional[str]): 时间区间起点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
    end (Optional[str]): 时间区间终点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
    details (Optional[str]): 选择是否获取详细的记录，可选值为'y'/'n'，默认为 'n',选择详细记录可查看每天当天在租房间数

    返回结果 (returns):
    下面是一个调用返回示例：
    calculate_occupancy("2025-08-01", "2025-08-05", "y")
    返回：
    '
    --- 每日入住与预定详情 ---
    日期: 2025-08-01 | 在住房间数: 150 | 预定房间数: 0   | 出租情况 Roomnights occ: 25.91% Application occ: 25.91%
    日期: 2025-08-02 | 在住房间数: 151 | 预定房间数: 0   | 出租情况 Roomnights occ: 26.08% Application occ: 26.08%
    日期: 2025-08-03 | 在住房间数: 151 | 预定房间数: 0   | 出租情况 Roomnights occ: 26.08% Application occ: 26.08%
    日期: 2025-08-04 | 在住房间数: 154 | 预定房间数: 0   | 出租情况 Roomnights occ: 26.60% Application occ: 26.60%
    日期: 2025-08-05 | 在住房间数: 155 | 预定房间数: 0   | 出租情况 Roomnights occ: 26.77% Application occ: 26.77%

    --- 计算结果 ---
    查询范围: 2025-08-01 到 2025-08-05 (5 天)
    总可用房晚数: 2,895
    实际入住房晚数: 761
    预定房晚数: 0
    ------------------
    --- 出租情况 ---
    Roomnights occ (不包含签约但未入住): 26.29%
    Application occ (包含签约但未入住): 26.29%
    ------------------
    '
    """

    FILE_PATH = 'demo/master_base.xml'
    TOTAL_ROOMS = 579

    print("--- 入住率计算 ---")

    # 验证日期格式
    try:
        datetime.datetime.strptime(start, '%Y-%m-%d')
        datetime.datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        return "输入错误：日期格式不正确，请使用 'YYYY-MM-DD' 格式。"

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
        功能描述 (description): 一个用于获取指定时间段内的不同房型型的出租情况（租金，坪效，空置率）的工具，同时还可获得不同房型的最高租金与最低租金，以及对应的用户ID

        输入参数 (parameters):
        start_time (Optional[str]): 时间区间起点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
        end_time (Optional[str]): 时间区间终点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'

        返回结果 (returns):
        下面是一个调用返回示例：
        occupancy_details("2025-08-01", "2025-08-31")
        返回：
        '
        --- 各户型经营表现分析 (数据范围: 2025-08-01 至 2025-08-31) ---

        ==================== 户型: 一房豪华式公寓 ====================
        期末供应与占用: 总数 150 间, 期末在租 58 间(包括已预订房间)，其中期末付费 58 间
        期末空置率    : 61.33%
        ---
        期间房晚数    : 总入住房晚数 1,610 晚, 总付费房晚数 1,610 晚
        期间空置率    : 65.38%
        ---
        期间租金表现  : 期间总租金 718,410.88 元, 期间平均日租金 446.22 元, 按30天计算平均月租金 13,386.54 元
        坪效表现      : 6.11 元/m²/日 (按户型面积 73 m² 计算)
        ---
        最高月租金    : 21,029.00 元 (记录ID: 2773, 入住: 2025-01-06, 离店: 2026-01-06)
        最低月租金    : 8,250.00 元 (记录ID: 2911, 入住: 2025-05-27, 离店: 2026-05-27)

        ==================== 户型: 一房行政豪华式公寓 ====================
        期末供应与占用: 总数 19 间, 期末在租 6 间(包括已预订房间)，其中期末付费 6 间
        期末空置率    : 68.42%
        ---
        期间房晚数    : 总入住房晚数 186 晚, 总付费房晚数 186 晚
        期间空置率    : 68.42%
        ---
        期间租金表现  : 期间总租金 114,002.29 元, 期间平均日租金 612.92 元, 按30天计算平均月租金 18,387.47 元
        坪效表现      : 6.96 元/m²/日 (按户型面积 88 m² 计算)
        ---
        最高月租金    : 24,000.00 元 (记录ID: 3385, 入住: 2025-07-22, 离店: 2026-07-22)
        最低月租金    : 12,484.80 元 (记录ID: 2867, 入住: 2025-03-04, 离店: 2026-03-04)

        ==================== 户型: 两房行政公寓 ====================
        期末供应与占用: 总数 15 间, 期末在租 3 间(包括已预订房间)，其中期末付费 3 间
        期末空置率    : 80.00%
        ---
        期间房晚数    : 总入住房晚数 68 晚, 总付费房晚数 68 晚
        期间空置率    : 85.38%
        ---
        期间租金表现  : 期间总租金 53,570.00 元, 期间平均日租金 787.79 元, 按30天计算平均月租金 23,633.82 元
        坪效表现      : 7.29 元/m²/日 (按户型面积 108 m² 计算)
        ---
        最高月租金    : 24,220.00 元 (记录ID: 3311, 入住: 2025-07-15, 离店: 2026-07-15)
        最低月租金    : 20,160.00 元 (记录ID: 3677, 入住: 2025-08-26, 离店: 2025-10-13)

        ==================== 户型: 三房公寓 ====================
        期末供应与占用: 总数 1 间, 期末在租 0 间(包括已预订房间)，其中期末付费 0 间
        期末空置率    : 100.00%
        ---
        期间房晚数    : 总入住房晚数 0 晚, 总付费房晚数 0 晚
        期间空置率    : 100.00%
        ---
        期间租金表现  : 期间总租金 0.00 元, 期间平均日租金 0.00 元
        坪效表现      : 0.00 元/m²/日 (按户型面积 134 m² 计算)
        ---
        最高月租金    : N/A (期间无付费记录)
        最低月租金    : N/A (期间无付费记录)

        ==================== 户型: 豪华单间公寓 ====================
        期末供应与占用: 总数 22 间, 期末在租 7 间(包括已预订房间)，其中期末付费 7 间
        期末空置率    : 68.18%
        ---
        期间房晚数    : 总入住房晚数 160 晚, 总付费房晚数 160 晚
        期间空置率    : 76.54%
        ---
        期间租金表现  : 期间总租金 37,177.47 元, 期间平均日租金 232.36 元, 按30天计算平均月租金 6,970.78 元
        坪效表现      : 5.16 元/m²/日 (按户型面积 45 m² 计算)
        ---
        最高月租金    : 8,530.00 元 (记录ID: 2507, 入住: 2024-11-05, 离店: 2025-11-05)
        最低月租金    : 5,050.20 元 (记录ID: 2940, 入住: 2025-04-01, 离店: 2026-04-01)

        ==================== 户型: 行政单间公寓 ====================
        期末供应与占用: 总数 360 间, 期末在租 119 间(包括已预订房间)，其中期末付费 117 间
        期末空置率    : 66.94%
        ---
        期间房晚数    : 总入住房晚数 3,152 晚, 总付费房晚数 3,100 晚
        期间空置率    : 71.76%
        ---
        期间租金表现  : 期间总租金 850,342.33 元, 期间平均日租金 274.30 元, 按30天计算平均月租金 8,229.12 元
        坪效表现      : 4.57 元/m²/日 (按户型面积 60 m² 计算)
        ---
        最高月租金    : 13,705.00 元 (记录ID: 2849, 入住: 2025-02-26, 离店: 2026-02-26)
        最低月租金    : 6,600.00 元 (记录ID: 3232, 入住: 2025-06-07, 离店: 2026-06-07)

        ==================== 户型: 豪华行政单间 ====================
        期末供应与占用: 总数 12 间, 期末在租 1 间(包括已预订房间)，其中期末付费 1 间
        期末空置率    : 91.67%
        ---
        期间房晚数    : 总入住房晚数 31 晚, 总付费房晚数 31 晚
        期间空置率    : 91.67%
        ---
        期间租金表现  : 期间总租金 7,192.00 元, 期间平均日租金 232.00 元, 按30天计算平均月租金 6,960.00 元
        坪效表现      : 3.46 元/m²/日 (按户型面积 67 m² 计算)
        ---
        最高月租金    : 6,960.00 元 (记录ID: 3267, 入住: 2025-06-15, 离店: 2026-06-15)
        最低月租金    : 6,960.00 元 (记录ID: 3267, 入住: 2025-06-15, 离店: 2026-06-15)

        ==================== 总体概要 ====================
        所有户型期间总平均日租金: 345.43 元 (基于 5,155 晚期间总付费房晚数计算)
        所有户型期间总坪效: 5.29 元/m²/日 (基于总租金除以总付费面积房晚数)
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
        '1BD': "一房豪华式公寓",
        '1BP': "一房行政豪华式公寓",
        '2BD': "两房行政公寓",
        '3BR': "三房公寓",
        'STD': "豪华单间公寓",
        'STE': "行政单间公寓",
        'STP': "豪华行政单间"
    }

    FILE_PATH = 'demo/master_base.xml'
    print("--- 户型经营表现分析工具 ---")

    # 验证日期格式
    try:
        datetime.datetime.strptime(start_time, '%Y-%m-%d')
        datetime.datetime.strptime(end_time, '%Y-%m-%d')
    except ValueError:
        return "输入错误：日期格式不正确，请使用 'YYYY-MM-DD' 格式。"

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
    功能描述 (description): 一个用于获取指定用户ID的用户信息

    输入参数 (parameters):
    id (Union[str, List[str]]): 用户ID，可使用从如occupancy_details等其他工具中获取的ID；例如: '3664'或'3664, 3694'(同时查询多个ID) 或 ['3664', '3694']

    返回结果 (returns):
    下面是一个调用返回示例：
    query_guest("3664, 999")
    返回：
    '
    成功加载并处理了 501 条记录。
    --- ID: 3664 的核心数据 ---
    主键ID         : 3664
    客户档案ID     : 2522
    姓名           : 晏**
    推断性别       : 男
    出生日期       : 2003-11-02 01:00:00
    语言代码       : C
    手机           : [空]
    电子邮件       : 1**********@163.com
    国籍代码       : CN
    国家代码       : CN
    省份/州代码    : JX
    街道地址       : 江***
    证件类型代码   : 01
    证件号码       : 3****************2
    酒店ID         : 11
    客户档案类型   : GUEST
    入住次数       : 0
    创建用户       : JACQUELINELIANG
    创建时间       : 2025-08-11 16:38:58
    修改用户       : SHINZHANG
    修改时间       : 2025-08-11 17:03:41
    ----------------------------
    ============================================================

    --- 未找到 ID 为 999 的记录 ---
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

            print(f"\n正在合并数据...")
            # 使用 left join，保留所有主客户信息，即使没有租金/状态记录
            merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
            print("数据合并完成。")
        else:
            merged_df = guest_df
            print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

    final_id_list: List[str] = []
    if isinstance(id, list):
        final_id_list = [str(item).strip() for item in id if str(item).strip()]
    elif isinstance(id, str):
        final_id_list = [item.strip() for item in re.split(r'[\s,]+', id) if item.strip()]

    if not final_id_list:
        return "输入错误：未能从输入中解析出有效的用户ID。"

    if merged_df is not None:
        result_variable = get_multiple_query_results_as_string(merged_df, ','.join(
            final_id_list))  # get_multiple_query_results_as_string expects a comma-separated string

        return result_variable


@mcp.tool()
def query_checkins(start: str, end: str, choice: str = 'ALL'):
    """
    功能描述 (description): 一个用于获取指定时间段内的入住信息，可获得的具体字段有：入住日期、离店日期、房号、房型、租金、状态、用户ID、备注、交班信息

    输入参数 (parameters):
    start (Optional[str]): 时间区间起点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
    end (Optional[str]): 时间区间终点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
    choice (Optional[str]): 选择是要查询的入住状态，可选值为"'1': I (在住) '2': O (结帐) '3': X (取消) '4': R (预订) '5': ALL (所有状态，默认)"，默认为 'ALL'

    返回结果 (returns):
    下面是一个调用返回示例：
    query_checkins('2025-08-08', '2025-08-12', '1')
    返回：
    '
     1: I (在住) 2: O (结帐) 3: X (取消) 4: R (预订) 5: ALL (所有状态，默认)
    --- 入住记录查询结果 (2025-08-08 到 2025-08-12, 状态: I) ---
    共找到 7 个房间的（去重后）记录。

          入住日期       离店日期    房号      房型  关联的所有用户ID        租金 状态                                    备注 交班信息
    2025-08-08 2026-08-08  A608  行政单间公寓       3548  7,011.00  I 年租押二付一/已经支付了11685元的押金/8.8办理入住/包500元水电
    2025-08-09 2025-11-09 B1510 一房豪华式公寓       3617 10,800.00  I
    2025-08-10 2026-08-10 A1008  行政单间公寓       3575  6,600.00  I                   POA11000/月 押2付1 6+6
    2025-08-11 2025-10-11 A1105  行政单间公寓 3663, 3734  7,984.20  I                         POA13307 押一付一
    2025-08-11 2025-10-10  A212  行政单间公寓       3664      0.00  I                           马总朋友，IT协助项目
    2025-08-11 2025-11-11  A515  行政单间公寓       3642  8,383.20  I         客户押一付一/已支付一个月押金13972元/带一只小狗入住
    2025-08-12 2026-08-12 A1723 一房豪华式公寓       3660 11,192.40  I                          18654/月，押二付一
    --------------------------------------------------------------------------------
    '
    """
    FILE_PATH = 'demo/master_base.xml'
    # 各户型代码到具体名称的映射
    ROOM_TYPE_NAMES = {
        '1BD': "一房豪华式公寓",
        '1BP': "一房行政豪华式公寓",
        '2BD': "两房行政公寓",
        '3BR': "三房公寓",
        'STD': "豪华单间公寓",
        'STE': "行政单间公寓",
        'STP': "豪华行政单间"
    }
    # 验证日期格式
    try:
        datetime.datetime.strptime(start, '%Y-%m-%d')
        datetime.datetime.strptime(end, '%Y-%m-%d')
    except ValueError:
        return "输入错误：日期格式不正确，请使用 'YYYY-MM-DD' 格式。"

    start_input = start
    end_input = end

    print(" 1: I (在住) 2: O (结帐) 3: X (取消) 4: R (预订) 5: ALL (所有状态，默认)")
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
    功能描述 (description): 一个用于获取指定房间号的历史入住信息，可获得的具体字段有：入住日期、离店日期、房号、房型、租金、状态、用户ID、备注、交班信息

    输入参数 (parameters):
    rooms (Union[str, List[str]]): 需要查询的一个或多个房间号。
        - 推荐的标准格式 (列表): ["A312", "A313", "B1510"]
        - 兼容的格式 (字符串): "A312"

    返回结果 (returns):
    下面是一个调用返回示例：
    query_by_room("A312,A313")
    返回：
    '
    --- 房间号查询结果 (A312, A313) ---
    共找到 4 条相关记录。

          入住日期       离店日期   房号     房型        租金 状态   用户ID                备注 交班信息
    2025-06-16 2025-09-16 A313 行政单间公寓  9,021.00  I 3296 客户预计需要租赁1个月+15天左右
    2025-06-16 2025-08-03 A312 行政单间公寓 10,144.80  O 3306       预计还需要再租赁15天
    2025-06-16 2025-09-16 A313 行政单间公寓      0.00  I 3356
    2025-06-16 2025-08-03 A312 行政单间公寓      0.00  O 3577
    '
    状态对应为 I (在住)  O (结帐)  X (取消)  R (预订)
    """

    FILE_PATH = 'demo/master_base.xml'
    # 各户型代码到具体名称的映射
    ROOM_TYPE_NAMES = {
        '1BD': "一房豪华式公寓",
        '1BP': "一房行政豪华式公寓",
        '2BD': "两房行政公寓",
        '3BR': "三房公寓",
        'STD': "豪华单间公寓",
        'STE': "行政单间公寓",
        'STP': "豪华行政单间"
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
        return "输入错误：未能从输入中解析出有效的房间号。"
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
        功能描述 (description): 一个用于获取指定房间号的历史工单信息，可获得的具体字段有：工单ID、房号、服务项目、需求描述、具体位置、优先级、进入房间指引/注意事项、服务状态、服务人员、处理结果、创建时间、完成时间

        输入参数 (parameters):
        room_number (str): 一个或多个房间号。例如: 'A513'

        返回结果 (returns):
        下面是一个调用返回示例：
        query_orders('A513')
        返回：
        '
          工单ID:     3422
          房号:       A513
          服务项目:   拖线板 (B506)
          需求描述:   浴室淋浴房漏水 需要第二次修补 漏水太厉害
          具体位置:   客厅 (009)
          优先级:   低
          进入房间指引/注意事项:   室内无人 需前台陪同
          服务状态:   O
          服务人员:   工程刘
          处理结果:   已处理
          创建时间:   2025-07-13 22:17:33
          完成时间:   2025-07-14 18:47:44
        '
    """

    XML_FILE_PATH = 'demo/lease_service_order.xml'

    SERVICE_CODE_MAP = {
        'A01': '更换布草', 'A02': '家具保洁', 'A03': '地面保洁', 'A04': '家电保洁',
        'A05': '洁具保洁', 'A06': '客用品更换', 'A07': '杀虫', 'B1001': '电梯',
        'B101': '冰箱', 'B102': '微波炉', 'B103': '烘干机', 'B104': '电视',
        'B105': '洗衣机', 'B106': '空气净化器', 'B107': '抽湿机', 'B108': '油烟机',
        'B110': '电风扇', 'B114': '取暖机', 'B117': '投影仪', 'B119': '屏幕',
        'B120': '热水器', 'B121': '洗碗机', 'B122': '电磁炉', 'B123': '烤箱',
        'B124': '排气扇', 'B201': '烟雾报警器', 'B202': '手动报警器',
        'B203': '消防喷淋', 'B204': '消防应急灯', 'B301': '暖气片', 'B302': '通风管',
        'B303': '空调', 'B401': '毛巾架', 'B402': '龙头', 'B403': '室内门把手/门锁',
        'B404': '窗户', 'B405': '铰链', 'B501': '电源插座', 'B502': '开关',
        'B503': '灯具', 'B504': '电灯泡', 'B505': '灭蝇灯', 'B506': '拖线板',
        'B601': '家具', 'B602': '橱柜', 'B603': '天花板', 'B604': '地板',
        'B605': '墙', 'B606': '百叶窗', 'B607': '脚板', 'B701': '排水',
        'B702': '浴盆', 'B703': '镜子', 'B704': '瓷砖', 'B705': '水槽',
        'B706': '花洒', 'B707': '马桶', 'B708': '台盆', 'B801': '其他',
        'B901': '网络设备'
    }
    all_orders_data = parse_service_orders(XML_FILE_PATH)
    if all_orders_data is None:
        return "未能加载工单数据。"

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
    功能描述 (description):
    一个用于根据时间范围、服务项目和具体位置等条件，查询历史工单信息的服务函数。（此时间段指的是工单开始的时间所处的时间段）
    可获得的具体字段有：工单ID、房号、服务项目、具体位置、需求描述、优先级、进入指引、服务状态、服务人员、处理结果、创建时间、完成时间。

    输入参数 (parameters):
    start_date_str (Optional[str]): 开始日期, 格式为 'YYYY-MM-DD'
    end_date_str (Optional[str]):   结束日期, 格式为 'YYYY-MM-DD'
    service_code (Optional[str]):   服务项目代码 (例如 'B501' 代表电源插座)。默认为None (不限)。
    location_code (Optional[str]):  具体位置代码 (例如 '004' 代表厨房)。默认为None (不限)。

    具体服务项目代码与具体位置代码为：
    SERVICE_CODE_MAP = {
        'A01': '更换布草', 'A02': '家具保洁', 'A03': '地面保洁', 'A04': '家电保洁',
        'A05': '洁具保洁', 'A06': '客用品更换', 'A07': '杀虫', 'B1001': '电梯',
        'B101': '冰箱', 'B102': '微波炉', 'B103': '烘干机', 'B104': '电视',
        'B105': '洗衣机', 'B106': '空气净化器', 'B107': '抽湿机', 'B108': '油烟机',
        'B110': '电风扇', 'B114': '取暖机', 'B117': '投影仪', 'B119': '屏幕',
        'B120': '热水器', 'B121': '洗碗机', 'B122': '电磁炉', 'B123': '烤箱',
        'B124': '排气扇', 'B201': '烟雾报警器', 'B202': '手动报警器',
        'B203': '消防喷淋', 'B204': '消防应急灯', 'B301': '暖气片', 'B302': '通风管',
        'B303': '空调', 'B401': '毛巾架', 'B402': '龙头', 'B403': '室内门把手/门锁',
        'B404': '窗户', 'B405': '铰链', 'B501': '电源插座', 'B502': '开关',
        'B503': '灯具', 'B504': '电灯泡', 'B505': '灭蝇灯', 'B506': '拖线板',
        'B601': '家具', 'B602': '橱柜', 'B603': '天花板', 'B604': '地板',
        'B605': '墙', 'B606': '百叶窗', 'B607': '脚板', 'B701': '排水',
        'B702': '浴盆', 'B703': '镜子', 'B704': '瓷砖', 'B705': '水槽',
        'B706': '花洒', 'B707': '马桶', 'B708': '台盆', 'B801': '其他',
        'B901': '网络设备'
    }
    LOCATION_CODE_MAP = {
        '002': '卧室', '004': '厨房', '008': '卫生间', '009': '客厅',
        '001': '公寓外围', '003': '工区走道', '005': '后场区域', '006': '前场区域',
        '011': '电梯厅-后', '010': '电梯厅-前', '007': '停车场', '012': '消防楼梯',
    }

    返回结果 (returns):
    str: 一个包含所有查询结果的、格式化好的字符串。如果未找到结果，则返回相应的提示信息。
        下面是一个调用返回示例：
        advanced_query_service(start_date_str='2025-07-01', service_code='B701')
        返回：
        '''
        查询条件: 时间范围: [2025-07-01 至 不限], 服务项目: [排水], 具体位置: [不限]
        --- 共找到 2 条相关工单 ---

        【记录 1】
        工单ID:     2639
        房号:       B902
        服务项目:   排水 (B701)
        具体位置:   卫生间 (008)
        需求描述:   浴室下水慢，密封胶条开裂
        优先级:     低
        进入指引:   未提供
        服务状态:   O
        服务人员:   Junfeng Wu
        处理结果:   完成
        创建时间:   2025-05-06 10:29:28
        完成时间:   2025-05-06 11:29:43

        【记录 2】
        工单ID:     3251
        房号:       B911
        服务项目:   排水 (B701)
        具体位置:   未提供 (无代码)
        需求描述:   浴室下水慢
        优先级:     LOW
        进入指引:   未提供
        服务状态:   O
        服务人员:   leonhu
        处理结果:   修复
        创建时间:   2025-07-03 12:12:09
        完成时间:   2025-07-03 12:39:36
        '''
    """
    XML_FILE_PATH = 'demo/lease_service_order.xml'
    SERVICE_CODE_MAP = {
        'A01': '更换布草', 'A02': '家具保洁', 'A03': '地面保洁', 'A04': '家电保洁',
        'A05': '洁具保洁', 'A06': '客用品更换', 'A07': '杀虫', 'B1001': '电梯',
        'B101': '冰箱', 'B102': '微波炉', 'B103': '烘干机', 'B104': '电视',
        'B105': '洗衣机', 'B106': '空气净化器', 'B107': '抽湿机', 'B108': '油烟机',
        'B110': '电风扇', 'B114': '取暖机', 'B117': '投影仪', 'B119': '屏幕',
        'B120': '热水器', 'B121': '洗碗机', 'B122': '电磁炉', 'B123': '烤箱',
        'B124': '排气扇', 'B201': '烟雾报警器', 'B202': '手动报警器',
        'B203': '消防喷淋', 'B204': '消防应急灯', 'B301': '暖气片', 'B302': '通风管',
        'B303': '空调', 'B401': '毛巾架', 'B402': '龙头', 'B403': '室内门把手/门锁',
        'B404': '窗户', 'B405': '铰链', 'B501': '电源插座', 'B502': '开关',
        'B503': '灯具', 'B504': '电灯泡', 'B505': '灭蝇灯', 'B506': '拖线板',
        'B601': '家具', 'B602': '橱柜', 'B603': '天花板', 'B604': '地板',
        'B605': '墙', 'B606': '百叶窗', 'B607': '脚板', 'B701': '排水',
        'B702': '浴盆', 'B703': '镜子', 'B704': '瓷砖', 'B705': '水槽',
        'B706': '花洒', 'B707': '马桶', 'B708': '台盆', 'B801': '其他',
        'B901': '网络设备'
    }
    LOCATION_CODE_MAP = {
        '002': '卧室', '004': '厨房', '008': '卫生间', '009': '客厅',
        '001': '公寓外围', '003': '工区走道', '005': '后场区域', '006': '前场区域',
        '011': '电梯厅-后', '010': '电梯厅-前', '007': '停车场', '012': '消防楼梯',
    }

    ALL_ORDERS_DATA = parse_service_orders(XML_FILE_PATH)
    if ALL_ORDERS_DATA is None:
        return "未能加载工单数据。"

    # --- 处理和验证输入 ---
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    except ValueError:
        return "输入错误：日期格式不正确，请使用 'YYYY-MM-DD' 格式。"

    # --- 执行查询并格式化结果 ---
    found_orders = search_orders_advanced(ALL_ORDERS_DATA, start_date, end_date, service_code, location_code)

    # 构建查询条件描述字符串
    criteria_desc = (
        f"时间范围: [{start_date_str or '不限'} 至 {end_date_str or '不限'}], "
        f"服务项目: [{SERVICE_CODE_MAP.get(service_code, '不限')}], "
        f"具体位置: [{LOCATION_CODE_MAP.get(location_code, '不限')}]"
    )

    return format_to_string(found_orders, criteria_desc)


@mcp.tool()
def query_distribution_report(
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None,
) -> str:
    """
    功能描述 (description):
    获取一段时间内工单统计汇总的总结报告

    输入参数 (parameters):
    start_date_str (Optional[str]): 开始日期, 格式为 'YYYY-MM-DD'
    end_date_str (Optional[str]):   结束日期, 格式为 'YYYY-MM-DD'

    返回结果 (returns):
    str: 一个包含所有查询结果的、格式化好的字符串。如果未找到结果，则返回相应的提示信息。
        下面是一个调用返回示例：
        query_distribution_report(start_date_str='2025-07-01', end_date_str='2025-07-05')
        返回：
        '''
        ==================================================

        --- 总体数据总结 ---

        查询范围内总工单数: 14 条


        --- Top 3 工单项目 ---
          1. 未知代码 (): 5 次 (35.7%)
          2. 龙头: 4 次 (28.6%)
          3. 排水: 2 次 (14.3%)

        --- Top 3 工单位置 ---
          1. 未知位置: 9 次 (64.3%)
          2. 客厅: 5 次 (35.7%)

        --- Top 3 楼层分布 ---
          1. 5楼: 5 次 (35.7%)
          2. 12楼: 2 次 (14.3%)
          3. 6楼: 2 次 (14.3%)

        --- Top 3 楼栋分布 ---
          1. A栋: 11 次 (78.6%)
          2. B栋: 3 次 (21.4%)

        ==================================================

        ==================================================
        --- 服务工单分布情况详细报告 ---

        [ 栋座: A栋 ]
          [ 楼层: 12楼 ]
            ● 位置: 未知位置
              - 未知代码 (): 1 次
          [ 楼层: 2楼 ]
            ● 位置: 客厅
              - 家具: 1 次
          [ 楼层: 3楼 ]
            ● 位置: 未知位置
              - 排水: 1 次
          [ 楼层: 5楼 ]
            ● 位置: 未知位置
              - 龙头: 2 次
              - 未知代码 (): 2 次
          [ 楼层: 6楼 ]
            ● 位置: 客厅
              - 其他: 1 次
            ● 位置: 未知位置
              - 未知代码 (): 1 次
          [ 楼层: 8楼 ]
            ● 位置: 客厅
              - 龙头: 2 次

        [ 栋座: B栋 ]
          [ 楼层: 12楼 ]
            ● 位置: 客厅
              - 其他: 1 次
          [ 楼层: 5楼 ]
            ● 位置: 未知位置
              - 未知代码 (): 1 次
          [ 楼层: 9楼 ]
            ● 位置: 未知位置
              - 排水: 1 次
        ==================================================
        '''
    """
    XML_FILE_PATH = 'demo/lease_service_order.xml'
    SERVICE_CODE_MAP = {
        'A01': '更换布草', 'A02': '家具保洁', 'A03': '地面保洁', 'A04': '家电保洁',
        'A05': '洁具保洁', 'A06': '客用品更换', 'A07': '杀虫', 'B1001': '电梯',
        'B101': '冰箱', 'B102': '微波炉', 'B103': '烘干机', 'B104': '电视',
        'B105': '洗衣机', 'B106': '空气净化器', 'B107': '抽湿机', 'B108': '油烟机',
        'B110': '电风扇', 'B114': '取暖机', 'B117': '投影仪', 'B119': '屏幕',
        'B120': '热水器', 'B121': '洗碗机', 'B122': '电磁炉', 'B123': '烤箱',
        'B124': '排气扇', 'B201': '烟雾报警器', 'B202': '手动报警器',
        'B203': '消防喷淋', 'B204': '消防应急灯', 'B301': '暖气片', 'B302': '通风管',
        'B303': '空调', 'B401': '毛巾架', 'B402': '龙头', 'B403': '室内门把手/门锁',
        'B404': '窗户', 'B405': '铰链', 'B501': '电源插座', 'B502': '开关',
        'B503': '灯具', 'B504': '电灯泡', 'B505': '灭蝇灯', 'B506': '拖线板',
        'B601': '家具', 'B602': '橱柜', 'B603': '天花板', 'B604': '地板',
        'B605': '墙', 'B606': '百叶窗', 'B607': '脚板', 'B701': '排水',
        'B702': '浴盆', 'B703': '镜子', 'B704': '瓷砖', 'B705': '水槽',
        'B706': '花洒', 'B707': '马桶', 'B708': '台盆', 'B801': '其他',
        'B901': '网络设备'
    }
    LOCATION_CODE_MAP = {
        '002': '卧室', '004': '厨房', '008': '卫生间', '009': '客厅',
        '001': '公寓外围', '003': '工区走道', '005': '后场区域', '006': '前场区域',
        '011': '电梯厅-后', '010': '电梯厅-前', '007': '停车场', '012': '消防楼梯',
    }

    ALL_ORDERS_DATA = parse_service_orders(XML_FILE_PATH)
    if ALL_ORDERS_DATA is None:
        return "未能加载工单数据。"

    # --- 处理和验证输入 ---
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    except ValueError:
        return "输入错误：日期格式不正确，请使用 'YYYY-MM-DD' 格式。"

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
    打开一个网页数据仪表盘，调用后你会得到一个打开成功消息
    """
    generate_dashboard()
    return "仪表盘开启成功，请访问 https://chatbot.sparkai.xin/ 查看"


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
        remark_keyword: Optional[str] = None
) -> Dict[str, Any]:
    """
    根据筛选条件对住客入住数据进行统计分析

    例如可以使用这个工具获取到公寓目前的在住住客的统计信息

    Args:
        name (Optional[str]): 按住客姓名进行模糊搜索。
        room_number (Optional[str]): 按房号进行精确匹配。
        gender: (Optional[str]) = None: 按性别进行筛选
        status (Union[str, List[str]]):
            按住客状态进行精确筛选 ('I'(In-House, 在住), 'R'(Reservation, 预订), 'O'(Checked-Out, 已离店), 'X'(Cancelled, 已取消), '实际当前在住')。
            可多选，如status=['I', 'O']
            由于数据源长时间未更新，实际当前在住住客数量与状态为'I'的数据数量存在差距，如需获取当前实际在住住客统计信息，需使用status='实际当前在住'(此参数不可多选)
        nation (Optional[str]): 按国籍进行模糊搜索。
        min_age (Optional[int]): 筛选住客的最小年龄。
        max_age (Optional[int]): 筛选住客的最大年龄。
        min_rent (Optional[float]): 筛选月租金的最低值。
        max_rent (Optional[float]): 筛选月租金的最高值。
        start_arr_date (Optional[Any]): 时间段开始时间
        end_arr_date (Optional[Any]): 时间段结束时间
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
              "rent_analysis": [{"gender": str, "count": int, "percentage": str}]
            }
        }

    调用示例：
    查询当前在住住客的各类统计数据：get_statistical_summary(status = '实际当前在住')
    查询在2025年9月新入住的住客的统计数据：get_statistical_summary(status=['I','O','R'], start_arr_date='2025-09-01', end_arr_date='2025-09-30')
    查询当前男性住客中有宠物住客的统计数据：get_statistical_summary(gender='男', status='实际当前在住', remark_keyword='宠物')
    查询男性住客的统计数据，包括年龄国籍等维度的人数分布：get_statistical_summary(gender='男', status='实际当前在住')
    """
    guest_df = load_data_from_xml('demo/master_guest.xml')
    # 加载状态和租金数据
    status_rent_df = load_status_rent_data_from_xml('demo/master_base.xml')

    # 3. 如果状态租金数据成功加载，则执行合并
    if status_rent_df is not None:
        # 确保合并键的数据类型一致
        guest_df['profile_id'] = pd.to_numeric(guest_df['id'], errors='coerce')

        print(f"\n正在合并数据...")
        # 使用左连接（left join）进行合并
        merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
        print("数据合并完成。")
    else:
        # 如果第二个文件不存在或加载失败，则继续使用原始数据
        merged_df = guest_df
        print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

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
        remark_keyword: Optional[str] = None
) -> str:
    """
    根据筛选条件获取详细的住客个人信息列表

    例如，您可以使用此函数获取所有月租金超过10000元的在住客人的完整名单

    Args:
        name (Optional[str]): 按住客姓名进行模糊搜索。
        room_number (Optional[str]): 按房号进行精确匹配。
        gender (Optional[str]): 按性别进行筛选 ('男' 或 '女')。
        status (Union[str, List[str]]):
            按住客状态进行精确筛选 ('I'(In-House, 在住), 'R'(Reservation, 预订), 'O'(Checked-Out, 已离店), 'X'(Cancelled, 已取消), '实际当前在住')。
            可多选，如status=['I', 'O']。
            由于数据源长时间未更新，实际当前在住住客数量与状态为'I'的数据数量存在差距，如需获取当前实际在住住客列表，需使用status='实际当前在住'(此参数不可多选)。
        nation (Optional[str]): 按国籍进行模糊搜索。
        min_age (Optional[int]): 筛选住客的最小年龄。
        max_age (Optional[int]): 筛选住客的最大年龄。
        min_rent (Optional[float]): 筛选月租金的最低值。
        max_rent (Optional[float]): 筛选月租金的最高值。
        start_arr_date (Optional[Any]): 筛选此日期之后（包含当天）入住的记录。
        end_arr_date (Optional[Any]): 筛选此日期之前（包含当天）入住的记录。
        remark_keyword (Optional[str]): 在备注字段中进行模糊搜索。

    Returns:
        一个单一的字符串 (str)，包含了所有符合条件的住客的详细信息。
        该字符串的结构如下:
        - 字符串开头会有一个总数统计的标题。
        - 每位住客的信息都经过格式化，与单ID查询的结果一致。
        - 住客信息之间由一个醒目的分隔符 (例如 "==================================================") 隔开。
        - 如果没有找到任何记录，将返回一条提示信息，如 "--- 未找到符合条件的住客记录 ---"。

    调用示例：
    查询当前所有备注中包含'宠物'的在住客人的详细列表：get_filtered_details(status='实际当前在住', remark_keyword='宠物')
    查询所有月租金高于10000元的住客名单：get_filtered_details(min_rent=10000.01,status='实际当前在住')
    查询所有国籍为'USA'的住客详细信息：get_filtered_details(nation='USA',status='实际当前在住')
    """
    guest_df = load_data_from_xml('demo/master_guest.xml')
    # 加载状态和租金数据
    status_rent_df = load_status_rent_data_from_xml('demo/master_base.xml')

    # 3. 如果状态租金数据成功加载，则执行合并
    if status_rent_df is not None:
        # 确保合并键的数据类型一致
        guest_df['profile_id'] = pd.to_numeric(guest_df['id'], errors='coerce')

        print(f"\n正在合并数据...")
        # 使用左连接（left join）进行合并
        merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
        print("数据合并完成。")
    else:
        # 如果第二个文件不存在或加载失败，则继续使用原始数据
        merged_df = guest_df
        print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

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
    )

    return details_string_result


@mcp.tool()
def nearby_report(room: Optional[str]):
    """
    功能描述 (description): 一个用于获取指定房间号的周围房间的入住情况，可获得的具体字段有：入住日期、离店日期、房号、房型、租金、用户ID、备注、交班信息

    输入参数 (parameters):
    room (Optional[str]): 需要查询的房间号。
        - 兼容的格式 (字符串): "A312"

    返回结果 (returns):
    下面是一个调用返回示例：
    print(nearby_report("A1608"))
    返回：
    '
    --- 房间 A1608 周边入住状态查询 (2025-10-21) ---

      - 房间 A1607: [有人居住 (I)]
        住客ID:    3804
        在住时段:    2025-09-10 至 2025-12-20
        房型:      STE
        租金:      7512.6
        备注:      3个月零10天/押一付一
      - 房间 A1609: [当前无人居住]
      - 房间 A1708: [当前无人居住]
      - 房间 A1508: [当前无人居住]
      - 房间 A1507: [当前无人居住]
      - 房间 A1509: [当前无人居住]
      - 房间 A1707: [当前无人居住]
      - 房间 A1709: [当前无人居住]
      - 房间 A1707: [当前无人居住]
    '
    状态对应为 I (在住)  O (结帐)  X (取消)  R (预订)
    """
    FILE_PATH = 'demo/master_base.xml'
    # 优先处理列表形式，这是我们引导模型生成的标准形式
    if isinstance(room, list):
        final_room_list = [str(item).strip() for item in room if str(item).strip()]

    # 兼容模型可能返回单个字符串的边缘情况
    elif isinstance(room, str):
        # 假设字符串只包含一个房间号，或用逗号/空格分隔的多个房间号
        final_room_list = [r.strip() for r in re.split(r'[\s,]+', room) if r.strip()]

    if not final_room_list:
        return "输入错误：未能从输入中解析出有效的房间号。"

    nearby_query_result = query_nearby_rooms_status(FILE_PATH, room)
    nearby_report = format_nearby_status(nearby_query_result, room)

    return nearby_report


if __name__ == "__main__":

    app_instance = mcp.sse_app

    print(get_statistical_summary(gender='男', status='实际当前在住'))

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