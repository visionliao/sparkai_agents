import xml.etree.ElementTree as ET
import os
import datetime
import re

# --- 配置 ---
XML_FILE_PATH = 'lease_service_order.xml'

SERVICE_CODE_MAP = {
    'A01': 'Linen Change', 'A02': 'Furniture Cleaning', 'A03': 'Floor Cleaning', 'A04': 'Appliance Cleaning',
    'A05': 'Sanitary Ware Cleaning', 'A06': 'Guest Supplies Replacement', 'A07': 'Pest Control', 'B1001': 'Elevator',
    'B101': 'Refrigerator', 'B102': 'Microwave', 'B103': 'Dryer', 'B104': 'Television',
    'B105': 'Washing Machine', 'B106': 'Air Purifier', 'B107': 'Dehumidifier', 'B108': 'Range Hood',
    'B110': 'Electric Fan', 'B114': 'Heater', 'B117': 'Projector', 'B119': 'Screen',
    'B120': 'Water Heater', 'B121': 'Dishwasher', 'B122': 'Induction Cooker', 'B123': 'Oven',
    'B124': 'Exhaust Fan', 'B201': 'Smoke Detector', 'B202': 'Manual Alarm',
    'B203': 'Fire Sprinkler', 'B204': 'Emergency Fire Light', 'B301': 'Radiator', 'B302': 'Ventilation Duct',
    'B303': 'Air Conditioner', 'B401': 'Towel Rack', 'B402': 'Faucet', 'B403': 'Interior Door Handle/Lock',
    'B404': 'Window', 'B405': 'Hinge', 'B501': 'Power Socket', 'B502': 'Switch',
    'B503': 'Lighting Fixture', 'B504': 'Light Bulb', 'B505': 'Fly Killer Lamp', 'B506': 'Power Strip',
    'B601': 'Furniture', 'B602': 'Cabinet', 'B603': 'Ceiling', 'B604': 'Floor',
    'B605': 'Wall', 'B606': 'Blinds', 'B607': 'Skirting Board', 'B701': 'Drainage',
    'B702': 'Bathtub', 'B703': 'Mirror', 'B704': 'Tile', 'B705': 'Sink',
    'B706': 'Shower Head', 'B707': 'Toilet', 'B708': 'Washbasin', 'B801': 'Other',
    'B901': 'Network Equipment'
}

LOCATION_CODE_MAP = {
    '002': 'Bedroom',
    '004': 'Kitchen',
    '008': 'Bathroom',
    '009': 'Living Room',
    '001': 'Apartment Exterior',
    '003': 'Work Area Corridor',
    '005': 'Back-of-house Area',
    '006': 'Front-of-house Area',
    '011': 'Elevator Hall - Rear',
    '010': 'Elevator Hall - Front',
    '007': 'Parking Lot',
    '012': 'Fire Escape Staircase',
}

# --- 步骤 2: 创建查询函数 ---
def get_service_name(code):
    """
    根据服务代码查询服务项目名称。
    如果代码不存在，则返回一个提示信息。
    """
    if not code:
        return "Not Provided"
    return SERVICE_CODE_MAP.get(code, f"Unknown Code ({code})")


# --- 辅助函数 ---
def convert_excel_date(excel_serial_date_str):
    if not excel_serial_date_str: return "N/A"
    try:
        excel_serial_date = float(excel_serial_date_str)
        base_date = datetime.datetime(1899, 12, 30)
        delta = datetime.timedelta(days=excel_serial_date)
        return (base_date + delta).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return excel_serial_date_str


# --- 数据加载与搜索函数 (无变化) ---
def parse_service_orders(xml_file):
    print(f"Loading data from '{xml_file}'...")
    if not os.path.exists(xml_file):
        print(f"Error: File '{xml_file}' not found.")
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
        print(f"Successfully loaded {len(orders)} work orders.\n")
        return orders
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file. Error: {e}")
        return None


def search_by_rmno(orders, room_number):
    if not room_number: return []
    search_term = room_number.lower().strip()
    return [order for order in orders if order.get('rmno', '').lower().strip() == search_term]

def sanitize_for_display(text):
    """
    清理字符串，将可能破坏布局的控制字符（如换行、回车、U+2028等）替换为空格。
    这确保了每个字段的内容不会意外地跨越多行。
    """
    if not isinstance(text, str):
        return text

    # 正则表达式，匹配所有C0和C1控制字符，以及Unicode的行/段落分隔符
    control_char_regex = re.compile(r'[\x00-\x1F\x7F-\x9F\u2028\u2029]')

    # 将所有匹配到的控制字符替换为一个空格，防止单词粘连
    sanitized_text = control_char_regex.sub(' ', text)

    return sanitized_text

# --- 步骤 3: 修改输出格式 ---
def format_results_string(results):
    if not results:
        return ">> No related work orders found."

    output_parts = []
    output_parts.append(f"--- Found {len(results)} related work orders ---\n\n")

    for i, order in enumerate(results):
        # 获取服务代码并查找其名称
        product_code = order.get('product_code', '')
        service_name = get_service_name(product_code)

        location_code = order.get('location', '')
        location_name = LOCATION_CODE_MAP.get(location_code)

        # 转换时间
        create_dt_human = convert_excel_date(order.get('create_datetime', ''))
        complete_dt_human = convert_excel_date(order.get('complete_date', ''))

        sanitized_requirement = sanitize_for_display(order.get('requirement') or 'None')
        sanitized_entry_guidelines = sanitize_for_display(order.get('entry_guidelines') or 'None')

        output_parts.append(f"【Record {i + 1}】\n")
        output_parts.append(f"  Order ID:             {order.get('id', 'N/A')}\n")
        output_parts.append(f"  Room No.:             {order.get('rmno', 'N/A')}\n")
        output_parts.append(f"  Service Item:         {service_name} ({product_code or 'No Code'})\n")
        output_parts.append(f"  Specific Location:    {location_name} ({location_code or 'No Code'})\n")
        output_parts.append(f"  Requirement Desc.:    {sanitized_requirement}\n")
        output_parts.append(f"  Priority:             {order.get('priority', 'No Description')}\n")
        output_parts.append(f"  Entry Guidelines:     {sanitized_entry_guidelines}\n")
        output_parts.append(f"  Service State:        {order.get('service_state', 'N/A')}\n")
        output_parts.append(f"  Service Staff:        {order.get('service_man', 'Not Assigned')}\n")
        output_parts.append(f"  Resolution:           {order.get('remark', 'None')}\n")
        output_parts.append(f"  Creation Time:        {create_dt_human}\n")
        output_parts.append(f"  Completion Time:      {complete_dt_human}\n")
        output_parts.append("-" * 25 + "\n\n")

    return "".join(output_parts)


def main():
    all_orders = parse_service_orders(XML_FILE_PATH)
    if all_orders is None: return


    print("Welcome to the Service Work Order Inquiry System!")
    while True:
        room_number_input = input("Please enter the room number to query (enter 'q' to quit): ")
        if room_number_input.lower().strip() == 'q':
            print("Thank you for using, goodbye!")
            break
        found_orders = search_by_rmno(all_orders, room_number_input)
        result_string = format_results_string(found_orders)
        print(result_string)


if __name__ == "__main__":
    main()