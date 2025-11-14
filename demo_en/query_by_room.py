import pandas as pd
from datetime import datetime
from lxml import etree
import re  # 引入正则表达式库

# --- 配置区域 ---
FILE_PATH = 'master_base.xml'
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


# --- 数据解析函数 (与之前相同) ---
def parse_spreadsheetml(file_path: str):
    """
    使用 lxml 解析 SpreadsheetML 2003 XML 文件并返回一个 pandas DataFrame 或错误信息。
    """
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = root.findall('.//ss:Worksheet/ss:Table/ss:Row', namespaces=ns)
        if not rows: return pd.DataFrame()
        header_row = rows[0]
        header = [cell.find('ss:Data', namespaces=ns).text.strip() if cell.find('ss:Data',
                                                                                namespaces=ns) is not None and cell.find(
            'ss:Data', namespaces=ns).text is not None else "" for cell in header_row.findall('ss:Cell', namespaces=ns)]
        data = []
        for row in rows[1:]:
            row_data = [(cell.find('ss:Data', namespaces=ns).text if cell.find('ss:Data',
                                                                               namespaces=ns) is not None and cell.find(
                'ss:Data', namespaces=ns).text is not None else '') for cell in row.findall('ss:Cell', namespaces=ns)]
            if len(row_data) < len(header): row_data.extend([''] * (len(header) - len(row_data)))
            data.append(row_data)
        return pd.DataFrame(data, columns=header)
    except Exception as e:
        return f"Error parsing XML file: {e}"


def sanitize_for_display(text):
    """
    清理字符串，将可能破坏表格布局的控制字符替换为空格。
    """
    if not isinstance(text, str):
        return text
    control_char_regex = re.compile(r'[\x00-\x1F\x7F-\x9F\u2028\u2029]')
    sanitized_text = control_char_regex.sub(' ', text)
    return sanitized_text

# --- 核心查询函数 (按房号或楼层模式筛选) ---
def query_records_by_room(file_path: str, query_inputs: list):
    """
    根据一个或多个房间号或楼层模式查询所有相关记录。
    查询输入可以包含具体的房间号（如 'A212'）或简化模式（如 'A2*'）。
    """
    if not query_inputs:
        return "Error: No room numbers or floor patterns entered."

    df_or_error = parse_spreadsheetml(file_path)
    if isinstance(df_or_error, str):
        return df_or_error
    df = df_or_error

    if df.empty:
        return "Failed to load any data from the file."

    # --- 数据预处理 ---
    required_cols = ['id', 'sta', 'rmno', 'rmtype', 'arr', 'dep', 'full_rate_long', 'is_long', 'remark', 'co_msg']
    if not all(col in df.columns for col in required_cols):
        return f"Error: Required columns are missing from the file. Needed: {required_cols}"

    for col in ['id', 'arr', 'dep', 'full_rate_long']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(subset=['rmno'], inplace=True) # 移除房间号为空的记录，以确保后续字符串操作的有效性

    df['arr_date'] = pd.to_datetime(df['arr'], unit='D', origin='1899-12-30').dt.date
    df['dep_date'] = pd.to_datetime(df['dep'], unit='D', origin='1899-12-30').dt.date

    # --- 核心筛选逻辑 ---
    filters = []
    for item in query_inputs:
        item_upper = item.upper()
        if item_upper.endswith('*'):
            prefix = item_upper[:-1]
            if prefix:
                filters.append(df['rmno'].str.upper().str.startswith(prefix))
        else:
            filters.append(df['rmno'].str.upper() == item_upper)
    if not filters:
        return "Error: No valid query conditions found."
    combined_condition = filters[0]
    for i in range(1, len(filters)):
        combined_condition = combined_condition | filters[i]
    room_records_df = df[combined_condition].copy()
    return room_records_df


# --- 新增功能: 核心查询函数 2 (查询附近房间状态) ---
def query_nearby_rooms_status(file_path: str, target_room: str):
    """
    查询指定房间相邻房间的当前入住状态。
    返回一个包含当前入住信息的DataFrame和相邻房间号列表。
    """
    df_or_error = parse_spreadsheetml(file_path)
    if isinstance(df_or_error, str):
        return df_or_error
    df = df_or_error

    if df.empty:
        return "Failed to load any data from the file."

    # --- 数据预处理 ---
    required_cols = ['id', 'sta', 'rmno', 'rmtype', 'arr', 'dep', 'full_rate_long', 'is_long', 'remark', 'co_msg']
    if not all(col in df.columns for col in required_cols):
        return f"Error: Required columns are missing from the file. Needed: {required_cols}"

    for col in ['id', 'arr', 'dep', 'full_rate_long']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(subset=['rmno'], inplace=True)  # 移除房间号为空的记录，以确保后续字符串操作的有效性

    df['arr_date'] = pd.to_datetime(df['arr'], unit='D', origin='1899-12-30').dt.date
    df['dep_date'] = pd.to_datetime(df['dep'], unit='D', origin='1899-12-30').dt.date

    target_room_upper = target_room.upper()

    # 1. 使用正则表达式解析房号，分离字母前缀和数字部分
    match = re.match(r'([A-Z]*)(\d+)', target_room_upper)
    if not match:
        return f"Error: Unable to parse room number '{target_room}'. Format should be 'A212'.", None

    prefix = match.group(1)  # 字母前缀，如 'A'
    room_num = int(match.group(2))  # 数字部分，如 212

    # 2. 计算相邻的房号
    prev_str = f"{prefix}{room_num - 1}"  # 例如 'A211'
    next_str = f"{prefix}{room_num + 1}"  # 例如 'A213'
    upward_str = f"{prefix}{room_num + 100}" # 上一层楼，同房号
    under_str = f"{prefix}{room_num - 100}" # 下一层楼，同房号
    prev_upward_str = f"{prefix}{room_num + 99}" # 上一层楼，前一个房号
    next_upward_str = f"{prefix}{room_num + 101}" # 上一层楼，后一个房号
    prev_under_str = f"{prefix}{room_num - 101}" # 下一层楼，前一个房号
    next_under_str = f"{prefix}{room_num - 99}" # 下一层楼，后一个房号
    nearby_rooms_list = [target_room, prev_str, next_str, upward_str, under_str, prev_under_str, next_under_str, prev_upward_str, next_upward_str]

    # 3. 在DataFrame中筛选出这些相邻房间的所有历史记录
    nearby_records_df = df[df['rmno'].str.upper().isin(nearby_rooms_list)].copy()

    # 4. 判断当前是否有人居住
    today = datetime.now().date()

    # 筛选条件：
    # a. 当前日期必须大于等于入住日期
    # b. 当前日期必须小于等于离店日期
    # c. 房间状态(sta)必须是 'I' (Occupied)
    current_stayers_df = nearby_records_df[
        (nearby_records_df['arr_date'] <= today) &
        (nearby_records_df['dep_date'] >= today) &
        (nearby_records_df['sta'].str.upper() == 'I')
        ].copy()

    if not current_stayers_df.empty:
        current_stayers_df['remark'] = current_stayers_df['remark'].fillna('').apply(sanitize_for_display)
        current_stayers_df['co_msg'] = current_stayers_df['co_msg'].fillna('').apply(sanitize_for_display)

    return current_stayers_df, nearby_rooms_list


# --- 格式化输出函数 1 (历史记录报告) ---
def format_string(records_df, query_inputs, room_names) -> str:
    if isinstance(records_df, str):
        return records_df
    query_str_display = ", ".join(query_inputs)
    if records_df.empty:
        return f"No records found related to '{query_str_display}'."

    records_df['remark'] = records_df['remark'].apply(sanitize_for_display)
    records_df['co_msg'] = records_df['co_msg'].apply(sanitize_for_display)
    records_df['Room Type Name'] = records_df['rmtype'].map(room_names).fillna(records_df['rmtype'])
    records_df['Stay Type'] = records_df['is_long'].apply(lambda x: 'Long Stay' if x == 'T' else 'Short Stay')
    records_df['Rent/Rate'] = records_df['full_rate_long'].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A")
    records_df['remark'] = records_df['remark'].fillna('')
    records_df['co_msg'] = records_df['co_msg'].fillna('')
    records_df_sorted = records_df.sort_values(by='arr_date', ascending=False)
    report_lines = []
    report_lines.append(f"--- Room Number/Floor Pattern Query Results ({query_str_display}) ---")
    report_lines.append(f"Found {len(records_df_sorted)} relevant records.\n")
    display_columns = {
        'arr_date': 'Arrival Date', 'dep_date': 'Departure Date', 'rmno': 'Room No.', 'Room Type Name': 'Room Type',
        'Rent/Rate': 'Rent', 'sta': 'Status', 'id': 'User ID', 'remark': 'Remark', 'co_msg': 'Handover Info'
    }
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', 1000)
    table_string = records_df_sorted[list(display_columns.keys())].rename(columns=display_columns).to_string(
        index=False)
    report_lines.append(table_string)
    report_lines.append("\n" + "-" * 80)
    return "\n".join(report_lines)


# --- 格式化输出函数 2 (附近房间状态报告) ---
def format_nearby_status(query_result, target_room: str) -> str:
    """
    格式化相邻房间入住状态的查询结果，提供详细信息。
    """
    # 这里使用全局的ROOM_TYPE_NAMES映射
    global ROOM_TYPE_NAMES

    if isinstance(query_result, str):
        return query_result  # 如果查询函数返回了错误信息，直接显示

    current_stayers_df, nearby_rooms_list = query_result

    # 映射房型名称、入住类型和租金
    current_stayers_df['Room Type Name'] = current_stayers_df['rmtype'].map(ROOM_TYPE_NAMES).fillna(current_stayers_df['rmtype'])
    current_stayers_df['Stay Type'] = current_stayers_df['is_long'].apply(lambda x: 'Long Stay' if x == 'T' else 'Short Stay')
    current_stayers_df['Rent/Rate'] = current_stayers_df['full_rate_long'].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A")

    if nearby_rooms_list is None:
        return "Query failed, unable to generate report."

    report_lines = []
    report_lines.append(f"--- Nearby Room Occupancy Status for Room {target_room} ({datetime.now().strftime('%Y-%m-%d')}) ---")

    for room in nearby_rooms_list:
        # 查找该房间是否在“当前入住者”的DataFrame中
        record = current_stayers_df[current_stayers_df['rmno'].str.upper() == room.upper()]

        if not record.empty:
            # 如果找到记录，说明有人住，提取详细信息
            stay_info = record.iloc[0]
            guest_id = stay_info.get('id', 'N/A')
            remark = stay_info.get('remark', '').strip()
            co_msg = stay_info.get('co_msg', '').strip()
            roomtype = stay_info.get('Room Type Name', '').strip() # 使用映射后的名称
            stay_type = stay_info.get('Stay Type', '').strip() # 使用映射后的名称
            full_rate_long = stay_info.get('Rent/Rate', '') # 使用格式化后的租金

            report_lines.append(f"\n  - Room {room}: [Occupied (I)]")
            report_lines.append(f"    {'Guest ID:':<12} {guest_id}")
            report_lines.append(f"    {'Stay Period:':<12} {stay_info['arr_date']} to {stay_info['dep_date']}")
            report_lines.append(f"    {'Room Type:':<12} {roomtype}")
            report_lines.append(f"    {'Stay Type:':<12} {stay_type}")
            report_lines.append(f"    {'Rent:':<12} {full_rate_long}")
            if remark: # 只有在备注不为空时才显示
                report_lines.append(f"    {'Remark:':<12} {remark}")
            if co_msg: # 只有在交班信息不为空时才显示
                report_lines.append(f"    {'Handover Info:':<12} {co_msg}")
        else:
            # 如果没找到，说明当前无人居住
            report_lines.append(f"  - Room {room}: [Currently Vacant]")

    report_lines.append("\n" + "-" * 70)
    return "\n".join(report_lines)


# --- 主程序入口 (已重构，先加载数据再执行各项查询) ---
if __name__ == "__main__":
    print("--- Room History Records Query Tool ---")
    #room_input = input("请输入一个或多个房间号或楼层模式 (如 'A2*', 'B*', 用空格或逗号分隔): ")
    room_input = 'A212, B202 C303 A2* A16*' # 示例输入

    # 使用正则表达式分割输入，并清除空字符串
    # 例如，'A101, B202 C303 A2*' -> ['A101', 'B202', 'C303', 'A2*']
    room_list = [r.strip() for r in re.split(r'[\s,]+', room_input) if r.strip()]

    # 1. 调用查询函数
    found_records = query_records_by_room(FILE_PATH, room_list)

    # 2. 调用格式化函数
    final_string = format_string(
        found_records,
        room_list, # 将处理后的输入列表传递给格式化函数
        ROOM_TYPE_NAMES # 传递房间类型名称映射
    )

    # 3. 打印结果
    print(final_string)

    print("\n" + "=" * 80)
    print("Feature 2: Query nearby room occupancy status")
    target_room_for_nearby_check = 'A1606' # 示例目标房间

    # 调用查询函数
    nearby_query_result = query_nearby_rooms_status(FILE_PATH, target_room_for_nearby_check)

    # 调用格式化函数
    nearby_report = format_nearby_status(nearby_query_result, target_room_for_nearby_check)

    # 打印结果
    print(nearby_report)
    print("=" * 80)