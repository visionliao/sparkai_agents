import pandas as pd
import os
from lxml import etree
from datetime import datetime, timedelta

# --- 配置 ---
XML_FILE_PATH = 'master_guest.xml'

# 定义重要字段列表
IMPORTANT_FIELDS = [
    'id', 'profile_id', 'name', 'sex_like', 'birth', 'language',
    'mobile', 'email', 'nation', 'country', 'state', 'street',
    'id_code', 'id_no', 'hotel_id', 'profile_type', 'times_in',
    'create_user', 'create_datetime', 'modify_user', 'modify_datetime',
]

# 字段名到中文描述的映射
FIELD_NAME_MAPPING = {
    'id': '主键ID', 'profile_id': '客户档案ID', 'name': '姓名',
    'sex_like': '推断性别', 'birth': '出生日期', 'language': '语言代码',
    'mobile': '手机', 'email': '电子邮件', 'nation': '国籍代码',
    'country': '国家代码', 'state': '省份/州代码', 'street': '街道地址',
    'id_code': '证件类型代码', 'id_no': '证件号码', 'hotel_id': '酒店ID',
    'profile_type': '客户档案类型', 'times_in': '入住次数',
    'create_user': '创建用户', 'create_datetime': '创建时间',
    'modify_user': '修改用户', 'modify_datetime': '修改时间',
}


def get_display_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if '\u4e00' <= char <= '\u9fff' else 1
    return width


def convert_excel_date(excel_date):
    try:
        num_date = float(excel_date)
        base_date = datetime(1899, 12, 30)
        dt = base_date + timedelta(days=num_date)
        return dt.strftime('%Y-%m-%d %H:%M:%S') if num_date != int(num_date) else dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return excel_date


def load_data_from_xml(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        print(f"错误：文件 '{file_path}' 不存在。")
        return None
    try:
        tree = etree.parse(file_path)
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = tree.xpath('.//ss:Row', namespaces=ns)
        if not rows: return None
        header = [cell.text for cell in rows[0].xpath('.//ss:Data', namespaces=ns)]
        all_rows_data = [[cell.text if cell.text is not None else '' for cell in row.xpath('.//ss:Data', namespaces=ns)]
                         for row in rows[1:]]
        df = pd.DataFrame([row for row in all_rows_data if len(row) == len(header)], columns=header)

        if 'id' not in df.columns: return None
        df['id'] = pd.to_numeric(df['id'], errors='coerce')
        df.dropna(subset=['id'], inplace=True)
        df['id'] = df['id'].astype(int)

        date_columns = ['birth', 'create_datetime', 'modify_datetime']
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_excel_date)

        print(f"成功加载并处理了 {len(df)} 条记录。")
        return df
    except Exception as e:
        print(f"加载或处理XML文件时发生错误: {e}")
        return None


# --- 【核心新函数】 ---
def get_query_result_as_string(df: pd.DataFrame, query_id: int) -> str:
    """
    查询指定ID的数据，并将格式化后的结果作为单个字符串返回。

    Args:
        df (pd.DataFrame): 包含所有客户数据的DataFrame。
        query_id (int): 要查询的客户ID。

    Returns:
        str: 格式化后的查询结果字符串，或一条“未找到”的消息。
    """
    result = df[df['id'] == query_id]

    if result.empty:
        return f"--- 未找到 ID 为 {query_id} 的记录 ---"

    record = result.iloc[0]
    output_lines = []

    # 添加标题行
    output_lines.append(f"--- ID: {query_id} 的核心数据 ---")

    max_label_width = 15
    for field in IMPORTANT_FIELDS:
        if field in record:
            display_name = FIELD_NAME_MAPPING.get(field, field)
            value = record[field]
            display_value = value if pd.notna(value) and str(value).strip() != '' else "[空]"

            if field == 'sex_like':
                if display_value == '>':
                    display_value = "男"
                elif display_value == '?':
                    display_value = "女"

            padding_spaces = " " * (max_label_width - get_display_width(display_name))
            line = f"{display_name}{padding_spaces}: {display_value}"
            output_lines.append(line)
        else:
            line = f"{FIELD_NAME_MAPPING.get(field, field)}: [字段未找到]"
            output_lines.append(line)

    # 添加结尾行
    output_lines.append("----------------------------")

    # 将所有行用换行符连接成一个字符串并返回
    return "\n".join(output_lines)


# --- 【新增功能：多次查询，参数为字符串类型】 ---
def get_multiple_query_results_as_string(df: pd.DataFrame, query_ids_str: str) -> str:
    """
    解析逗号分隔的ID字符串，查询指定ID列表的数据，并将格式化后的结果作为单个字符串返回。
    每个记录之间用分隔符隔开。此函数通过调用 get_query_result_as_string 来复用单次查询接口。

    Args:
        df (pd.DataFrame): 包含所有客户数据的DataFrame。
        query_ids_str (str): 逗号分隔的客户ID字符串，例如 "3664,3494,9999"。

    Returns:
        str: 格式化后的查询结果字符串，包含所有有效ID的信息。
    """
    all_results = []
    invalid_ids = []
    # 定义一个清晰的分隔符，用于分隔不同ID的查询结果
    separator = "\n\n" + "=" * 60 + "\n\n"

    # 解析输入的字符串为ID列表
    raw_ids = [id_str.strip() for id_str in query_ids_str.split(',') if id_str.strip()]

    if not raw_ids:
        return "输入为空或不包含有效ID。"

    for id_part in raw_ids:
        try:
            q_id = int(id_part)
            # 调用原有的单次查询接口来获取每个ID的结果
            result_string = get_query_result_as_string(df, q_id)
            all_results.append(result_string)
        except ValueError:
            invalid_ids.append(id_part)
            # 可以在这里添加一个消息，说明该ID无效，但为了简洁，我们只收集无效ID

    output_str = ""
    if all_results:
        output_str = separator.join(all_results)
    else:
        output_str = "未查询到任何有效记录。"

    if invalid_ids:
        output_str += f"\n\n--- 注意：以下ID无效或无法解析，已跳过：{', '.join(invalid_ids)} ---"

    return output_str


def query_and_display_interactive(df: pd.DataFrame):
    """
    启动一个交互式循环，允许用户输入单个或多个客户ID进行查询，并将结果打印。
    """
    while True:
        user_input = input(
            "\n请输入要查询的客户 ID (可输入多个，用逗号分隔，如: 3664,3494；输入 'q' 或 'quit' 退出): ").strip()
        if user_input.lower() in ['q', 'quit']:
            print("脚本退出。")
            break

        # 直接将用户输入字符串传递给多查询函数
        # 错误处理（如非数字ID）现在由 get_multiple_query_results_as_string 内部处理
        result_string = get_multiple_query_results_as_string(df, user_input)
        print(result_string)


if __name__ == "__main__":
    guest_df = load_data_from_xml(XML_FILE_PATH)

    if guest_df is not None:
        # --- 示例：如何将单个查询结果存入变量 (保持不变，直接调用单次查询接口) ---
        print("\n--- 将ID 3664 的查询结果存入变量 ---")
        query_id_example = 3664

        # 调用函数，将返回的字符串存入 `result_variable`
        result_variable = get_query_result_as_string(guest_df, query_id_example)

        print("单个查询结果已成功存入变量 'result_variable'。")
        print("现在可以对这个变量进行操作，例如打印它：\n")

        # 打印变量的内容
        print(result_variable)

        # --- 示例：如何将多个查询结果存入变量 (使用新增的多查询接口，参数为字符串) ---
        print("\n\n--- 将ID 3664、3494 和一个不存在的 ID (9999) 以及一个无效输入 ('abc') 的查询结果存入变量 ---")
        # 参数现在是一个字符串
        multiple_query_ids_str_example = "3664, 3494, 9999, abc"

        # 调用新增的多查询函数，将返回的字符串存入 `multiple_results_variable`
        multiple_results_variable = get_multiple_query_results_as_string(guest_df, multiple_query_ids_str_example)

        print("多个查询结果已成功存入变量 'multiple_results_variable'。")
        print("现在可以对这个变量进行操作，例如打印它：\n")

        # 打印变量的内容
        print(multiple_results_variable)

        # --- 启动交互式查询 (已更新以支持多查询，且参数传递为字符串) ---
        print("\n\n--- 现在启动交互式查询 (支持单个或多个ID) ---")
        query_and_display_interactive(guest_df)
    else:
        print("数据未能成功加载，程序即将退出。")