# --- START OF FILE query_checkins.py ---

import pandas as pd
from datetime import datetime
from lxml import etree
import re

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


# --- 数据解析函数 ---
def parse_spreadsheetml(file_path: str):
    """
    Parses a SpreadsheetML 2003 XML file and converts it into a Pandas DataFrame.
    """
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = root.findall('.//ss:Worksheet/ss:Table/ss:Row', namespaces=ns)
        if not rows:
            return pd.DataFrame()
        header_row = rows[0]
        header = [cell.find('ss:Data', namespaces=ns).text.strip() if cell.find('ss:Data',
                                                                                namespaces=ns) is not None and cell.find(
            'ss:Data', namespaces=ns).text is not None else "" for cell in header_row.findall('ss:Cell', namespaces=ns)]
        data = []
        for row in rows[1:]:
            row_data = [(cell.find('ss:Data', namespaces=ns).text if cell.find('ss:Data',
                                                                               namespaces=ns) is not None and cell.find(
                'ss:Data', namespaces=ns).text is not None else '') for cell in row.findall('ss:Cell', namespaces=ns)]
            if len(row_data) < len(header):
                row_data.extend([''] * (len(header) - len(row_data)))
            data.append(row_data)
        return pd.DataFrame(data, columns=header)
    except FileNotFoundError:
        return f"Error: File not found. Please ensure '{file_path}' exists in the current directory."
    except etree.XMLSyntaxError:
        return f"Error: XML file '{file_path}' is corrupted and cannot be parsed."
    except Exception as e:
        return f"An unknown error occurred while parsing the XML file: {e}"


# --- 核心查询函数 (已更新为聚合用户ID) ---
def query_checkin_records(file_path: str, start_date_str: str, end_date_str: str, status_filter: str = 'ALL'):
    """
    Queries check-in records, deduplicates, and aggregates all user IDs for the same room within the time period.
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return "Error: Incorrect date format. Please use 'YYYY-MM-DD' format."
    if start_date > end_date:
        return "Error: Start date cannot be later than end date."

    df_or_error = parse_spreadsheetml(file_path)
    if isinstance(df_or_error, str):
        return df_or_error
    df = df_or_error
    if df.empty:
        return "Failed to load any data from the file."

    required_cols = ['id', 'sta', 'rmno', 'rmtype', 'arr', 'dep', 'full_rate_long', 'is_long', 'create_datetime',
                     'remark', 'co_msg']
    if not all(col in df.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in df.columns]
        return f"Error: Missing required columns in the file. Needed: {required_cols}, Missing: {missing_cols}"

    for col in ['id', 'arr', 'dep', 'full_rate_long', 'create_datetime']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['arr', 'rmno', 'create_datetime', 'id'], inplace=True)

    df['arr_date'] = pd.to_datetime(df['arr'], unit='D', origin='1899-12-30').dt.date
    df['dep_date'] = pd.to_datetime(df['dep'], unit='D', origin='1899-12-30').dt.date
    df['create_dt'] = pd.to_datetime(df['create_datetime'], unit='D', origin='1899-12-30')

    checkin_records_df = df[(df['arr_date'] >= start_date) & (df['arr_date'] <= end_date)].copy()

    if status_filter != 'ALL':
        checkin_records_df = checkin_records_df[checkin_records_df['sta'] == status_filter]

    if not checkin_records_df.empty:
        # 步骤 1: 按房号聚合所有唯一的用户ID
        checkin_records_df['id_str'] = checkin_records_df['id'].astype(float).astype(int).astype(str)
        aggregated_ids = checkin_records_df.groupby('rmno')['id_str'].apply(lambda x: ', '.join(x.unique()))

        # 步骤 2: 找到每个房间的“代表性”记录
        checkin_records_df['rent_priority'] = (checkin_records_df['full_rate_long'] > 0).astype(int)
        sorted_records = checkin_records_df.sort_values(by=['rmno', 'rent_priority', 'create_dt'],
                                                        ascending=[True, False, False])
        unique_checkin_records = sorted_records.drop_duplicates(subset='rmno', keep='first').copy()

        # 步骤 3: 将聚合后的ID列表映射到代表性记录上
        unique_checkin_records['all_user_ids'] = unique_checkin_records['rmno'].map(aggregated_ids)

        return unique_checkin_records
    else:
        return checkin_records_df


# --- 辅助函数 ---
def sanitize_for_display(text):
    """
    Cleans strings, replacing control characters that might break table layout with spaces.
    """
    if not isinstance(text, str):
        return text
    control_char_regex = re.compile(r'[\x00-\x1F\x7F-\x9F\u2028\u2029]')
    return control_char_regex.sub(' ', text)


# --- 格式化输出函数 (已更新以显示聚合后的ID) ---
def format_records_to_string(records_df, start_date_str, end_date_str, room_names, status_filter):
    """
    Formats the processed DataFrame into an easy-to-read string report.
    """
    if isinstance(records_df, str):
        return records_df

    status_text = f"Status: {status_filter}" if status_filter != 'ALL' else "All Statuses"

    if records_df.empty:
        return f"No (deduplicated, {status_text}) check-in records found between {start_date_str} and {end_date_str}."

    records_df = records_df.copy()

    # 数据准备
    records_df['Room Type Name'] = records_df['rmtype'].map(room_names).fillna(records_df['rmtype'])
    records_df['Stay Type'] = records_df['is_long'].apply(lambda x: 'Long Stay' if x == 'T' else 'Short Stay')
    records_df['Rent/Rate'] = records_df['full_rate_long'].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A")
    records_df['remark'] = records_df['remark'].fillna('').apply(sanitize_for_display)
    records_df['co_msg'] = records_df['co_msg'].fillna('').apply(sanitize_for_display)
    records_df['all_user_ids'] = records_df['all_user_ids'].fillna('N/A')

    records_df_sorted = records_df.sort_values(by='arr_date')

    report_lines = []
    report_lines.append(f"--- Check-in Records Query Results ({start_date_str} to {end_date_str}, {status_text}) ---")
    report_lines.append(f"Found {len(records_df_sorted)} (deduplicated) records for rooms.\n")

    # 定义要显示的列和它们的标题
    display_columns = {
        'arr_date': 'Arrival Date',
        'dep_date': 'Departure Date',
        'rmno': 'Room No.',
        'Room Type Name': 'Room Type',
        'all_user_ids': 'All Associated User IDs',
        'Rent/Rate': 'Rent',
        'sta': 'Status',
        'remark': 'Remark',
        'co_msg': 'Handover Info'
    }

    # 调整pandas的显示选项，防止长文本被截断
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', 1200)

    # 生成主表格字符串
    table_string = records_df_sorted[list(display_columns.keys())].rename(columns=display_columns).to_string(
        index=False)
    report_lines.append(table_string)

    report_lines.append("\n" + "-" * 80)
    return "\n".join(report_lines)


# --- 主程序入口 ---
if __name__ == "__main__":
    print("--- Recent Check-in Records Query Tool ---")

    # 示例输入，您可以根据需要修改
    start_input = "2025-08-01"
    end_input = "2025-08-31"

    print(f"Query Date Range: {start_input} to {end_input}")

    # 用户交互式输入状态
    print("\nPlease select the record status to query:")
    print(" 1: I (Occupied)\n 2: O (Checked Out)\n 3: X (Canceled)\n 4: R (Reserved)\n 5: ALL (All Statuses, default)")

    # 为了方便测试，可以预设一个值，例如 '5' for ALL
    # status_choice = input("Enter option (1-5, press Enter for 5): ")
    status_choice = "5" # Example preset choice for testing
    if not status_choice:
        status_choice = '5'

    status_map = {'1': 'I', '2': 'O', '3': 'X', '4': 'R', '5': 'ALL'}
    selected_status = status_map.get(status_choice, 'ALL')

    print(f"Query Status: {selected_status}")

    # 执行查询
    found_records = query_checkin_records(FILE_PATH, start_input, end_input, status_filter=selected_status)

    # 生成报告
    final_report_string = format_records_to_string(found_records, start_input, end_input, ROOM_TYPE_NAMES,
                                                   status_filter=selected_status)

    # 打印最终报告
    print("\n" + "=" * 80)
    print(final_report_string)
    print("=" * 80)

    # 可选：将报告保存到文件
    '''if isinstance(found_records, pd.DataFrame) and not found_records.empty:
        try:
            output_filename = "checkin_report_aggregated.txt"
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(final_report_string)
            print(f"\nQuery report saved to {output_filename}")
        except Exception as e:
            print(f"\nError writing report file: {e}")'''