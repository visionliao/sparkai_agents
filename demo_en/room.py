import pandas as pd
from datetime import datetime, timedelta
from lxml import etree

# --- 1. 配置区域 (请根据你的实际情况修改这里) ---

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

ROOM_TYPE_NAMES = {
    '1BD': "One Bedroom Deluxe",
    '1BP': "One Bedroom Premier",
    '2BD': "Two Bedrooms Executive",
    '3BR': "Three-bedroom",
    'STD': "Studio Deluxe",
    'STE': "Studio Executive",
    'STP': "Studio Premier"
}

FILE_PATH = 'master_base.xml'


# --- 2. 数据解析函数 ---

def parse_spreadsheetml(file_path: str) -> pd.DataFrame:
    """
    使用 lxml 解析 SpreadsheetML 2003 XML 文件并返回一个 pandas DataFrame。
    此函数与原代码保持一致。
    """
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = root.findall('.//ss:Worksheet/ss:Table/ss:Row', namespaces=ns)

        if not rows: return pd.DataFrame()

        header_row = rows[0]
        header = []
        for cell in header_row.findall('ss:Cell', namespaces=ns):
            data_element = cell.find('ss:Data', namespaces=ns)
            col_name = data_element.text.strip() if data_element is not None and data_element.text is not None else ""
            header.append(col_name)

        data = []
        for row in rows[1:]:
            row_data = [
                (cell.find('ss:Data', namespaces=ns).text if cell.find('ss:Data',
                                                                       namespaces=ns) is not None and cell.find(
                    'ss:Data', namespaces=ns).text is not None else '')
                for cell in row.findall('ss:Cell', namespaces=ns)
            ]
            if len(row_data) < len(header):
                row_data.extend([''] * (len(header) - len(row_data)))
            data.append(row_data)

        return pd.DataFrame(data, columns=header)
    except Exception as e:
        # 输出改为英文
        print(f"Error parsing XML file: {e}")
        return None


# --- 3. 核心分析函数 (返回结果列表) ---
def analyze_room_type_performance(file_path: str, start_date_str: str, end_date_str: str, room_counts: dict,
                                  room_areas: dict):
    """
    计算指定时间范围内的各户型经营表现。
    - 将输入从一个时间点改为一个时间段 (start_date_str, end_date_str)。
    - 在租数与付费在租数改为期末在租数与期末付费在租数。
    - 后续的租金、坪效、空置率计算均改为在给定的时间段内按照实际晚数计算。
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        # 输出改为英文
        return f"Error: Incorrect date format. Please use 'YYYY-MM-DD'."

    if start_date > end_date:
        # 输出改为英文
        return "Error: Start date cannot be later than end date."

    num_days_in_period = (end_date - start_date).days + 1

    df_or_error = parse_spreadsheetml(file_path)
    if isinstance(df_or_error, str):
        return df_or_error
    df = df_or_error

    if df is None or df.empty:
        # 输出改为英文
        return "Failed to load data, analysis aborted."

    required_cols = ['id', 'sta', 'rmno', 'rmtype', 'arr', 'dep', 'full_rate_long', 'create_datetime']
    if not all(col in df.columns for col in required_cols):
        # 输出改为英文
        return f"Error: The file is missing required columns. Needed: {required_cols}"

    # --- 数据预处理 (与原代码基本一致) ---
    df_inhouse = df[df['sta'].isin(['I', 'R'])].copy()
    for col in ['id', 'arr', 'dep', 'full_rate_long', 'create_datetime']:
        df_inhouse[col] = pd.to_numeric(df_inhouse[col], errors='coerce')
    df_inhouse.dropna(subset=['id', 'arr', 'dep', 'rmno', 'rmtype', 'full_rate_long', 'create_datetime'], inplace=True)
    df_inhouse = df_inhouse[df_inhouse['rmno'] != '']
    df_inhouse['arr_date'] = pd.to_datetime(df_inhouse['arr'], unit='D', origin='1899-12-30').dt.date
    df_inhouse['dep_date'] = pd.to_datetime(df_inhouse['dep'], unit='D', origin='1899-12-30').dt.date
    df_inhouse['create_dt'] = pd.to_datetime(df_inhouse['create_datetime'], unit='D', origin='1899-12-30')

    # --- 计算期末在租数和期末付费在租数 (End-of-period snapshot) ---
    # 筛选在结束日期当天仍在租的房间
    df_end_of_period_occupied = df_inhouse[
        (df_inhouse['arr_date'] <= end_date) & (df_inhouse['dep_date'] > end_date)
        ].copy()

    df_end_of_period_occupied_unique = pd.DataFrame()
    if not df_end_of_period_occupied.empty:
        # 优先级：付费 > 创建日期最新
        df_end_of_period_occupied['rent_priority'] = (df_end_of_period_occupied['full_rate_long'] > 0).astype(int)
        df_end_of_period_occupied_sorted = df_end_of_period_occupied.sort_values(
            by=['rmno', 'rent_priority', 'create_dt'], ascending=[True, False, False]
        )
        df_end_of_period_occupied_unique = df_end_of_period_occupied_sorted.drop_duplicates(subset='rmno', keep='first')

    # --- 识别在分析期间内所有重叠的预订 (用于最高/最低租金的显示) ---
    # 这些是所有在期间内有重叠的独立预订记录（按'id'去重），用于查找最高/最低月租金。
    df_all_bookings_in_period = df_inhouse[
        (df_inhouse['arr_date'] <= end_date) & (df_inhouse['dep_date'] > start_date)
        ].copy().drop_duplicates(subset='id', keep='first')  # 确保每个booking ID只出现一次

    # === 修改开始 ===
    # 如果在整个分析期间内没有找到任何相关的预订记录（即没有预订与该时间段有任何重叠），
    # 则返回一个空列表。这会触发 format_analysis_to_string 函数中的特定消息。
    if df_all_bookings_in_period.empty:
        return []  # 返回空列表，表示没有找到与该期间相关的经营活动记录
    # === 修改结束 ===

    analysis_results = []
    # 合并所有户型代码，确保报告完整性
    # 确保即使 df_inhouse 为空，也能获取配置的户型代码
    all_room_types = set(room_counts.keys()) | set(room_areas.keys())
    if not df_inhouse.empty:
        all_room_types |= set(df_inhouse['rmtype'].unique())

    for rmtype in sorted(list(all_room_types)):
        total_supply = room_counts.get(rmtype, 0)
        area = room_areas.get(rmtype, 0)

        # --- 1. 期末在租数与期末付费在租数 ---
        occupied_rooms_end_of_period_df = df_end_of_period_occupied_unique[
            df_end_of_period_occupied_unique['rmtype'] == rmtype
            ]
        end_of_period_occupied_count = len(occupied_rooms_end_of_period_df)
        end_of_period_rented_count_for_calc = len(
            occupied_rooms_end_of_period_df[occupied_rooms_end_of_period_df['full_rate_long'] > 0]
        )
        end_of_period_vacancy_rate = ((
                                                  total_supply - end_of_period_occupied_count) / total_supply) * 100 if total_supply > 0 else 100

        # --- 2. 期间的房晚数和租金计算 (按实际晚数) ---
        total_occupied_room_nights_for_rmtype = 0  # 期间总入住房晚数
        total_paid_room_nights_for_rmtype = 0  # 期间总付费房晚数
        total_rent_for_rmtype_period = 0  # 期间总租金 (按日租金累加)

        # 遍历分析期间内的每一天
        for day in pd.date_range(start=start_date, end=end_date, freq='D').date:
            # 获取当天该户型所有在租的记录
            daily_occupied_df = df_inhouse[
                (df_inhouse['arr_date'] <= day) & (df_inhouse['dep_date'] > day) &
                (df_inhouse['rmtype'] == rmtype)
                ].copy()

            daily_unique_occupied_rooms = pd.DataFrame()
            if not daily_occupied_df.empty:
                # 对当天在租的房间进行去重和优先级处理 (付费优先，创建日期最新优先)
                daily_occupied_df['rent_priority'] = (daily_occupied_df['full_rate_long'] > 0).astype(int)
                daily_occupied_df_sorted = daily_occupied_df.sort_values(
                    by=['rmno', 'rent_priority', 'create_dt'], ascending=[True, False, False]
                )
                daily_unique_occupied_rooms = daily_occupied_df_sorted.drop_duplicates(subset='rmno', keep='first')

                # 累加当天的在租房数到总入住房晚数
                total_occupied_room_nights_for_rmtype += len(daily_unique_occupied_rooms)

                daily_paid_rooms = pd.DataFrame()  # 初始化 daily_paid_rooms 为空 DataFrame

                if not daily_unique_occupied_rooms.empty:  # 只有当 daily_unique_occupied_rooms 不为空时才进行筛选
                    # 筛选当天付费的在租房间
                    daily_paid_rooms = daily_unique_occupied_rooms[daily_unique_occupied_rooms['full_rate_long'] > 0]

                # 累加当天的付费房数到总付费房晚数
                total_paid_room_nights_for_rmtype += len(daily_paid_rooms)

                # 累加每个付费房晚的日租金到期间总租金
                # 如果 daily_paid_rooms 是空的，这个循环将不会执行，这是正确的行为
                for idx, row in daily_paid_rooms.iterrows():
                    monthly_rate = row['full_rate_long']
                    total_rent_for_rmtype_period += (monthly_rate / 30.0)

        # --- 3. 计算期间平均值和比率 ---
        # 期间平均日租金
        avg_daily_rent = total_rent_for_rmtype_period / total_paid_room_nights_for_rmtype if total_paid_room_nights_for_rmtype > 0 else 0
        # 期间坪效 (元/m²/日)
        ping_xiao_daily = avg_daily_rent / area if area > 0 and avg_daily_rent > 0 else 0

        ### 新增 ###
        # 计算期间总付费面积房晚数，用于后续计算总体坪效
        total_paid_area_nights_for_rmtype = total_paid_room_nights_for_rmtype * area

        # 期间空置率
        total_available_room_nights_for_rmtype = total_supply * num_days_in_period
        vacancy_rate_period = ((
                                           total_available_room_nights_for_rmtype - total_occupied_room_nights_for_rmtype) / total_available_room_nights_for_rmtype) * 100 if total_available_room_nights_for_rmtype > 0 else 100

        # --- 4. 最高/最低月租金 (从在期间内所有重叠的付费预订的完整月租金中查找) ---
        # 筛选出属于当前户型且有付费记录的所有相关预订
        relevant_paid_bookings_for_rmtype = df_all_bookings_in_period[
            (df_all_bookings_in_period['rmtype'] == rmtype) &
            (df_all_bookings_in_period['full_rate_long'] > 0)
            ]

        max_rent_record, min_rent_record = None, None
        if not relevant_paid_bookings_for_rmtype.empty:
            max_rent_row = relevant_paid_bookings_for_rmtype.loc[
                relevant_paid_bookings_for_rmtype['full_rate_long'].idxmax()]
            min_rent_row = relevant_paid_bookings_for_rmtype.loc[
                relevant_paid_bookings_for_rmtype['full_rate_long'].idxmin()]
            max_rent_record = {'rent': max_rent_row['full_rate_long'], 'id': int(max_rent_row['id']),
                               'arr': max_rent_row['arr_date'], 'dep': max_rent_row['dep_date']}
            min_rent_record = {'rent': min_rent_row['full_rate_long'], 'id': int(min_rent_row['id']),
                               'arr': min_rent_row['arr_date'], 'dep': min_rent_row['dep_date']}

        # 结果字典的键改为英文
        analysis_results.append({
            'Room Type Code': rmtype,
            'Total Supply': total_supply,
            'Occupied at End of Period': end_of_period_occupied_count,
            'Paid Occupied at End of Period': end_of_period_rented_count_for_calc,
            'Vacancy Rate at End of Period (%)': end_of_period_vacancy_rate,
            'Total Occupied Room Nights (Period)': total_occupied_room_nights_for_rmtype,
            'Total Paid Room Nights (Period)': total_paid_room_nights_for_rmtype,
            'Vacancy Rate (Period %)': vacancy_rate_period,
            'Total Rent (Period)': total_rent_for_rmtype_period,
            'Avg Daily Rate (Period)': avg_daily_rent,
            'Area (m²)': area,
            'Efficiency (per m²/day)': ping_xiao_daily,
            'max_rent_info': max_rent_record,
            'min_rent_info': min_rent_record,
            'Total Paid Area Nights (Period)': total_paid_area_nights_for_rmtype
        })

    return analysis_results


# --- 4. 修改后的格式化函数 ---
def format_analysis_to_string(analysis_results: list, start_date_str: str, end_date_str: str, room_names: dict) -> str:
    """
    将分析结果列表格式化为一个易于阅读的多行字符串报告。
    此函数已修改以适应时间段分析结果的显示。
    """
    # 输出改为英文
    if isinstance(analysis_results, str):  # 如果传入的是错误信息
        return analysis_results

    if not analysis_results:
        # 当 analyze_room_type_performance 返回空列表时，显示此消息
        return f"No relevant room records found for the date range {start_date_str} to {end_date_str}."

    report_lines = []
    report_lines.append(f"--- Room Type Performance Analysis (Period: {start_date_str} to {end_date_str}) ---")

    # 过滤掉那些所有关键指标都为0或N/A的户型，只报告有实际数据的户型
    # 关键指标包括期末在租数、期间总入住房晚数或期间总租金
    # 使用英文键进行过滤
    meaningful_results = [
        r for r in analysis_results if r['Occupied at End of Period'] >= 0 or
                                       r['Total Occupied Room Nights (Period)'] > 0 or
                                       r['Total Rent (Period)'] > 0
    ]

    if not meaningful_results:
        # 如果虽然存在户型配置，但所有户型在指定期间都没有实际经营活动，也显示此消息
        return f"Although room types are configured, no actual operational activity was found for the date range {start_date_str} to {end_date_str}."

    # 使用英文键和英文文本生成报告
    for result in meaningful_results:
        room_type_name = room_names.get(result['Room Type Code'], result['Room Type Code'])
        report_lines.append(f"\n==================== Room Type: {room_type_name} ====================")

        # 期末数据
        line1_ep = f"End-of-Period Supply & Occupancy: Total {result['Total Supply']} rooms, Occupied {result['Occupied at End of Period']}, of which {result['Paid Occupied at End of Period']} are paid"
        line2_ep = f"End-of-Period Vacancy Rate   : {result['Vacancy Rate at End of Period (%)']:.2f}%"
        report_lines.extend([line1_ep, line2_ep, "---"])

        # 期间数据 (按房晚计算)
        line1_period = f"Period Room Nights    : Total Occupied {result['Total Occupied Room Nights (Period)']:,} nights, Total Paid {result['Total Paid Room Nights (Period)']:,} nights"
        line2_period = f"Period Vacancy Rate : {result['Vacancy Rate (Period %)']:.2f}%"
        report_lines.extend([line1_period, line2_period, "---"])

        # 期间租金和坪效
        line3 = f"Period Revenue      : Total Rent {result['Total Rent (Period)']:,.2f}, Avg Daily Rate {result['Avg Daily Rate (Period)']:,.2f}, Avg Monthly (30-day) {(30 * result['Avg Daily Rate (Period)']):,.2f}"
        line4 = f"Efficiency          : {result['Efficiency (per m²/day)']:,.2f} per m²/day (based on area of {result['Area (m²)']} m²)"
        report_lines.extend([line3, line4, "---"])

        # 最高/最低月租金 (仍然显示原始月租金及预订信息)
        if result['max_rent_info']:
            max_info = result['max_rent_info']
            line5 = f"Highest Monthly Rent: {max_info['rent']:,.2f} (Booking ID: {int(max_info['id'])}, Arrival: {max_info['arr']}, Departure: {max_info['dep']})"
        else:
            line5 = "Highest Monthly Rent: N/A (No paid records in period)"
        report_lines.append(line5)

        if result['min_rent_info']:
            min_info = result['min_rent_info']
            line6 = f"Lowest Monthly Rent : {min_info['rent']:,.2f} (Booking ID: {int(min_info['id'])}, Arrival: {min_info['arr']}, Departure: {min_info['dep']})"
        else:
            line6 = "Lowest Monthly Rent : N/A (No paid records in period)"
        report_lines.append(line6)

    # --- 总体概要 (基于期间房晚和租金) ---
    # 总体概要也应该基于 meaningful_results 来计算
    total_rent_all_types = sum(r['Total Rent (Period)'] for r in meaningful_results)
    total_paid_room_nights_all_types = sum(r['Total Paid Room Nights (Period)'] for r in meaningful_results)

    ### 新增/修改 ###
    total_paid_area_nights_all_types = sum(r['Total Paid Area Nights (Period)'] for r in meaningful_results)

    overall_avg_daily_rent = (total_rent_all_types / total_paid_room_nights_all_types
                              if total_paid_room_nights_all_types > 0 else 0)

    overall_ping_xiao = (total_rent_all_types / total_paid_area_nights_all_types
                         if total_paid_area_nights_all_types > 0 else 0)

    report_lines.append("\n==================== Overall Summary ====================")
    summary_line_adr = (f"Overall Avg Daily Rate (All Types): {overall_avg_daily_rent:,.2f} "
                        f"(based on {total_paid_room_nights_all_types:,} total paid room nights)")

    summary_line_pingxiao = f"Overall Efficiency (All Types)  : {overall_ping_xiao:,.2f} per m²/day (based on total rent / total paid area nights)"

    report_lines.append(summary_line_adr)
    report_lines.append(summary_line_pingxiao)  # 添加坪效行
    # --- 总体概要结束 ---

    report_lines.append("========================================================")

    return "\n".join(report_lines)


# --- 主程序入口 ---
if __name__ == "__main__":
    # 输出改为英文
    print("--- Room Type Performance Analysis Tool ---")
    # 为了测试，可以取消注释以下两行，让用户输入日期
    # start_date_input = input("Enter the start date for analysis (YYYY-MM-DD): ")
    # end_date_input = input("Enter the end date for analysis (YYYY-MM-DD): ")

    # 默认测试日期范围
    start_date_input = "2025-08-01"
    end_date_input = "2025-08-31"

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
    print(final_report_string)