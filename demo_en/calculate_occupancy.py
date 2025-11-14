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
            # 确保每行数据与header长度一致，不足的用空字符串填充
            if len(row_data) < len(header):
                row_data.extend([''] * (len(header) - len(row_data)))
            data.append(row_data)

        df = pd.DataFrame(data, columns=header)
        return df
    except Exception as e:
        print(f"Error parsing XML file: {e}") # 翻译：解析XML文件时发生错误
        return None


def calculate_occupancy_rate(file_path: str, start_date_str: str, end_date_str: str, total_rooms: int,
                             show_details: bool = False):
    """
    计算指定时间范围内的酒店入住率和出租率，并可选择返回每日详情字符串。
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return None, "Error: Incorrect date format. Please use 'YYYY-MM-DD'." # 翻译：错误: 日期格式不正确，请使用 'YYYY-MM-DD' 格式。

    if start_date > end_date:
        return None, "Error: Start date cannot be later than end date." # 翻译：错误: 开始日期不能晚于结束日期。

    try:
        df = parse_spreadsheetml(file_path)
        if df is None or df.empty:
            return None, "Error: Failed to parse data from the XML file." # 翻译：错误: 无法从XML文件中解析出数据。
    except FileNotFoundError:
        return None, f"Error: File not found -> {file_path}" # 翻译：错误: 文件未找到

    required_cols = ['sta', 'rmno', 'arr', 'dep']
    if not all(col in df.columns for col in required_cols):
        return None, f"Error: Missing required columns in the file. Required: {required_cols}" # 翻译：错误: 文件中缺少必要的列。需要:

    # M# <--- 修改: 筛选状态为 'I' (在住) 或 'R' (预定) 的记录
    df_filtered = df[df['sta'].isin(['I', 'R'])].copy()
    df_filtered.dropna(subset=['arr', 'dep', 'rmno'], inplace=True)
    df_filtered = df_filtered[df_filtered['rmno'] != '']

    # 尝试将Excel序列日期转换为数值，无法转换的变为NaN
    df_filtered['arr'] = pd.to_numeric(df_filtered['arr'], errors='coerce')
    df_filtered['dep'] = pd.to_numeric(df_filtered['dep'], errors='coerce')
    # 删除arr或dep为NaN的行
    df_filtered.dropna(subset=['arr', 'dep'], inplace=True)

    # 将Excel序列日期（浮点数）转换为datetime.date对象
    df_filtered['arr_date'] = pd.to_datetime(df_filtered['arr'], unit='D', origin='1899-12-30').dt.date
    df_filtered['dep_date'] = pd.to_datetime(df_filtered['dep'], unit='D', origin='1899-12-30').dt.date

    # --- 详细计算过程 ---
    details_log = ""
    if show_details:
        details_log += "\n--- Daily In-house and Reservation Details ---\n"  # 翻译：--- 每日入住与预定详情 ---

    total_occupied_room_nights = 0
    total_reserved_room_nights = 0  # M# <--- 新增: 用于累计预定房晚数
    # 生成查询日期范围
    date_range = pd.date_range(start=start_date, end=end_date, freq='D').date

    for day in date_range:
        # 筛选出当天所有相关记录 (包括在住和预定)
        daily_records_df = df_filtered[
            (df_filtered['arr_date'] <= day) & (df_filtered['dep_date'] > day)
            ]

        # M# <--- 修改: 分别计算在住和预定的房间数
        inhouse_rooms_on_day = daily_records_df[daily_records_df['sta'] == 'I']['rmno'].unique()
        reserved_rooms_on_day = daily_records_df[daily_records_df['sta'] == 'R']['rmno'].unique()

        inhouse_rooms_count = len(inhouse_rooms_on_day)
        reserved_rooms_count = len(reserved_rooms_on_day)

        total_occupied_room_nights += inhouse_rooms_count
        total_reserved_room_nights += reserved_rooms_count

        if show_details:
            # M# <--- 修改: 每日详情现在同时显示在住和预定数量
            details_log += (
                f"Date: {day} | In-house Rooms: {inhouse_rooms_count:<3} | Reserved Rooms: {reserved_rooms_count:<3} | " # 翻译：日期: | 在住房间数: | 预定房间数:
                f"Roomnights occ: {(inhouse_rooms_count / total_rooms) * 100 if total_rooms > 0 else 0:.2f}% "
                f"Application occ: {((inhouse_rooms_count + reserved_rooms_count) / total_rooms) * 100 if total_rooms > 0 else 0:.2f}%\n"
            )

    num_days = (end_date - start_date).days + 1
    total_available_room_nights = total_rooms * num_days

    # 入住率 (仅基于在住)
    occupancy_rate = (
                             total_occupied_room_nights / total_available_room_nights) * 100 if total_available_room_nights > 0 else 0

    # 计算出租率 (在住 + 预定)
    rental_rate = ((
                               total_occupied_room_nights + total_reserved_room_nights) / total_available_room_nights) * 100 if total_available_room_nights > 0 else 0

    result_data = {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "days_in_range": num_days,
        "total_available_room_nights": total_available_room_nights,
        "total_occupied_room_nights": total_occupied_room_nights,
        "total_reserved_room_nights": total_reserved_room_nights,  # M# <--- 新增
        "occupancy_rate_percentage": occupancy_rate,
        "rental_rate_percentage": rental_rate  # M# <--- 新增
    }

    return result_data, details_log


def format_result_to_string(result_data: dict, details_log: str = "") -> str:
    """
    将计算结果和详细日志格式化为单个字符串。
    """
    if not result_data:
        return ""

    report_string = details_log

    report_string += "\n--- Calculation Results ---\n" # 翻译：--- 计算结果 ---
    report_string += f"Query Range: {result_data['start_date']} to {result_data['end_date']} ({result_data['days_in_range']} days)\n" # 翻译：查询范围: ... 天)
    report_string += f"Total Available Room Nights: {result_data['total_available_room_nights']:,}\n" # 翻译：总可用房晚数:
    report_string += f"Actual In-house Room Nights: {result_data['total_occupied_room_nights']:,}\n" # 翻译：实际入住房晚数:
    report_string += f"Reserved Room Nights: {result_data['total_reserved_room_nights']:,}\n"  # 翻译：预定房晚数:
    report_string += "------------------\n"  # M# <--- 新增: 分隔线
    report_string += "--- Occupancy Situation ---\n" # 翻译：--- 出租情况 ---
    report_string += f"Roomnights occ (excluding booked but not yet in-house): {result_data['occupancy_rate_percentage']:.2f}%\n"  # 翻译：Roomnights occ (不包含签约但未入住):
    report_string += f"Application occ (including booked but not yet in-house): {result_data['rental_rate_percentage']:.2f}%\n"  # 翻译：Application occ (包含签约但为入住):
    report_string += "------------------\n"

    return report_string


# --- 主程序入口 ---
if __name__ == "__main__":
    FILE_PATH = 'master_base.xml'
    TOTAL_ROOMS = 579

    print("--- Hotel Occupancy and Rental Rate Calculator ---")  # 翻译：--- 酒店入住率与出租率计算器 ---

    '''start_input = input("Please enter the start date (YYYY-MM-DD): ") # 翻译：请输入开始日期 (YYYY-MM-DD):
    end_input = input("Please enter the end date (YYYY-MM-DD): ") # 翻译：请输入结束日期 (YYYY-MM-DD):
    details_input = input("Include daily detailed calculation process? (y/n, default n): ").lower() # 翻译：是否包含每日详细计算过程? (y/n，默认为 n):'''

    start_input = "2025-08-01"
    end_input = "2025-08-05"
    details_input = "y"

    show_details_flag = True if details_input == 'y' else False

    result_dict, details_string = calculate_occupancy_rate(
        FILE_PATH, start_input, end_input, TOTAL_ROOMS, show_details=show_details_flag
    )

    if result_dict is None:
        print(details_string)
    else:
        final_report_string = format_result_to_string(result_dict, details_string)
        print(final_report_string)

        '''try:
            with open("occupancy_report.txt", "w", encoding="utf-8") as f:
                f.write(final_report_string)
            print("Report successfully saved to file: occupancy_report.txt") # 翻译：报告已成功保存到文件: occupancy_report.txt
        except Exception as e:
            print(f"Error writing report file: {e}") # 翻译：写入报告文件时出错:'''