import xml.etree.ElementTree as ET
import os
import datetime
import re
from collections import Counter

# --- 配置与数据字典 (无变化) ---
XML_FILE_PATH = 'lease_service_order.xml'
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


# --- 辅助函数 (部分新增) ---
def get_service_name(code):
    return SERVICE_CODE_MAP.get(code, f"未知代码 ({code})")


def convert_excel_to_datetime_obj(excel_serial_date_str):
    if not excel_serial_date_str: return None
    try:
        excel_serial_date = float(excel_serial_date_str)
        base_date = datetime.datetime(1899, 12, 30)
        return base_date + datetime.timedelta(days=excel_serial_date)
    except (ValueError, TypeError):
        return None


def parse_room_info(rmno):
    if not rmno or not isinstance(rmno, str):
        return {'building': '未知栋', 'floor': '未知楼层'}
    match = re.match(r'^([A-Za-z])?(\d+)$', rmno.strip())
    if not match:
        return {'building': '未知栋', 'floor': '未知楼层 (格式错误)'}
    prefix, number_part = match.groups()
    if prefix:
        building = f"{prefix.upper()}栋"
    else:
        building = "主楼"
    if len(number_part) == 3:
        floor = f"{number_part[0]}楼"
    elif len(number_part) == 4:
        floor = f"{number_part[:2]}楼"
    else:
        floor = "未知楼层 (编号异常)"
    return {'building': building, 'floor': floor}


# --- 新增: 定义时间分段的辅助函数 ---
def get_time_segment(hour):
    """根据小时返回对应的时间段描述。"""
    if 0 <= hour < 7:
        return "深夜 (00:00-06:59)"
    elif 7 <= hour < 12:
        return "上午 (07:00-11:59)"
    elif 12 <= hour < 14:
        return "午间 (12:00-13:59)"
    elif 14 <= hour < 18:
        return "下午 (14:00-17:59)"
    else:  # 18 到 23
        return "夜间 (18:00-23:59)"


# --- 数据加载与筛选 (无变化) ---
def parse_service_orders(xml_file):
    print(f"正在从 '{xml_file}' 加载数据...")
    if not os.path.exists(xml_file):
        print(f"错误: 文件 '{xml_file}' 未找到。")
        return None
    try:
        namespaces = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        tree = ET.parse(xml_file)
        root = tree.getroot()
        table = root.find('.//ss:Table', namespaces)
        if table is None: return []
        rows = table.findall('ss:Row', namespaces)
        header_row = rows[0]
        headers = [cell.find('ss:Data', namespaces).text for cell in header_row.findall('ss:Cell', namespaces)]
        orders = []
        for row in rows[1:]:
            order_data = {}
            cells = row.findall('ss:Cell', namespaces)
            for i, cell in enumerate(cells):
                if i < len(headers):
                    data_element = cell.find('ss:Data', namespaces)
                    value = data_element.text if data_element is not None and data_element.text is not None else ""
                    order_data[headers[i]] = value.strip()
            orders.append(order_data)
        print(f"成功加载 {len(orders)} 条工单数据。\n")
        return orders
    except ET.ParseError as e:
        print(f"错误: 解析XML文件失败。错误信息: {e}")
        return None


def search_orders_advanced(orders, start_date=None, end_date=None, service_code=None, location_code=None):
    results = []
    for order in orders:
        order_date_obj = convert_excel_to_datetime_obj(order.get('create_datetime'))
        if order_date_obj:
            order_date = order_date_obj.date()
            if start_date and order_date < start_date: continue
            if end_date and order_date > end_date: continue
        elif start_date or end_date:
            continue
        if service_code and order.get('product_code') != service_code: continue
        if location_code and order.get('location') != location_code: continue
        results.append(order)
    return results


def sanitize_for_display(text):
    if not isinstance(text, str): return text
    control_char_regex = re.compile(r'[\x00-\x1F\x7F-\x9F\u2028\u2029]')
    sanitized_text = control_char_regex.sub(' ', text)
    return sanitized_text


def format_to_string(results, criteria):
    if not results:
        return f"查询条件: {criteria}\n>> 未找到符合条件的工单信息。"
    # ... 此函数无变化，保持原样 ...
    output_parts = []
    output_parts.append(f"查询条件: {criteria}")
    output_parts.append(f"--- 共找到 {len(results)} 条相关工单 ---\n\n")
    for i, order in enumerate(results):
        product_code = order.get('product_code', '')
        service_name = get_service_name(product_code)
        location_code = order.get('location', '')
        location_name = LOCATION_CODE_MAP.get(location_code) if location_code else "未提供"
        create_dt_human = convert_excel_to_datetime_obj(order.get('create_datetime', ''))
        complete_dt_human = convert_excel_to_datetime_obj(order.get('complete_date', ''))
        sanitized_requirement = sanitize_for_display(order.get('requirement') or '无')
        default_text = "未提供"
        output_parts.append(f"【记录 {i + 1}】\n")
        output_parts.append(f"  房号:       {order.get('rmno', default_text)}\n")
        output_parts.append(f"  服务项目:   {service_name} ({product_code or '无代码'})\n")
        output_parts.append(f"  具体位置:   {location_name} ({location_code or '无代码'})\n")
        output_parts.append(f"  需求描述:   {sanitized_requirement}\n")
        output_parts.append(
            f"  创建时间:   {create_dt_human.strftime('%Y-%m-%d %H:%M:%S') if create_dt_human else 'N/A'}\n")
        output_parts.append(
            f"  完成时间:   {complete_dt_human.strftime('%Y-%m-%d %H:%M:%S') if complete_dt_human else 'N/A'}\n")
        output_parts.append("-" * 25 + "\n\n")
    return "".join(output_parts)


def analyze_distribution(orders):
    distribution = {}
    for order in orders:
        room_info = parse_room_info(order.get('rmno'))
        building, floor = room_info['building'], room_info['floor']
        location_name = LOCATION_CODE_MAP.get(order.get('location'), '未知位置')
        service_name = get_service_name(order.get('product_code'))

        building_data = distribution.setdefault(building, {})
        floor_data = building_data.setdefault(floor, {})
        location_data = floor_data.setdefault(location_name, {})
        location_data[service_name] = location_data.get(service_name, 0) + 1
    return distribution


def format_distribution_report(distribution_data):
    if not distribution_data: return ""
    report_parts = ["\n" + "=" * 50]
    report_parts.append("--- 服务工单分布情况详细报告 ---")
    for building in sorted(distribution_data.keys()):
        building_data = distribution_data[building]
        report_parts.append(f"\n[ 栋座: {building} ]")
        for floor in sorted(building_data.keys()):
            floor_data = building_data[floor]
            report_parts.append(f"  [ 楼层: {floor} ]")
            for location, location_data in floor_data.items():
                report_parts.append(f"    ● 位置: {location}")
                for service, count in location_data.items():
                    report_parts.append(f"      - {service}: {count} 次")
    report_parts.append("=" * 50 + "\n")
    return "\n".join(report_parts)


def calculate_summaries(orders):
    if not orders:
        return {}, {}, {}, {}

    service_counts = Counter()
    location_counts = Counter()
    floor_counts = Counter()
    building_counts = Counter()

    for order in orders:
        service_counts[get_service_name(order.get('product_code'))] += 1
        location_counts[LOCATION_CODE_MAP.get(order.get('location'), '未知位置')] += 1

        room_info = parse_room_info(order.get('rmno'))
        floor_counts[room_info['floor']] += 1
        building_counts[room_info['building']] += 1

    return service_counts, location_counts, floor_counts, building_counts


def format_summary_report(total_orders, service_counts, location_counts, floor_counts, building_counts):
    if not total_orders:
        return "没有可用于生成总结报告的数据。"

    report_parts = ["\n" + "=" * 50]
    report_parts.append("--- 总体数据总结 ---")
    report_parts.append(f"查询范围内总工单数: {total_orders} 条\n")

    def get_top_three_string(title, counter):
        lines = [f"--- Top 3 {title} ---"]
        if not counter:
            lines.append("  无数据")
            return "\n".join(lines)
        for i, (item, count) in enumerate(counter.most_common(3)):
            percentage = (count / total_orders) * 100
            lines.append(f"  {i + 1}. {item}: {count} 次 ({percentage:.1f}%)")
        return "\n".join(lines)

    report_parts.append(get_top_three_string("工单项目", service_counts))
    report_parts.append(get_top_three_string("工单位置", location_counts))
    report_parts.append(get_top_three_string("楼层分布", floor_counts))
    report_parts.append(get_top_three_string("楼栋分布", building_counts))

    report_parts.append("=" * 50 + "\n")
    return "\n\n".join(report_parts)


# --- 时间维度分析函数 (已修改) ---
def analyze_temporal_distribution(orders):
    """分析工单的时间分布情况，按分段统计小时。"""
    if not orders:
        return {}, {}, {}, {}, {}

    yearly_counts = Counter()
    monthly_counts = Counter()
    weekly_counts = Counter()
    day_of_week_counts = Counter()
    segment_counts = Counter()  # 修改：不再使用hourly_counts

    for order in orders:
        dt_obj = convert_excel_to_datetime_obj(order.get('create_datetime'))
        if dt_obj:
            yearly_counts[dt_obj.year] += 1
            monthly_counts[dt_obj.strftime('%Y-%m')] += 1
            weekly_counts[dt_obj.strftime('%Y-W%W')] += 1
            day_of_week_counts[dt_obj.strftime('%A')] += 1
            # 修改：调用新函数，按时间段计数
            segment = get_time_segment(dt_obj.hour)
            segment_counts[segment] += 1

    return yearly_counts, monthly_counts, weekly_counts, day_of_week_counts, segment_counts


# --- 时间分布报告函数 (已修改) ---
def format_temporal_report(total_orders, yearly_counts, monthly_counts, weekly_counts, day_of_week_counts,
                           segment_counts):
    """将时间分布统计数据格式化为带百分比的可读报告。"""
    if not total_orders:
        return "没有可用于生成时间分布报告的数据。"

    report_parts = ["\n" + "=" * 50]
    report_parts.append("--- 工单创建时间分布报告 ---")
    report_parts.append("=" * 50)

    # 年、月、周、日的分布报告 (无变化)
    report_parts.append("\n[ 按年份分布 ]")
    for year, count in sorted(yearly_counts.items()):
        percentage = (count / total_orders) * 100
        report_parts.append(f"  - {year} 年: {count} 次 ({percentage:.1f}%)")

    report_parts.append("\n[ 按月份分布 ]")
    for month, count in sorted(monthly_counts.items()):
        percentage = (count / total_orders) * 100
        report_parts.append(f"  - {month} 月: {count} 次 ({percentage:.1f}%)")

    report_parts.append("\n[ 按周数分布 ]")
    for week, count in sorted(weekly_counts.items()):
        percentage = (count / total_orders) * 100
        report_parts.append(f"  - {week}: {count} 次 ({percentage:.1f}%)")

    report_parts.append("\n[ 按星期内的日分布 (周一至周日) ]")
    day_map = {
        "Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
        "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日"
    }
    for day_en, day_cn in day_map.items():
        count = day_of_week_counts.get(day_en, 0)
        percentage = (count / total_orders) * 100
        report_parts.append(f"  - {day_cn}: {count} 次 ({percentage:.1f}%)")

    # 修改：按天内时段分布
    report_parts.append("\n[ 按天内时段分布 ]")
    # 定义一个列表以保证输出的顺序是按时间先后的
    time_segments_order = [
        "深夜 (00:00-06:59)",
        "上午 (07:00-11:59)",
        "午间 (12:00-13:59)",
        "下午 (14:00-17:59)",
        "夜间 (18:00-23:59)"
    ]
    for segment in time_segments_order:
        count = segment_counts.get(segment, 0)
        percentage = (count / total_orders) * 100
        report_parts.append(f"  - {segment}: {count} 次 ({percentage:.1f}%)")

    report_parts.append("\n" + "=" * 50 + "\n")
    return "\n".join(report_parts)


# --- 主程序 (已修改) ---
def main():
    all_orders = parse_service_orders(XML_FILE_PATH)
    if not all_orders:
        return

    start_date_str = '2025-09-01'
    end_date_str = '2025-09-30'
    target_service_code = None
    target_location_code = None

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

    # 1. 筛选出符合条件的工单
    found_orders = search_orders_advanced(all_orders, start_date, end_date, target_service_code, target_location_code)

    service_counts, location_counts, floor_counts, building_counts = calculate_summaries(found_orders)
    summary_report = format_summary_report(len(found_orders), service_counts, location_counts, floor_counts,
                                           building_counts)
    print(summary_report)

    distribution_data = analyze_distribution(found_orders)
    distribution_report = format_distribution_report(distribution_data)
    print(distribution_report)

    # 修改：更新变量名以匹配新的返回值
    yearly, monthly, weekly, daily, segments = analyze_temporal_distribution(found_orders)
    # 修改：传入新的分段数据
    temporal_report = format_temporal_report(len(found_orders), yearly, monthly, weekly, daily, segments)
    print(temporal_report)


if __name__ == "__main__":
    main()