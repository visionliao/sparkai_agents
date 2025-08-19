import pandas as pd
from datetime import datetime, timedelta
from lxml import etree


def parse_spreadsheetml(file_path: str) -> pd.DataFrame:
    """
    使用 lxml 解析 SpreadsheetML 2003 XML 文件并返回一个 pandas DataFrame。
    """
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = root.findall('.//ss:Worksheet/ss:Table/ss:Row', namespaces=ns)

        if not rows:
            return pd.DataFrame()

        header_row = rows[0]
        header = []
        for cell in header_row.findall('ss:Cell', namespaces=ns):
            data_element = cell.find('ss:Data', namespaces=ns)
            col_name = data_element.text.strip() if data_element is not None and data_element.text is not None else ""
            header.append(col_name)

        data = []
        for row in rows[1:]:
            row_data = []
            cells = row.findall('ss:Cell', namespaces=ns)
            for cell in cells:
                cell_text_element = cell.find('ss:Data', namespaces=ns)
                cell_value = cell_text_element.text if cell_text_element is not None and cell_text_element.text is not None else ''
                row_data.append(cell_value)
            if len(row_data) < len(header):
                row_data.extend([''] * (len(header) - len(row_data)))
            data.append(row_data)

        df = pd.DataFrame(data, columns=header)
        return df
    except Exception as e:
        print(f"解析XML文件时发生错误: {e}")
        return None


def calculate_occupancy_rate(file_path: str, start_date_str: str, end_date_str: str, total_rooms: int,
                             show_details: bool = False):
    """
    计算指定时间范围内的酒店入住率，并可选择返回每日详情字符串。
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return None, "错误: 日期格式不正确，请使用 'YYYY-MM-DD' 格式。"

    if start_date > end_date:
        return None, "错误: 开始日期不能晚于结束日期。"

    try:
        df = parse_spreadsheetml(file_path)
        if df is None or df.empty:
            return None, "错误: 无法从XML文件中解析出数据。"
    except FileNotFoundError:
        return None, f"错误: 文件未找到 -> {file_path}"

    required_cols = ['sta', 'rmno', 'arr', 'dep']
    if not all(col in df.columns for col in required_cols):
        return None, f"错误: 文件中缺少必要的列。需要: {required_cols}"

    df_inhouse = df[df['sta'] == 'I'].copy()
    df_inhouse.dropna(subset=['arr', 'dep', 'rmno'], inplace=True)
    df_inhouse = df_inhouse[df_inhouse['rmno'] != '']

    df_inhouse['arr'] = pd.to_numeric(df_inhouse['arr'], errors='coerce')
    df_inhouse['dep'] = pd.to_numeric(df_inhouse['dep'], errors='coerce')
    df_inhouse.dropna(subset=['arr', 'dep'], inplace=True)

    df_inhouse['arr_date'] = pd.to_datetime(df_inhouse['arr'], unit='D', origin='1899-12-30').dt.date
    df_inhouse['dep_date'] = pd.to_datetime(df_inhouse['dep'], unit='D', origin='1899-12-30').dt.date

    # --- 详细计算过程 ---
    details_log = ""
    if show_details:
        details_log += "\n--- 每日入住详情 ---\n"

    total_occupied_room_nights = 0
    date_range = pd.date_range(start=start_date, end=end_date, freq='D').date

    for day in date_range:
        occupied_rooms_on_day_df = df_inhouse[
            (df_inhouse['arr_date'] <= day) & (df_inhouse['dep_date'] > day)
            ]

        unique_occupied_rooms = occupied_rooms_on_day_df['rmno'].unique()
        unique_occupied_rooms_count = len(unique_occupied_rooms)

        total_occupied_room_nights += unique_occupied_rooms_count

        if show_details:
            room_list_str = ", ".join(unique_occupied_rooms[:10])
            if len(unique_occupied_rooms) > 10:
                room_list_str += f", ... (共 {unique_occupied_rooms_count} 间)"
            elif unique_occupied_rooms_count == 0:
                room_list_str = "无"
            details_log += f"日期: {day} | 当日入住房间数: {unique_occupied_rooms_count:<3} | 房间号: {room_list_str}\n"

    num_days = (end_date - start_date).days + 1
    total_available_room_nights = total_rooms * num_days
    occupancy_rate = (
                                 total_occupied_room_nights / total_available_room_nights) * 100 if total_available_room_nights > 0 else 0

    result_data = {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "days_in_range": num_days,
        "total_available_room_nights": total_available_room_nights,
        "total_occupied_room_nights": total_occupied_room_nights,
        "occupancy_rate_percentage": occupancy_rate
    }

    return result_data, details_log


def format_result_to_string(result_data: dict, details_log: str = "") -> str:
    """
    将计算结果和详细日志格式化为单个字符串。
    """
    if not result_data:
        return ""

    # 首先添加详细日志（如果存在）
    report_string = details_log

    # 然后添加最终的摘要报告
    report_string += "\n--- 计算结果 ---\n"
    report_string += f"查询范围: {result_data['start_date']} 到 {result_data['end_date']} ({result_data['days_in_range']} 天)\n"
    report_string += f"总可用房晚数: {result_data['total_available_room_nights']:,}\n"
    report_string += f"实际入住房晚数: {result_data['total_occupied_room_nights']:,}\n"
    report_string += f"入住率: {result_data['occupancy_rate_percentage']:.2f}%\n"
    report_string += "------------------\n"

    return report_string


# --- 主程序入口 ---
if __name__ == "__main__":
    FILE_PATH = 'master_base.xml'
    TOTAL_ROOMS = 579

    print("--- 酒店入住率计算器 ---")

    start_input = input("请输入开始日期 (YYYY-MM-DD): ")
    end_input = input("请输入结束日期 (YYYY-MM-DD): ")
    details_input = input("是否包含每日详细计算过程? (y/n，默认为 n): ").lower()

    show_details_flag = True if details_input == 'y' else False

    # 函数现在返回两个值：一个字典（数据）和一个字符串（日志）
    result_dict, details_string = calculate_occupancy_rate(
        FILE_PATH, start_input, end_input, TOTAL_ROOMS, show_details=show_details_flag
    )

    # 检查是否有错误发生
    if result_dict is None:
        # 如果出错，details_string 会包含错误信息
        print(details_string)
    else:
        # --- 将所有输出格式化并存入一个字符串变量 ---
        final_report_string = format_result_to_string(result_dict, details_string)

        # 1. 打印这个字符串变量到控制台
        print(final_report_string)

        # 2. 现在你可以对这个字符串变量做任何你想做的事情
        # 例如，写入一个文件
        '''try:
            with open("occupancy_report.txt", "w", encoding="utf-8") as f:
                f.write(final_report_string)
            print("报告已成功保存到文件: occupancy_report.txt")
        except Exception as e:
            print(f"写入报告文件时出错: {e}")'''