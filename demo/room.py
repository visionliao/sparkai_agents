import pandas as pd
from datetime import datetime
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

FILE_PATH = 'master_base.xml'


# --- 2. 数据解析函数 ---

def parse_spreadsheetml(file_path: str) -> pd.DataFrame:
    """
    使用 lxml 解析 SpreadsheetML 2003 XML 文件并返回一个 pandas DataFrame。
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
        print(f"解析XML文件时发生错误: {e}")
        return None


# --- 3. 核心分析函数 (返回结果列表) ---
def analyze_room_type_performance(file_path: str, as_of_date_str: str, room_counts: dict, room_areas: dict):
    try:
        as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
    except ValueError:
        return f"错误: 日期格式不正确，请使用 'YYYY-MM-DD' 格式。"

    df_or_error = parse_spreadsheetml(file_path)
    if isinstance(df_or_error, str):
        return df_or_error
    df = df_or_error

    if df is None or df.empty:
        return "未能加载数据，分析中止。"

    required_cols = ['id', 'sta', 'rmno', 'rmtype', 'arr', 'dep', 'full_rate_long', 'create_datetime']
    if not all(col in df.columns for col in required_cols):
        return f"错误: 文件中缺少必要的列。需要: {required_cols}"

    # ... (数据预处理和计算逻辑与之前完全相同)
    df_inhouse = df[df['sta'] == 'I'].copy()
    for col in ['id', 'arr', 'dep', 'full_rate_long', 'create_datetime']:
        df_inhouse[col] = pd.to_numeric(df_inhouse[col], errors='coerce')
    df_inhouse.dropna(subset=['id', 'arr', 'dep', 'rmno', 'rmtype', 'full_rate_long', 'create_datetime'], inplace=True)
    df_inhouse = df_inhouse[df_inhouse['rmno'] != '']
    df_inhouse['arr_date'] = pd.to_datetime(df_inhouse['arr'], unit='D', origin='1899-12-30').dt.date
    df_inhouse['dep_date'] = pd.to_datetime(df_inhouse['dep'], unit='D', origin='1899-12-30').dt.date
    df_inhouse['create_dt'] = pd.to_datetime(df_inhouse['create_datetime'], unit='D', origin='1899-12-30')

    df_occupied = df_inhouse[(df_inhouse['arr_date'] <= as_of_date) & (df_inhouse['dep_date'] > as_of_date)].copy()
    df_occupied['rent_priority'] = (df_occupied['full_rate_long'] > 0).astype(int)
    df_occupied_sorted = df_occupied.sort_values(by=['rmno', 'rent_priority', 'create_dt'],
                                                 ascending=[True, False, False])
    df_occupied_unique = df_occupied_sorted.drop_duplicates(subset='rmno', keep='first')

    analysis_results = []
    all_room_types = set(room_counts.keys()) | set(room_areas.keys()) | set(df_occupied_unique['rmtype'].unique())

    for rmtype in sorted(list(all_room_types)):
        total_supply = room_counts.get(rmtype, 0)
        area = room_areas.get(rmtype, 0)
        occupied_rooms_df = df_occupied_unique[df_occupied_unique['rmtype'] == rmtype]
        occupied_count = len(occupied_rooms_df)
        rented_rooms_df = occupied_rooms_df[occupied_rooms_df['full_rate_long'] > 0]
        rented_count_for_calc = len(rented_rooms_df)
        total_rent = rented_rooms_df['full_rate_long'].sum()
        avg_rent = total_rent / rented_count_for_calc if rented_count_for_calc > 0 else 0
        ping_xiao = avg_rent / area if area > 0 and avg_rent > 0 else 0
        vacancy_rate = ((total_supply - occupied_count) / total_supply) * 100 if total_supply > 0 else 100

        max_rent_record, min_rent_record = None, None
        if rented_count_for_calc > 0:
            max_rent_row = rented_rooms_df.loc[rented_rooms_df['full_rate_long'].idxmax()]
            min_rent_row = rented_rooms_df.loc[rented_rooms_df['full_rate_long'].idxmin()]
            max_rent_record = {'rent': max_rent_row['full_rate_long'], 'id': int(max_rent_row['id']),
                               'arr': max_rent_row['arr_date'], 'dep': max_rent_row['dep_date']}
            min_rent_record = {'rent': min_rent_row['full_rate_long'], 'id': int(min_rent_row['id']),
                               'arr': min_rent_row['arr_date'], 'dep': min_rent_row['dep_date']}

        analysis_results.append({
            '户型代码': rmtype, '总数': total_supply, '在租数': occupied_count, '付费在租数': rented_count_for_calc,
            '空置率(%)': vacancy_rate, '总月租金(元)': total_rent, '平均月租金(元)': avg_rent,
            '户型面积(m²)': area, '坪效(元/m²/月)': ping_xiao,
            'max_rent_info': max_rent_record, 'min_rent_info': min_rent_record
        })

    return analysis_results


# --- 4. 修改后的格式化函数 ---
def format_analysis_to_string(analysis_results: list, as_of_date_str: str, room_names: dict) -> str:
    """
    将分析结果列表格式化为一个易于阅读的多行字符串报告。
    """
    if isinstance(analysis_results, str):  # 如果传入的是错误信息
        return analysis_results

    if not analysis_results:
        return f"在日期 {as_of_date_str} 没有找到任何在租的房间记录。"

    report_lines = []
    report_lines.append(f"--- 各户型经营表现分析 (数据截止日期: {as_of_date_str}) ---")

    for result in analysis_results:
        room_type_name = room_names.get(result['户型代码'], result['户型代码'])
        report_lines.append(f"\n==================== 户型: {room_type_name} ====================")

        line1 = f"供应与占用: 总数 {result['总数']} 间, 在租 {result['在租数']} 间 (其中付费 {result['付费在租数']} 间)"
        line2 = f"空置率    : {result['空置率(%)']:.2f}%"
        report_lines.extend([line1, line2, "---"])

        line3 = f"租金表现  : 平均月租金 {result['平均月租金(元)']:,.2f} 元"
        line4 = f"坪效表现  : {result['坪效(元/m²/月)']:,.2f} 元/m²/月 (按面积 {result['户型面积(m²)']} m² 计算)"
        report_lines.extend([line3, line4, "---"])

        if result['max_rent_info']:
            max_info = result['max_rent_info']
            line5 = f"最高租金  : {max_info['rent']:,.2f} 元 (记录ID: {max_info['id']}, 入住: {max_info['arr']}, 离店: {max_info['dep']})"
        else:
            line5 = "最高租金  : N/A (无付费记录)"
        report_lines.append(line5)

        if result['min_rent_info']:
            min_info = result['min_rent_info']
            line6 = f"最低租金  : {min_info['rent']:,.2f} 元 (记录ID: {min_info['id']}, 入住: {min_info['arr']}, 离店: {min_info['dep']})"
        else:
            line6 = "最低租金  : N/A (无付费记录)"
        report_lines.append(line6)

    # --- 新增代码块：计算并添加总体概要 ---
    # 使用列表推导式和sum()函数，高效地从结果列表中提取并加总所有户型的总租金和付费房间数
    total_rent_all_types = sum(r['总月租金(元)'] for r in analysis_results)
    total_rented_count_all_types = sum(r['付费在租数'] for r in analysis_results)

    # 计算总体平均租金，并进行除零检查
    overall_avg_rent = (total_rent_all_types / total_rented_count_all_types
                        if total_rented_count_all_types > 0 else 0)

    # 将总体概要信息添加到报告的末尾
    report_lines.append("\n==================== 总体概要 ====================")
    summary_line = (f"所有户型总平均月租金: {overall_avg_rent:,.2f} 元 "
                    f"(基于 {total_rented_count_all_types} 间付费在租房间计算)")
    report_lines.append(summary_line)
    # --- 新增代码块结束 ---

    report_lines.append("\n========================================================")

    return "\n".join(report_lines)


# --- 主程序入口 ---
if __name__ == "__main__":
    print("--- 户型经营表现分析工具 ---")
    as_of_date_input = input("请输入要分析的截止日期 (YYYY-MM-DD): ")

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
    print(final_report_string)