import os
import datetime
import pandas as pd
from typing import List, Any, Union, Optional
import re

from demo.calculate_occupancy import calculate_occupancy_rate, format_result_to_string
from demo.room import analyze_room_type_performance, format_analysis_to_string
from demo.query_guest_data import load_data_from_xml, get_query_result_as_string
from demo.query_checkins import query_checkin_records, format_records_to_string
from demo.query_by_room import query_records_by_room, format_string
from demo.query_orders import parse_service_orders, search_by_rmno, format_results_to_string

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("公寓数据查询")

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

@mcp.tool()
def calculate_occupancy(start: str, end: str, details: str):
    """
    功能描述 (description): 一个用于获取指定时间内的入住率的工具

    输入参数 (parameters):
    start (Optional[str]): 时间区间起点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
    end (Optional[str]): 时间区间终点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
    details (Optional[str]): 选择是否获取详细的记录，可选值为'y'/'n'，默认为 'n'


    返回结果 (returns):
    下面是一个调用返回示例：
    print(calculate_occupancy("2025-06-01", "2025-06-05", "y"))
    返回：
    '
    --- 入住率计算 ---

    --- 每日入住详情 ---
    日期: 2025-06-01 | 当日入住房间数: 89  | 房间号: B1203, B602, B1103, B1206, B607, B1211, A1206, B502, B1212, A1208, ... (共 89 间)
    日期: 2025-06-02 | 当日入住房间数: 90  | 房间号: B1203, B602, B1103, B1206, B607, B1211, A1206, B502, B1212, A1208, ... (共 90 间)
    日期: 2025-06-03 | 当日入住房间数: 91  | 房间号: B1203, B602, B1103, B1206, B607, B1211, A1206, B502, B1212, A1208, ... (共 91 间)
    日期: 2025-06-04 | 当日入住房间数: 91  | 房间号: B1203, B602, B1103, B1206, B607, B1211, A1206, B502, B1212, A1208, ... (共 91 间)
    日期: 2025-06-05 | 当日入住房间数: 92  | 房间号: B1203, B602, B1103, B1206, B607, B1211, A1206, B502, B1212, A1208, ... (共 92 间)

    --- 计算结果 ---
    查询范围: 2025-06-01 到 2025-06-05 (5 天)
    总可用房晚数: 2,895
    实际入住房晚数: 453
    入住率: 15.65%
    ------------------
    '
    """

    FILE_PATH = 'demo/master_base.xml'
    TOTAL_ROOMS = 579

    print("--- 入住率计算 ---")

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
def occupancy_details(time: str):
    """
        功能描述 (description): 一个用于获取指定时间的不同房型型的出租情况（租金，坪效，空置率）的工具，同时还可获得不同房型的最高租金与最低租金，以及对应的用户ID

        输入参数 (parameters):
        time (Optional[str]): 数据截止时间，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'

        返回结果 (returns):
        下面是一个调用返回示例：
        print(occupancy_details("2025-08-01"))
        返回：
        '
        --- 户型经营表现分析工具 ---
        请输入要分析的截止日期 (YYYY-MM-DD): 2025-08-01
        --- 各户型经营表现分析 (数据截止日期: 2025-08-01) ---

        ==================== 户型: 一房豪华式公寓 ====================
        供应与占用: 总数 150 间, 在租 55 间 (其中付费 55 间)
        空置率    : 63.33%
        ---
        租金表现  : 平均月租金 13,506.25 元
        坪效表现  : 185.02 元/m²/月 (按面积 73 m² 计算)
        ---
        最高租金  : 21,029.00 元 (记录ID: 2773, 入住: 2025-01-06, 离店: 2026-01-06)
        最低租金  : 8,250.00 元 (记录ID: 2911, 入住: 2025-05-27, 离店: 2026-05-27)

        ==================== 户型: 一房行政豪华式公寓 ====================
        供应与占用: 总数 19 间, 在租 7 间 (其中付费 7 间)
        空置率    : 63.16%
        ---
        租金表现  : 平均月租金 17,825.80 元
        坪效表现  : 202.57 元/m²/月 (按面积 88 m² 计算)
        ---
        最高租金  : 24,000.00 元 (记录ID: 3385, 入住: 2025-07-22, 离店: 2026-07-22)
        最低租金  : 12,484.80 元 (记录ID: 2867, 入住: 2025-03-04, 离店: 2026-03-04)

        ==================== 户型: 两房行政公寓 ====================
        供应与占用: 总数 15 间, 在租 4 间 (其中付费 4 间)
        空置率    : 73.33%
        ---
        租金表现  : 平均月租金 21,759.90 元
        坪效表现  : 201.48 元/m²/月 (按面积 108 m² 计算)
        ---
        最高租金  : 24,220.00 元 (记录ID: 3311, 入住: 2025-07-15, 离店: 2026-07-15)
        最低租金  : 19,419.60 元 (记录ID: 3352, 入住: 2025-07-10, 离店: 2025-08-15)

        ==================== 户型: 三房公寓 ====================
        供应与占用: 总数 1 间, 在租 0 间 (其中付费 0 间)
        空置率    : 100.00%
        ---
        租金表现  : 平均月租金 0.00 元
        坪效表现  : 0.00 元/m²/月 (按面积 134 m² 计算)
        ---
        最高租金  : N/A (无付费记录)
        最低租金  : N/A (无付费记录)

        ==================== 户型: 豪华单间公寓 ====================
        供应与占用: 总数 22 间, 在租 5 间 (其中付费 5 间)
        空置率    : 77.27%
        ---
        租金表现  : 平均月租金 7,030.48 元
        坪效表现  : 156.23 元/m²/月 (按面积 45 m² 计算)
        ---
        最高租金  : 8,530.00 元 (记录ID: 2625, 入住: 2024-12-01, 离店: 2025-12-01)
        最低租金  : 5,050.20 元 (记录ID: 2940, 入住: 2025-04-01, 离店: 2026-04-01)

        ==================== 户型: 行政单间公寓 ====================
        供应与占用: 总数 360 间, 在租 120 间 (其中付费 118 间)
        空置率    : 66.67%
        ---
        租金表现  : 平均月租金 8,341.90 元
        坪效表现  : 139.03 元/m²/月 (按面积 60 m² 计算)
        ---
        最高租金  : 13,705.00 元 (记录ID: 2849, 入住: 2025-02-26, 离店: 2026-02-26)
        最低租金  : 6,600.00 元 (记录ID: 3232, 入住: 2025-06-07, 离店: 2026-06-07)

        ==================== 户型: 豪华行政单间 ====================
        供应与占用: 总数 12 间, 在租 0 间 (其中付费 0 间)
        空置率    : 100.00%
        ---
        租金表现  : 平均月租金 0.00 元
        坪效表现  : 0.00 元/m²/月 (按面积 67 m² 计算)
        ---
        最高租金  : N/A (无付费记录)
        最低租金  : N/A (无付费记录)

        ==================== 总体概要 ====================
        所有户型总平均月租金: 10,445.29 元 (基于 189 间付费在租房间计算)

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
    as_of_date_input = time

    # 1. 调用计算函数，获取原始数据结果
    results_list = analyze_room_type_performance(
        FILE_PATH,
        as_of_date_input,
        ROOM_TYPE_COUNTS,
        ROOM_TYPE_AREAS
    )

    # 2. 调用格式化函数，将结果存入字符串变量
    final_report_string = format_analysis_to_string(
        results_list,
        as_of_date_input,
        ROOM_TYPE_NAMES
    )

    # 3. 打印字符串变量
    return final_report_string

@mcp.tool()
def query_guest(id: str):
    """
    功能描述 (description): 一个用于获取指定用户ID的用户信息

    输入参数 (parameters):
    id (Optional[str]): 用户ID，可使用从如occupancy_details等其他工具中获取的ID；例如: '3664'

    返回结果 (returns):
    下面是一个调用返回示例：
    print(query_guest("3664"))
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
    '
    """

    XML_FILE_PATH = 'demo/master_guest.xml'

    # 1. 重要字段列表
    IMPORTANT_FIELDS = [
        'id', 'profile_id', 'name', 'sex_like', 'birth', 'language',  # 'sex' -> 'sex_like'
        'mobile', 'email', 'nation', 'country', 'state', 'street',
        'id_code', 'id_no', 'hotel_id', 'profile_type', 'times_in',
        'create_user', 'create_datetime', 'modify_user', 'modify_datetime',
    ]

    # 2. 中文映射
    FIELD_NAME_MAPPING = {
        'id': '主键ID',
        'profile_id': '客户档案ID',
        'name': '姓名',
        'sex_like': '推断性别',  # 修改
        'birth': '出生日期',
        'language': '语言代码',
        'mobile': '手机',
        'email': '电子邮件',
        'nation': '国籍代码',
        'country': '国家代码',
        'state': '省份/州代码',
        'street': '街道地址',
        'id_code': '证件类型代码',
        'id_no': '证件号码',
        'hotel_id': '酒店ID',
        'profile_type': '客户档案类型',
        'times_in': '入住次数',
        'create_user': '创建用户',
        'create_datetime': '创建时间',
        'modify_user': '修改用户',
        'modify_datetime': '修改时间',
    }
    guest_df = load_data_from_xml(XML_FILE_PATH)
    query_id = int(id)

    if guest_df is not None:
        query_id_example = query_id

        result_variable = get_query_result_as_string(guest_df, query_id_example)

        return result_variable

@mcp.tool()
def query_checkins(start: str, end: str, choice: str):
    """
    功能描述 (description): 一个用于获取指定时间段内的入住信息，可获得的具体字段有：入住日期、离店日期、房号、房型、租金、状态、用户ID、备注、交班信息

    输入参数 (parameters):
    start (Optional[str]): 时间区间起点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
    end (Optional[str]): 时间区间终点，必须按照YYYY-MM-DD格式填写；例如: '2025-05-01'
    choice (Optional[str]): 选择是要查询的入住状态，可选值为"'1': I (在住) '2': O (结帐) '3': X (取消) '4': R (预订) '5': ALL (所有状态，默认)"，默认为 'ALL'

    返回结果 (returns):
    下面是一个调用返回示例：
    print(query_checkins('2025-08-08', '2025-08-12', '1'))
    返回：
    '
    --- 入住记录查询结果 (2025-08-08 到 2025-08-12, 状态: I) ---
    共找到 7 条（去重后）记录。

          入住日期       离店日期    房号      房型        租金 状态  用户ID                                    备注 交班信息
    2025-08-08 2026-08-08  A608  行政单间公寓  7,011.00  I  3548 年租押二付一/已经支付了11685元的押金/8.8办理入住/包500元水电
    2025-08-09 2025-11-09 B1510 一房豪华式公寓 10,800.00  I  3617
    2025-08-10 2026-08-10 A1008  行政单间公寓  6,600.00  I  3575                   POA11000/月 押2付1 6+6
    2025-08-11 2025-10-11 A1105  行政单间公寓  7,984.20  I  3663                         POA13307 押一付一
    2025-08-11 2025-09-10  A212  行政单间公寓      0.00  I  3664                           马总朋友，IT协助项目
    2025-08-11 2025-11-11  A515  行政单间公寓  8,383.20  I  3642         客户押一付一/已支付一个月押金13972元/带一只小狗入住
    2025-08-12 2026-08-12 A1723 一房豪华式公寓 11,192.40  I  3660                          18654/月，押二付一

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
def query_by_room(room: str):
    """
    功能描述 (description): 一个用于获取指定房间号的入住信息，可获得的具体字段有：入住日期、离店日期、房号、房型、租金、状态、用户ID、备注、交班信息

    输入参数 (parameters):
    room (Optional[str]): 房间号，可同时查询多个房间号，用空格或逗号隔开即可；例如: 'A312,A313'


    返回结果 (returns):
    下面是一个调用返回示例：
    print(query_by_room("A312,A313"))
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
    room_input = room

    # 使用正则表达式分割输入，并清除空字符串
    # 例如，'A101, B202 C303' -> ['A101', 'B202', 'C303']
    room_list = [r.strip() for r in re.split(r'[\s,]+', room_input) if r.strip()]

    # 1. 调用查询函数
    found_records = query_records_by_room(FILE_PATH, room_list)

    # 2. 调用格式化函数
    final_report_string = format_string(
        found_records,
        room_list,
        ROOM_TYPE_NAMES
    )

    # 3. 打印结果
    return final_report_string

@mcp.tool()
def query_orders(room: str):
    """
        功能描述 (description): 一个用于获取指定房间号的历史工单信息，可获得的具体字段有：入住日期、离店日期、房号、房型、租金、状态、用户ID、备注、交班信息

        输入参数 (parameters):
        room (Optional[str]): 房间号


        返回结果 (returns):
        下面是一个调用返回示例：
        print(query_orders('A513'))
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
    all_orders = parse_service_orders(XML_FILE_PATH)
    if all_orders is None: return

    room_number_input = room

    found_orders = search_by_rmno(all_orders, room_number_input)
    result_string = format_results_to_string(found_orders)
    return result_string



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
    
    print(calculate_occupancy("2025-06-01", "2025-06-05", "y"))
    print(occupancy_details("2025-06-01"))
    print(query_guest("3664"))
    print(query_checkins('2025-08-08', '2025-08-12', '1'))
    print(query_by_room("A312,A313"))
    print(query_orders('A513'))
    '''



    mcp.run(transport="sse")
