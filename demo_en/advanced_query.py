import xml.etree.ElementTree as ET
import os
import datetime
import re
from collections import Counter  # 引入Counter，更方便地进行计数

# 配置与数据字典
XML_FILE_PATH = 'lease_service_order.xml'
SERVICE_CODE_MAP = {
    'A01': 'Linen Replacement', 'A02': 'Furniture Cleaning', 'A03': 'Floor Cleaning', 'A04': 'Appliance Cleaning',
    'A05': 'Sanitary Ware Cleaning', 'A06': 'Guest Supplies Replacement', 'A07': 'Pest Control', 'B1001': 'Elevator',
    'B101': 'Refrigerator', 'B102': 'Microwave Oven', 'B103': 'Dryer', 'B104': 'TV',
    'B105': 'Washing Machine', 'B106': 'Air Purifier', 'B107': 'Dehumidifier', 'B108': 'Range Hood',
    'B110': 'Electric Fan', 'B114': 'Heater', 'B117': 'Projector', 'B119': 'Screen',
    'B120': 'Water Heater', 'B121': 'Dishwasher', 'B122': 'Induction Cooker', 'B123': 'Oven',
    'B124': 'Exhaust Fan', 'B201': 'Smoke Detector', 'B202': 'Manual Alarm',
    'B203': 'Fire Sprinkler', 'B204': 'Emergency Light', 'B301': 'Radiator', 'B302': 'Ventilation Duct',
    'B303': 'Air Conditioner', 'B401': 'Towel Rack', 'B402': 'Faucet', 'B403': 'Indoor Door Handle/Lock',
    'B404': 'Window', 'B405': 'Hinge', 'B501': 'Power Socket', 'B502': 'Switch',
    'B503': 'Lighting Fixture', 'B504': 'Light Bulb', 'B505': 'Fly Killer Lamp', 'B506': 'Extension Cord',
    'B601': 'Furniture', 'B602': 'Cabinet', 'B603': 'Ceiling', 'B604': 'Floor',
    'B605': 'Wall', 'B606': 'Blinds', 'B607': 'Baseboard', 'B701': 'Drainage',
    'B702': 'Bathtub', 'B703': 'Mirror', 'B704': 'Tile', 'B705': 'Sink',
    'B706': 'Shower Head', 'B707': 'Toilet', 'B708': 'Basin', 'B801': 'Other',
    'B901': 'Network Equipment'
}
LOCATION_CODE_MAP = {
    '002': 'Bedroom', '004': 'Kitchen', '008': 'Bathroom', '009': 'Living Room',
    '001': 'Apartment Perimeter', '003': 'Work Area Corridor', '005': 'Back Area', '006': 'Front Area',
    '011': 'Elevator Lobby - Rear', '010': 'Elevator Lobby - Front', '007': 'Parking Lot', '012': 'Fire Staircase',
}


# --- 辅助、数据加载、高级筛选、结果格式化函数 (部分新增和修改) ---
def get_service_name(code):
    """根据服务代码获取对应的服务名称，如果未找到则返回未知代码提示。"""
    return SERVICE_CODE_MAP.get(code, f"Unknown Code ({code})")


def convert_excel_to_datetime_obj(excel_serial_date_str):
    """将Excel序列日期字符串（浮点数形式）转换为datetime对象。"""
    if not excel_serial_date_str: return None
    try:
        excel_serial_date = float(excel_serial_date_str)
        base_date = datetime.datetime(1899, 12, 30)  # Excel日期基准是1899年12月30日
        return base_date + datetime.timedelta(days=excel_serial_date)
    except (ValueError, TypeError):
        return None


def parse_room_info(rmno):
    """从房间号中解析出楼栋和楼层信息。"""
    if not rmno or not isinstance(rmno, str):
        return {'building': 'Unknown Building', 'floor': 'Unknown Floor'}
    match = re.match(r'^([A-Za-z])?(\d+)$', rmno.strip())
    if not match:
        return {'building': 'Unknown Building', 'floor': 'Unknown Floor (Format Error)'}
    prefix, number_part = match.groups()
    if prefix:
        building = f"{prefix.upper()} Block"
    else:
        building = "Main Building"
    if len(number_part) == 3:  # 例如 101 -> 1楼
        floor = f"{number_part[0]}F"
    elif len(number_part) == 4:  # 例如 1001 -> 10楼
        floor = f"{number_part[:2]}F"
    else:
        floor = "Unknown Floor (Numbering Error)"
    return {'building': building, 'floor': floor}


def parse_service_orders(xml_file):
    """从指定的XML文件中解析服务工单数据。"""
    print(f"Loading data from '{xml_file}'...")
    if not os.path.exists(xml_file):
        print(f"Error: File '{xml_file}' not found.")
        return None
    try:
        # 定义Excel XML的命名空间
        namespaces = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        tree = ET.parse(xml_file)
        root = tree.getroot()
        # 查找表格元素
        table = root.find('.//ss:Table', namespaces)
        if table is None: return []
        rows = table.findall('ss:Row', namespaces)
        # 获取表头
        header_row = rows[0]
        headers = [cell.find('ss:Data', namespaces).text for cell in header_row.findall('ss:Cell', namespaces)]
        orders = []
        # 遍历数据行
        for row in rows[1:]:
            order_data = {}
            cells = row.findall('ss:Cell', namespaces)
            for i, cell in enumerate(cells):
                if i < len(headers):
                    data_element = cell.find('ss:Data', namespaces)
                    value = data_element.text if data_element is not None and data_element.text is not None else ""
                    order_data[headers[i]] = value.strip()
            orders.append(order_data)
        print(f"Successfully loaded {len(orders)} service orders.\n")
        return orders
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file. Error message: {e}")
        return None


def search_orders_advanced(orders, start_date=None, end_date=None, service_code=None, location_code=None):
    """根据日期范围、服务代码和位置代码筛选工单。"""
    results = []
    for order in orders:
        order_date_obj = convert_excel_to_datetime_obj(order.get('create_datetime'))
        if order_date_obj:
            order_date = order_date_obj.date()  # 只比较日期部分
            if start_date and order_date < start_date: continue
            if end_date and order_date > end_date: continue
        elif start_date or end_date:  # 如果有日期筛选条件但工单日期无效，则跳过
            continue
        if service_code and order.get('product_code') != service_code: continue
        if location_code and order.get('location') != location_code: continue
        results.append(order)
    return results


def sanitize_for_display(text):
    """清理字符串中的控制字符，使其适合显示。"""
    if not isinstance(text, str): return text
    control_char_regex = re.compile(r'[\x00-\x1F\x7F-\x9F\u2028\u2029]')
    sanitized_text = control_char_regex.sub(' ', text)
    return sanitized_text


def format_to_string(results, criteria):
    """将筛选结果格式化为易读的字符串。"""
    if not results:
        return f"Query Criteria: {criteria}\n>> No service orders found matching the criteria."
    output_parts = []
    output_parts.append(f"Query Criteria: {criteria}")
    output_parts.append(f"--- Found {len(results)} relevant service orders ---\n\n")
    default_text = "N/A"
    for i, order in enumerate(results):
        product_code = order.get('product_code', '')
        service_name = get_service_name(product_code)
        location_code = order.get('location', '')
        location_name = LOCATION_CODE_MAP.get(location_code) if location_code else "N/A"
        create_dt_human = convert_excel_to_datetime_obj(order.get('create_datetime', ''))
        complete_dt_human = convert_excel_to_datetime_obj(order.get('complete_date', ''))
        sanitized_requirement = sanitize_for_display(order.get('requirement') or 'None')

        output_parts.append(f"【Record {i + 1}】\n")
        output_parts.append(f"  Room No.:     {order.get('rmno', default_text)}\n")
        output_parts.append(f"  Service Item: {service_name} ({product_code or 'No Code'})\n")
        output_parts.append(f"  Location:     {location_name} ({location_code or 'No Code'})\n")
        output_parts.append(f"  Description:  {sanitized_requirement}\n")
        output_parts.append(
            f"  Created Time: {create_dt_human.strftime('%Y-%m-%d %H:%M:%S') if create_dt_human else 'N/A'}\n")
        output_parts.append(
            f"  Completed Time: {complete_dt_human.strftime('%Y-%m-%d %H:%M:%S') if complete_dt_human else 'N/A'}\n")
        output_parts.append("-" * 25 + "\n\n")
    return "".join(output_parts)


def analyze_distribution(orders):
    """分析工单在不同楼栋、楼层和位置的服务项目分布。"""
    distribution = {}
    for order in orders:
        room_info = parse_room_info(order.get('rmno'))
        building, floor = room_info['building'], room_info['floor']
        location_name = LOCATION_CODE_MAP.get(order.get('location'), 'Unknown Location')
        service_name = get_service_name(order.get('product_code'))

        # 构建嵌套字典结构
        building_data = distribution.setdefault(building, {})
        floor_data = building_data.setdefault(floor, {})
        location_data = floor_data.setdefault(location_name, {})
        location_data[service_name] = location_data.get(service_name, 0) + 1
    return distribution


def format_distribution_report(distribution_data):
    """将工单分布数据格式化为详细报告。"""
    if not distribution_data: return ""  # 如果没有数据，返回空字符串
    report_parts = ["\n" + "=" * 50]
    report_parts.append("--- Detailed Service Order Distribution Report ---")
    for building in sorted(distribution_data.keys()):
        building_data = distribution_data[building]
        report_parts.append(f"\n[ Block: {building} ]")
        for floor in sorted(building_data.keys()):
            floor_data = building_data[floor]
            report_parts.append(f"  [ Floor: {floor} ]")
            for location, location_data in floor_data.items():
                report_parts.append(f"    ● Location: {location}")
                for service, count in location_data.items():
                    report_parts.append(f"      - {service}: {count} times")
    report_parts.append("=" * 50 + "\n")
    return "\n".join(report_parts)


# --- 新增: 总体数据总结分析函数 ---
def calculate_summaries(orders):
    """遍历工单，计算各个维度的总体数量。"""
    if not orders:
        return {}, {}, {}, {}

    service_counts = Counter()
    location_counts = Counter()
    floor_counts = Counter()
    building_counts = Counter()

    for order in orders:
        service_counts[get_service_name(order.get('product_code'))] += 1
        location_counts[LOCATION_CODE_MAP.get(order.get('location'), 'Unknown Location')] += 1

        room_info = parse_room_info(order.get('rmno'))
        floor_counts[room_info['floor']] += 1
        building_counts[room_info['building']] += 1

    return service_counts, location_counts, floor_counts, building_counts


# --- 新增: 格式化总结报告的函数 ---
def format_summary_report(total_orders, service_counts, location_counts, floor_counts, building_counts):
    """将统计数据格式化为Top 3的总结报告。"""
    if not total_orders:
        return "No data available to generate a summary report."

    report_parts = ["\n" + "=" * 50]
    report_parts.append("--- Overall Data Summary ---")
    report_parts.append(f"Total Service Orders in Query Range: {total_orders} orders\n")

    # 一个辅助函数，用于生成Top 3列表
    def get_top_three_string(title, counter):
        lines = [f"--- Top 3 {title} ---"]
        if not counter:
            lines.append("  No Data")
            return "\n".join(lines)

        # counter.most_common(3) 直接返回前三的 (项目, 次数) 列表
        for i, (item, count) in enumerate(counter.most_common(3)):
            percentage = (count / total_orders) * 100
            lines.append(f"  {i + 1}. {item}: {count} times ({percentage:.1f}%)")
        return "\n".join(lines)

    report_parts.append(get_top_three_string("Service Items", service_counts))
    report_parts.append(get_top_three_string("Locations", location_counts))
    report_parts.append(get_top_three_string("Floor Distribution", floor_counts))
    report_parts.append(get_top_three_string("Building Distribution", building_counts))

    report_parts.append("=" * 50 + "\n")
    return "\n\n".join(report_parts)


# --- 主程序 ---
def main():
    # 解析XML文件加载所有工单数据
    all_orders = parse_service_orders(XML_FILE_PATH)
    if not all_orders:
        return

    # 定义查询筛选条件
    start_date_str = '2025-07-01'
    end_date_str = None  # 不限制结束日期
    target_service_code = None  # 不限制服务项目
    target_location_code = None  # 不限制具体位置

    # 将日期字符串转换为datetime.date对象
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

    # 1. 筛选出符合条件的工单
    found_orders = search_orders_advanced(all_orders, start_date, end_date, target_service_code, target_location_code)

    # (可选) 打印详细的工单列表，目前已注释
    criteria_desc = (
        f"Time Range: [{start_date or 'Unlimited'} to {end_date or 'Unlimited'}], "
        f"Service Item: [{SERVICE_CODE_MAP.get(target_service_code, 'Unlimited')}], "
        f"Specific Location: [{LOCATION_CODE_MAP.get(target_location_code, 'Unlimited')}]"
    )
    # result_string = format_to_string(found_orders, criteria_desc)
    # print("\n" + "=" * 50)
    # print("--- Detailed Service Order List ---")
    # print(result_string)
    # print("=" * 50 + "\n")

    # 2. 生成并打印总体数据总结报告
    service_counts, location_counts, floor_counts, building_counts = calculate_summaries(found_orders)
    summary_report = format_summary_report(len(found_orders), service_counts, location_counts, floor_counts,
                                           building_counts)
    print(summary_report)

    # 3. 生成并打印详细分布报告
    distribution_data = analyze_distribution(found_orders)
    distribution_report = format_distribution_report(distribution_data)
    print(distribution_report)


# 当脚本作为主程序运行时执行main函数
if __name__ == "__main__":
    main()