import pandas as pd
import os
from lxml import etree
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# --- 配置 ---
XML_FILE_PATH = 'master_guest.xml'
XML_STATUS_RENT_PATH = 'master_base.xml'

IMPORTANT_FIELDS = [
    'id', 'profile_id', 'name', 'sex_like', 'birth', 'language',
    'mobile', 'email', 'nation', 'country', 'state', 'street',
    'id_code', 'id_no', 'hotel_id', 'profile_type', 'times_in',
    'create_user', 'create_datetime', 'modify_user', 'modify_datetime',
]
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

        print(f"成功从 '{file_path}' 加载并处理了 {len(df)} 条主记录。")
        return df
    except Exception as e:
        print(f"加载或处理 '{file_path}' 时发生错误: {e}")
        return None


# ---【核心变更 2】--- 新增一个函数，用于加载包含status和rent的XML文件
def load_status_rent_data_from_xml(file_path: str) -> pd.DataFrame:
    """
    专门从XML文件加载住客状态和租金数据。
    假设该文件至少包含 'profile_id', 'status', 'rent' 列。
    """
    if not os.path.exists(file_path):
        print(f"信息：状态/租金文件 '{file_path}' 不存在，将跳过加载。")
        return None
    try:
        tree = etree.parse(file_path)
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = tree.xpath('.//ss:Row', namespaces=ns)
        if not rows: return None

        header = [cell.text for cell in rows[0].xpath('.//ss:Data', namespaces=ns)]
        # 确保关键列存在
        if 'id' not in header:
            print(f"错误：'{file_path}' 中缺少关键合并列 'id'。")
            return None

        all_rows_data = [[cell.text if cell.text is not None else '' for cell in row.xpath('.//ss:Data', namespaces=ns)]
                         for row in rows[1:]]
        df = pd.DataFrame([row for row in all_rows_data if len(row) == len(header)], columns=header)

        # 数据类型转换，确保合并键类型一致
        df['id'] = pd.to_numeric(df['id'], errors='coerce')
        df.dropna(subset=['id'], inplace=True)

        print(f"成功从 '{file_path}' 加载了 {len(df)} 条状态/租金记录。")
        return df[['id', 'sta', 'full_rate_long']]  # 只返回需要的列
    except Exception as e:
        print(f"加载或处理 '{file_path}' 时发生错误: {e}")
        return None


# (get_query_result_as_string, get_multiple_query_results_as_string, get_guest_statistics, query_and_display_interactive 函数保持不变)
# ...
def get_query_result_as_string(df: pd.DataFrame, query_id: int) -> str:
    result = df[df['id'] == query_id]
    if result.empty: return f"--- 未找到 ID 为 {query_id} 的记录 ---"
    record = result.iloc[0]
    output_lines = [f"--- ID: {query_id} 的核心数据 ---"]
    max_label_width = 15
    for field in IMPORTANT_FIELDS:
        if field in record:
            display_name = FIELD_NAME_MAPPING.get(field, field)
            value = record[field]
            display_value = value if pd.notna(value) and str(value).strip() != '' else "[空]"
            if field == 'sex_like': display_value = {"_": "男", "?": "女"}.get(display_value, display_value)
            padding_spaces = " " * (max_label_width - get_display_width(display_name))
            output_lines.append(f"{display_name}{padding_spaces}: {display_value}")
        else:
            output_lines.append(f"{FIELD_NAME_MAPPING.get(field, field)}: [字段未找到]")
    output_lines.append("----------------------------")
    return "\n".join(output_lines)


def get_multiple_query_results_as_string(df: pd.DataFrame, query_ids_str: str) -> str:
    all_results = []
    invalid_ids = []
    separator = "\n\n" + "=" * 60 + "\n\n"
    raw_ids = [id_str.strip() for id_str in query_ids_str.split(',') if id_str.strip()]
    if not raw_ids: return "输入为空或不包含有效ID。"
    for id_part in raw_ids:
        try:
            q_id = int(id_part)
            all_results.append(get_query_result_as_string(df, q_id))
        except ValueError:
            invalid_ids.append(id_part)
    output_str = separator.join(all_results) if all_results else "未查询到任何有效记录。"
    if invalid_ids:
        output_str += f"\n\n--- 注意：以下ID无效或无法解析，已跳过：{', '.join(invalid_ids)} ---"
    return output_str


def get_guest_statistics(df: pd.DataFrame, name: Optional[str] = None, room_number: Optional[str] = None,
                         status: Optional[str] = None, nation: Optional[str] = None, min_age: Optional[int] = None,
                         max_age: Optional[int] = None, min_rent: Optional[float] = None,
                         max_rent: Optional[float] = None, remark_keyword: Optional[str] = None) -> Dict[str, Any]:
    filtered_df = df.copy()

    def apply_filter(column, value, exact=False):
        nonlocal filtered_df
        if column not in filtered_df.columns:
            print(f"警告：数据中不存在 '{column}' 列，相关筛选条件已忽略。")
            return
        if pd.isna(value): return
        filtered_df.dropna(subset=[column], inplace=True)
        if exact:
            filtered_df = filtered_df[filtered_df[column] == value]
        else:
            filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(value, case=False, na=False)]

    if name: apply_filter('name', name)
    if room_number: apply_filter('room_number', room_number, exact=True)
    if status: apply_filter('sta', status, exact=True)
    if nation: apply_filter('nation', nation)
    if remark_keyword: apply_filter('remark', remark_keyword)
    if min_age is not None or max_age is not None:
        if 'birth' in filtered_df.columns:
            birth_dates = pd.to_datetime(filtered_df['birth'], errors='coerce')
            filtered_df['age'] = (pd.to_datetime('today') - birth_dates).dt.days / 365.25
            filtered_df.dropna(subset=['age'], inplace=True)
            if not filtered_df.empty: filtered_df['age'] = filtered_df['age'].astype(int)
            if min_age is not None: filtered_df = filtered_df[filtered_df['age'] >= min_age]
            if max_age is not None: filtered_df = filtered_df[filtered_df['age'] <= max_age]
        else:
            print("警告：数据中不存在 'birth' 列，年龄筛选已忽略。")
    if min_rent is not None or max_rent is not None:
        if 'full_rate_long' in filtered_df.columns:
            filtered_df['full_rate_long'] = pd.to_numeric(filtered_df['full_rate_long'], errors='coerce')
            filtered_df.dropna(subset=['full_rate_long'], inplace=True)
            if min_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] >= min_rent]
            if max_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] <= max_rent]
        else:
            print(f"警告：数据中不存在 'full_rate_long' 列，租金筛选已忽略。")
    record_count = len(filtered_df)
    if record_count == 0: return {"count": 0, "analysis": None}
    unique_col = 'profile_id' if 'profile_id' in filtered_df.columns else 'id'
    analysis_df = filtered_df.drop_duplicates(subset=[unique_col])
    unique_guest_count = len(analysis_df)
    age_dist, nat_dist, gen_dist = [], [], []
    if 'age' in analysis_df.columns:
        bins, labels = [0, 18, 30, 45, 60, 150], ['18岁以下', '18-30岁', '31-45岁', '46-60岁', '60岁以上']
        age_groups = pd.cut(analysis_df['age'], bins=bins, labels=labels, right=False)
        age_counts = age_groups.value_counts().sort_index()
        for group, count in age_counts.items():
            age_dist.append(
                {"group": group, "count": int(count), "percentage": f"{(count / unique_guest_count) * 100:.2f}%"})
    if 'nation' in analysis_df.columns:
        nation_counts = analysis_df['nation'].value_counts()
        top_nations = nation_counts.nlargest(9)
        for nation, count in top_nations.items():
            nat_dist.append({"nation": nation if nation else "未知", "count": int(count),
                             "percentage": f"{(count / unique_guest_count) * 100:.2f}%"})
        if len(nation_counts) > 9:
            other_count = nation_counts.iloc[9:].sum()
            nat_dist.append({"nation": "其他", "count": int(other_count),
                             "percentage": f"{(other_count / unique_guest_count) * 100:.2f}%"})
    if 'sex_like' in analysis_df.columns:
        gender_map = {'>': '男', '?': '女'}
        gender_counts = analysis_df['sex_like'].map(gender_map).fillna('未知').value_counts()
        for gender, count in gender_counts.items():
            gen_dist.append(
                {"gender": gender, "count": int(count), "percentage": f"{(count / unique_guest_count) * 100:.2f}%"})
    return {"count": record_count,
            "analysis": {"based_on": f"基于 {unique_guest_count} 名独立住客的分析", "age_distribution": age_dist,
                         "nationality_distribution": nat_dist, "gender_distribution": gen_dist}}


def query_and_display_interactive(df: pd.DataFrame):
    while True:
        user_input = input(
            "\n请输入要查询的客户 ID (可输入多个，用逗号分隔，如: 3664,3494；输入 'q' 或 'quit' 退出): ").strip()
        if user_input.lower() in ['q', 'quit']:
            print("脚本退出。")
            break
        print(get_multiple_query_results_as_string(df, user_input))


if __name__ == "__main__":
    # ---【核心变更 3】--- 修改数据加载和合并逻辑

    # 1. 加载主住客数据
    guest_df = load_data_from_xml(XML_FILE_PATH)

    if guest_df is not None:
        # 2. 加载状态和租金数据
        status_rent_df = load_status_rent_data_from_xml(XML_STATUS_RENT_PATH)

        # 3. 如果状态租金数据成功加载，则执行合并
        if status_rent_df is not None:
            # 确保合并键的数据类型一致
            guest_df['profile_id'] = pd.to_numeric(guest_df['id'], errors='coerce')

            print(f"\n正在合并数据...")
            # 使用左连接（left join）进行合并
            merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
            print("数据合并完成。")
        else:
            # 如果第二个文件不存在或加载失败，则继续使用原始数据
            merged_df = guest_df
            print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

        # --- 后续所有操作都使用合并后的 `merged_df` ---

        # 示例1：将单个查询结果存入变量
        print("\n--- 将ID 3664 的查询结果存入变量 ---")
        result_variable = get_query_result_as_string(merged_df, 3664)
        print("单个查询结果已成功存入变量 'result_variable'。打印如下：\n")
        print(result_variable)

        # ... (后续示例和交互式查询都自动使用合并后的数据) ...
        print("\n\n" + "=" * 20 + " 功能演示：统计分析 " + "=" * 20)
        print("\n--- 示例：获取所有在住('I')、年龄在20到40岁之间、月租金高于3000的住客统计信息 ---")

        stats_result = get_guest_statistics(
            merged_df,
            status='I',
            min_age=0,

            min_rent=0
        )

        print(f"\n查询到的记录总数: {stats_result['count']}")
        if stats_result['analysis']:
            analysis = stats_result['analysis']
            print(f"统计概要: {analysis['based_on']}")
            print("\n年龄分布:")
            for item in analysis['age_distribution']: print(
                f"  - {item['group']:<10}: {item['count']}人 ({item['percentage']})")
            print("\n国籍分布:")
            for item in analysis['nationality_distribution']: print(
                f"  - {item['nation']:<10}: {item['count']}人 ({item['percentage']})")
            print("\n性别分布:")
            for item in analysis['gender_distribution']: print(
                f"  - {item['gender']:<10}: {item['count']}人 ({item['percentage']})")
        else:
            print("没有符合条件的住客可以进行分析。")
        print("=" * 64)

        print("\n\n--- 现在启动交互式查询 (支持单个或多个ID) ---")
        query_and_display_interactive(merged_df)
    else:
        print("主数据未能成功加载，程序即将退出。")