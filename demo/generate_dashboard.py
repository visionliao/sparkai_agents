import webbrowser
import os
import pandas as pd
from lxml import etree
from datetime import datetime, timedelta, date
import warnings
import http.server
import socketserver
import threading
import time

# --- 1. 配置区域 (根据需要修改) ---

# 数据源和模板文件路径
MASTER_BASE_XML_PATH = 'demo/master_base.xml'
TEMPLATE_PATH = "demo/template.html"
OUTPUT_PATH = "demo/dashboard.html"

# 公寓基本信息
TOTAL_ROOMS = 579

# 楼栋配置 (总数需要手动维护)
BUILDING_CONFIG = {
    'A': {'total': 418, 'key': 'building_a'},
    'B': {'total': 161, 'key': 'building_b'}
}

# 户型配置
ROOM_TYPE_COUNTS = {'STE': 360, '1BD': 150, 'STD': 22, '1BP': 19, '2BD': 15, 'STP': 12, '3BR': 1}
ROOM_TYPE_AREAS = {'STE': 60, '1BD': 73, 'STD': 45, '1BP': 88, '2BD': 108, 'STP': 67, '3BR': 134}
DASHBOARD_KEY_MAP = {'sd': 'STD', 'obd': '1BD', 'seb': 'STE', 'obp': '1BP', 'sea': '2BD', 'tbd': '3BR'}

# 渠道与市场映射
CHANNEL_MAP = {
    'AGT': 'channel_AGT',
    'MKC': 'channel_MKC',
    'MPM': 'channel_MPM',
    'WI': 'channel_WI',
    'LAT': 'channel_LAT',
    'CRS': 'channel_CRS',
    'REF': 'channel_REF',
    'OTA': 'channel_OTA',
    'ORC': 'channel_ORC',
    'WEB': 'channel_WEB',
    'LES': 'channel_LES',
    'STF': 'channel_STF',
}
MARKET_MAP = {
    'IND': 'market_IND',
    'LOC': 'market_LOC',
    'DOC': 'market_DOC',
    'ITC': 'market_ITC',
    'GDS': 'market_GDS',
    'OTA': 'market_OTA',
    'WEB': 'market_WEB',
    'WX': 'market_WX',
    'LES': 'market_LES',
}


# --- 2. 数据解析与分析函数 ---

def parse_spreadsheetml(file_path: str) -> pd.DataFrame:
    """使用 lxml 解析 XML 并返回一个包含所需字段的 DataFrame。"""
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = root.findall('.//ss:Worksheet/ss:Table/ss:Row', namespaces=ns)
        if not rows: return pd.DataFrame()

        header_row = rows[0]
        header = [cell.find('ss:Data', ns).text.strip() if cell.find('ss:Data', ns) is not None and cell.find('ss:Data',
                                                                                                              ns).text is not None else f"column_{i}"
                  for i, cell in enumerate(header_row.findall('ss:Cell', ns))]

        data = []
        for row in rows[1:]:
            row_data = [(cell.find('ss:Data', ns).text or '') for cell in row.findall('ss:Cell', ns)]
            if len(row_data) < len(header):
                row_data.extend([''] * (len(header) - len(row_data)))
            data.append(row_data)

        df = pd.DataFrame(data, columns=header)

        required_cols = ['id', 'arr', 'dep', 'full_rate_long', 'create_datetime', 'rmno', 'sta', 'building', 'channel',
                         'ratecode']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"错误: 数据源XML中缺少关键列 '{col}'")

        for col in ['id', 'arr', 'dep', 'full_rate_long', 'create_datetime']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(subset=['arr', 'rmno', 'create_datetime'], inplace=True)
        df['arr_date'] = pd.to_datetime(df['arr'], unit='D', origin='1899-12-30').dt.date
        df['dep_date'] = pd.to_datetime(df['dep'], unit='D', origin='1899-12-30').dt.date
        df['create_dt'] = pd.to_datetime(df['create_datetime'], unit='D', origin='1899-12-30')
        return df
    except FileNotFoundError:
        print(f"错误: 数据文件 '{file_path}' 未找到。")
        return None
    except Exception as e:
        print(f"解析XML文件时发生严重错误: {e}")
        return None


def get_current_records(df: pd.DataFrame, target_date: date, status_filter: list):
    if df is None: return pd.DataFrame()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        daily_records = df[
            (df['arr_date'] <= target_date) & (df['dep_date'] > target_date) & (df['sta'].isin(status_filter))].copy()
    if daily_records.empty: return pd.DataFrame()
    daily_records['rent_priority'] = (daily_records['full_rate_long'] > 0).astype(int)
    sorted_records = daily_records.sort_values(by=['rmno', 'rent_priority', 'create_dt'],
                                               ascending=[True, False, False])
    return sorted_records.drop_duplicates(subset='rmno', keep='first')


def analyze_room_type_performance(df: pd.DataFrame, start_date: date, end_date: date, room_counts: dict,
                                  room_areas: dict):
    if df is None: return {}
    num_days = (end_date - start_date).days + 1
    df_filtered = df[df['sta'].isin(['I', 'R'])].copy()
    results = {}
    for rmtype in sorted(list(room_counts.keys())):
        total_supply, area = room_counts.get(rmtype, 0), room_areas.get(rmtype, 0)
        if total_supply == 0: continue
        total_occupied_room_nights, total_rent_for_period = 0, 0
        relevant_bookings = df_filtered[(df_filtered['rmtype'] == rmtype) & (df_filtered['arr_date'] <= end_date) & (
                    df_filtered['dep_date'] > start_date)].copy()
        if not relevant_bookings.empty: relevant_bookings['rent_priority'] = (
                    relevant_bookings['full_rate_long'] > 0).astype(int)
        for day in pd.date_range(start=start_date, end=end_date).date:
            daily_occupied_df = relevant_bookings[
                (relevant_bookings['arr_date'] <= day) & (relevant_bookings['dep_date'] > day)]
            if not daily_occupied_df.empty:
                daily_unique = daily_occupied_df.sort_values(by=['rmno', 'rent_priority', 'create_dt'],
                                                             ascending=[True, False, False]).drop_duplicates(
                    subset='rmno', keep='first')
                total_occupied_room_nights += len(daily_unique)
                total_rent_for_period += (
                            daily_unique[daily_unique['full_rate_long'] > 0]['full_rate_long'] / 30.0).sum()
        total_available_nights = total_supply * num_days
        results[rmtype] = {
            'occupancy': (
                                     total_occupied_room_nights / total_available_nights) * 100 if total_available_nights > 0 else 0,
            'avg_rent': (
                        total_rent_for_period / total_occupied_room_nights * 30) if total_occupied_room_nights > 0 else 0,
            'efficiency': ((
                                       total_rent_for_period / total_occupied_room_nights) / area) if total_occupied_room_nights > 0 and area > 0 else 0,
            'total_income': total_rent_for_period
        }
    return results


# --- 3. 主执行逻辑 ---

def gather_automated_data(df: pd.DataFrame):
    """执行所有自动化计算并返回一个纯数字的数据字典。"""
    print("开始执行自动化数据计算...")
    today, thirty_days_ago = date.today(), date.today() - timedelta(days=30)
    auto_data = {}

    auto_data['report_date'] = today.strftime('%Y年%m月%d日')
    auto_data['data_period'] = f"{thirty_days_ago.strftime('%Y.%m.%d')} - {today.strftime('%Y.%m.%d')}"

    inhouse_records = get_current_records(df, today, ['I'])
    paid_records = inhouse_records[
        inhouse_records['full_rate_long'] > 0] if not inhouse_records.empty else pd.DataFrame()

    auto_data["rented_rooms"] = len(inhouse_records)
    auto_data["occupancy_rate"] = (len(inhouse_records) / TOTAL_ROOMS) * 100 if TOTAL_ROOMS > 0 else 0
    auto_data["chart_status_i"], auto_data["chart_status_r"] = len(inhouse_records), len(
        get_current_records(df, today, ['R']))
    auto_data["chart_status_o"] = len(
        df[(df['sta'] == 'O') & (df['dep_date'] >= thirty_days_ago) & (df['dep_date'] <= today)].drop_duplicates(
            subset='id'))
    auto_data["chart_status_x"] = len(df[(df['sta'] == 'X') & (df['create_dt'].dt.date >= thirty_days_ago) & (
                df['create_dt'].dt.date <= today)].drop_duplicates(subset='id'))
    auto_data["room_status_total"] = sum(
        auto_data[k] for k in ["chart_status_i", "chart_status_r", "chart_status_o", "chart_status_x"])
    auto_data["chart_status_remainder"] = TOTAL_ROOMS - auto_data["room_status_total"]
    auto_data["data_coverage_rate"] = (auto_data["room_status_total"] / TOTAL_ROOMS) * 100 if TOTAL_ROOMS > 0 else 0
    print("运营总览和房间状态计算完成。")

    auto_data["rented_with_rent_record"], auto_data["rented_without_rent_record"] = len(paid_records), len(
        inhouse_records) - len(paid_records)
    auto_data["estimated_monthly_income"] = paid_records['full_rate_long'].sum() if not paid_records.empty else 0
    auto_data["rooms_with_rent_record"] = df[df['full_rate_long'] > 0]['rmno'].nunique()
    print("租金与收入计算完成。")

    room_perf_data = analyze_room_type_performance(df, thirty_days_ago, today, ROOM_TYPE_COUNTS, ROOM_TYPE_AREAS)
    total_income_all = sum(v.get('total_income', 0) for v in room_perf_data.values())
    for key, rmtype in DASHBOARD_KEY_MAP.items():
        perf = room_perf_data.get(rmtype, {})
        auto_data[f"{key}_occupancy"], auto_data[f"{key}_avg_rent"], auto_data[f"{key}_efficiency"] = perf.get(
            'occupancy', 0), perf.get('avg_rent', 0), perf.get('efficiency', 0) * 30
        auto_data[f"{key}_income_contribution"] = (
                    perf.get('total_income', 0) / total_income_all * 100) if total_income_all > 0 else 0
    all_efficiencies = {k: v.get('efficiency', 0) for k, v in room_perf_data.items()}
    auto_data["highlight_max_efficiency"] = max(all_efficiencies.values()) * 30 if all_efficiencies else 0
    print("房型分析计算完成。")

    for b_code, b_config in BUILDING_CONFIG.items():
        key, total = b_config['key'], b_config['total']
        building_records = inhouse_records[inhouse_records['building'] == b_code]
        building_paid_records = building_records[building_records['full_rate_long'] > 0]
        auto_data[f"{key}_total"], auto_data[f"{key}_rented"] = total, len(building_records)
        auto_data[f"{key}_occupancy"] = (len(building_records) / total) * 100 if total > 0 else 0
        auto_data[f"{key}_avg_rent"] = building_paid_records[
            'full_rate_long'].mean() if not building_paid_records.empty else 0
        auto_data[f"{key}_median_rent"] = building_paid_records[
            'full_rate_long'].median() if not building_paid_records.empty else 0
    print("楼栋分析计算完成。")

    rents = paid_records['full_rate_long'] if not paid_records.empty else pd.Series(dtype='float64')
    auto_data["rent_avg"], auto_data["rent_median"], auto_data["rent_min"], auto_data[
        "rent_max"] = rents.mean(), rents.median(), rents.min(), rents.max()
    # 【新增】计算总坪效
    if not paid_records.empty:
        total_area_of_paid_rooms = paid_records['rmtype'].map(ROOM_TYPE_AREAS).sum()
        auto_data["rent_sqm_avg"] = (auto_data[
                                         "estimated_monthly_income"] / total_area_of_paid_rooms) if total_area_of_paid_rooms > 0 else 0
    else:
        auto_data["rent_sqm_avg"] = 0
    auto_data["chart_rent_dist_1"], auto_data["chart_rent_dist_2"] = int(
        rents[(rents >= 5000) & (rents < 10000)].count()), int(rents[(rents >= 10000) & (rents < 15000)].count())
    auto_data["chart_rent_dist_3"], auto_data["chart_rent_dist_4"] = int(
        rents[(rents >= 15000) & (rents < 20000)].count()), int(rents[(rents >= 20000) & (rents < 30000)].count())
    print("租金分析计算完成。")

    for ch_code, ch_key in CHANNEL_MAP.items():
        channel_records = paid_records[paid_records['channel'] == ch_code]
        auto_data[f"{ch_key}_count"], auto_data[f"{ch_key}_income"] = len(channel_records), channel_records[
            'full_rate_long'].sum()
    for mkt_code, mkt_key in MARKET_MAP.items():
        market_records = paid_records[paid_records['ratecode'] == mkt_code]
        auto_data[f"{mkt_key}_count"], auto_data[f"{mkt_key}_income"] = len(market_records), market_records[
            'full_rate_long'].sum()
    total_channel_income, total_market_income = sum(auto_data.get(f"{v}_income", 0) for v in CHANNEL_MAP.values()), sum(
        auto_data.get(f"{v}_income", 0) for v in MARKET_MAP.values())
    for ch_key in CHANNEL_MAP.values(): auto_data[f"{ch_key}_ratio"] = (
                auto_data.get(f"{ch_key}_income", 0) / total_channel_income * 100) if total_channel_income > 0 else 0
    for mkt_key in MARKET_MAP.values(): auto_data[f"{mkt_key}_ratio"] = (
                auto_data.get(f"{mkt_key}_income", 0) / total_market_income * 100) if total_market_income > 0 else 0
    print("渠道与市场分析计算完成。")

    auto_data["highlight_income"], auto_data["highlight_avg_rent"] = auto_data["estimated_monthly_income"] / 10000, \
    auto_data["rent_avg"]
    print("自动化数据获取完毕！")
    return auto_data


def main():
    """主函数，组织整个流程。"""
    manual_data = {
        "total_rooms": TOTAL_ROOMS
    }

    master_df = parse_spreadsheetml(MASTER_BASE_XML_PATH)
    if master_df is None: return

    automated_data = gather_automated_data(master_df)
    final_data = {**manual_data, **automated_data}

    try:
        final_data["occupancy_rate"] = f"{final_data.get('occupancy_rate', 0):.2f}"
        final_data["data_coverage_rate"] = f"{final_data.get('data_coverage_rate', 0):.2f}"
        final_data["estimated_monthly_income"] = f"{final_data.get('estimated_monthly_income', 0):,.2f}"
        final_data["highlight_income"] = f"{final_data.get('highlight_income', 0):.1f}"
        final_data["highlight_max_efficiency"] = f"{final_data.get('highlight_max_efficiency', 0):.2f}"
        final_data["rent_sqm_avg"] = f"{final_data.get('rent_sqm_avg', 0):.2f}"
        for key in ['rent_avg', 'rent_median', 'rent_min', 'rent_max', 'highlight_avg_rent']:
            final_data[key] = f"{final_data.get(key, 0):,.2f}"
        for key_prefix in DASHBOARD_KEY_MAP.keys():
            final_data[f"{key_prefix}_occupancy"] = f"{final_data.get(f'{key_prefix}_occupancy', 0):.2f}"
            final_data[f"{key_prefix}_avg_rent"] = f"{final_data.get(f'{key_prefix}_avg_rent', 0):,.2f}"
            final_data[f"{key_prefix}_efficiency"] = f"{final_data.get(f'{key_prefix}_efficiency', 0):.2f}"
            if f"{key_prefix}_income_contribution" in final_data:
                final_data[
                    f"{key_prefix}_income_contribution"] = f"{final_data.get(f'{key_prefix}_income_contribution', 0):.1f}"
        for b_config in BUILDING_CONFIG.values():
            key = b_config['key']
            final_data[f"{key}_occupancy"] = f"{final_data.get(f'{key}_occupancy', 0):.2f}"
            final_data[f"{key}_avg_rent"] = f"{final_data.get(f'{key}_avg_rent', 0):,.2f}"
            final_data[f"{key}_median_rent"] = f"{final_data.get(f'{key}_median_rent', 0):,.2f}"
        for key in list(CHANNEL_MAP.values()) + list(MARKET_MAP.values()):
            final_data[f"{key}_income"] = f"{final_data.get(f'{key}_income', 0):,.0f}"
            final_data[f"{key}_ratio"] = f"{final_data.get(f'{key}_ratio', 0):.1f}"

    except (KeyError, ValueError) as e:
        print(f"格式化数据时出错：{e}。请检查模板占位符和数据类型。")
        return

    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        print(f"错误：模板文件 '{TEMPLATE_PATH}' 未找到。")
        return

    output_content = template_content.format(**final_data)
    # 确保输出目录存在
    output_dir = os.path.dirname(OUTPUT_PATH)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(output_content)
    print(f"\n成功生成报表: {OUTPUT_PATH}")

    # --- 从这里开始是修改的核心 ---

    PORT = 3000
    # 我们需要在HTML文件所在的目录启动服务器
    # 例如，如果OUTPUT_PATH是 'demo/dashboard.html'，我们就在 'demo' 目录下启动服务
    server_dir = os.path.dirname(os.path.abspath(OUTPUT_PATH))

    # 定义一个处理HTTP请求的Handler，它会在指定的目录下提供文件服务
    Handler = http.server.SimpleHTTPRequestHandler

    # 切换到目标目录来启动服务器
    os.chdir(server_dir)

    httpd = socketserver.TCPServer(("", PORT), Handler)

    print(f"正在启动本地服务器，端口为: {PORT}")
    print(f"你可以在浏览器中访问: http://localhost:{PORT}/{os.path.basename(OUTPUT_PATH)}")

    # 在一个新线程中运行服务器，这样就不会阻塞主程序
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True  # 设置为守护线程，主程序退出时线程也退出
    server_thread.start()

    # 稍等片刻以确保服务器已启动
    time.sleep(1)

    # 在浏览器中打开URL
    url = f"http://localhost:{PORT}/{os.path.basename(OUTPUT_PATH)}"
    webbrowser.open(url)
    print("正在默认浏览器中打开报表...")

    # 让主程序保持运行，直到用户手动停止（例如按 Ctrl+C）
    try:
        # 你可以让脚本在这里结束后立即退出，服务器线程也会随之关闭
        print("\n报表已在浏览器中打开。服务器正在后台运行。")
        print("关闭此终端窗口或按 Ctrl+C 即可停止服务器。")
        while True:
            time.sleep(3600)  # 保持主线程存活
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        httpd.shutdown()
        print("服务器已关闭。")


if __name__ == '__main__':
    main()