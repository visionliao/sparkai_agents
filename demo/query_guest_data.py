import pandas as pd
import os
from lxml import etree
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union

# --- 配置 ---
XML_FILE_PATH = 'master_guest.xml'
XML_STATUS_RENT_PATH = 'master_base.xml'

# 在精确查询中重点显示的字段
IMPORTANT_FIELDS = [
    'id', 'profile_id', 'name', 'sex_like', 'birth', 'language',
    'mobile', 'email', 'nation', 'country', 'state', 'street',
    'id_code', 'id_no', 'hotel_id', 'profile_type', 'times_in', 'remark_y',
    'create_user', 'create_datetime', 'modify_user', 'modify_datetime',
    'sta', 'rmno', 'full_rate_long', 'arr', 'dep'
]
# 字段名的中文映射
FIELD_NAME_MAPPING = {
    'id': '主键ID', 'profile_id': '客户档案ID', 'name': '姓名',
    'sex_like': '推断性别', 'birth': '出生日期', 'language': '语言代码',
    'mobile': '手机', 'email': '电子邮件', 'nation': '国籍代码',
    'country': '国家代码', 'state': '省份/州代码', 'street': '街道地址',
    'id_code': '证件类型代码', 'id_no': '证件号码', 'hotel_id': '酒店ID',
    'profile_type': '客户档案类型', 'times_in': '入住次数', 'remark_y': '备注',
    'create_user': '创建用户', 'create_datetime': '创建时间',
    'modify_user': '修改用户', 'modify_datetime': '修改时间',
    'sta': '在住状态', 'rmno': '房间号', 'full_rate_long': '月租金', 'arr': '到达日期', 'dep': '离开日期'
}


def get_display_width(text: str) -> int:
    """计算字符串的显示宽度，中文字符计为2，英文字符计为1"""
    width = 0
    for char in text:
        width += 2 if '\u4e00' <= char <= '\u9fff' else 1
    return width


def load_data_from_xml(file_path: str) -> pd.DataFrame:
    """从Excel导出的XML文件中加载主客户数据"""
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
                numeric_dates = pd.to_numeric(df[col], errors='coerce')
                converted_dates = pd.to_timedelta(numeric_dates, unit='D') + pd.to_datetime('1899-12-30')
                df[col] = converted_dates.fillna(pd.to_datetime(df[col], format='mixed', errors='coerce'))

        print(f"成功从 '{file_path}' 加载并处理了 {len(df)} 条主记录。")
        return df
    except Exception as e:
        print(f"加载或处理 '{file_path}' 时发生错误: {e}")
        return None


def load_status_rent_data_from_xml(file_path: str) -> pd.DataFrame:
    """从XML文件加载客户的状态和租金信息"""
    if not os.path.exists(file_path):
        print(f"信息：状态/租金文件 '{file_path}' 不存在，将跳过加载。")
        return None
    try:
        tree = etree.parse(file_path)
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = tree.xpath('.//ss:Row', namespaces=ns)
        if not rows: return None

        header = [cell.text for cell in rows[0].xpath('.//ss:Data', namespaces=ns)]
        if 'id' not in header:
            print(f"错误：'{file_path}' 中缺少关键合并列 'id'。")
            return None

        all_rows_data = [[cell.text if cell.text is not None else '' for cell in row.xpath('.//ss:Data', namespaces=ns)]
                         for row in rows[1:]]
        df = pd.DataFrame([row for row in all_rows_data if len(row) == len(header)], columns=header)

        df['id'] = pd.to_numeric(df['id'], errors='coerce')
        df.dropna(subset=['id'], inplace=True)
        df['id'] = df['id'].astype(int)

        date_columns = ['dep', 'arr']
        for col in date_columns:
            if col in df.columns:
                numeric_dates = pd.to_numeric(df[col], errors='coerce')
                converted_dates = pd.to_timedelta(numeric_dates, unit='D') + pd.to_datetime('1899-12-30')
                df[col] = converted_dates.fillna(pd.to_datetime(df[col], format='mixed', errors='coerce'))

        print(f"成功从 '{file_path}' 加载了 {len(df)} 条状态/租金记录。")
        return df[['id', 'sta', 'full_rate_long', 'dep', 'arr', 'rmno', 'remark']]
    except Exception as e:
        print(f"加载或处理 '{file_path}' 时发生错误: {e}")
        return None


def get_query_result_as_string(df: pd.DataFrame, query_id: int) -> str:
    """根据单个ID查询并格式化输出客户的核心数据"""
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
            if field == 'sex_like': display_value = {">": "男", "?": "女"}.get(display_value, display_value)
            padding_spaces = " " * (max_label_width - get_display_width(display_name))
            output_lines.append(f"{display_name}{padding_spaces}: {display_value}")
        else:
            output_lines.append(f"{FIELD_NAME_MAPPING.get(field, field)}: [字段未找到]")
    output_lines.append("----------------------------")
    return "\n".join(output_lines)


def get_multiple_query_results_as_string(df: pd.DataFrame, query_ids_str: str) -> str:
    """支持用逗号分隔的字符串查询多个ID"""
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
                         status: Union[str, List[str]] = None, nation: Optional[str] = None, min_age: Optional[int] = None,
                         max_age: Optional[int] = None, min_rent: Optional[float] = None,
                         max_rent: Optional[float] = None, remark_keyword: Optional[str] = None,
                         gender: Optional[str] = None, start_arr_date: Optional[Any] = None,
                         end_arr_date: Optional[Any] = None) -> Dict[str, Any]:
    """
    根据多种筛选条件对客户数据进行统计分析。
    【最终逻辑】:
    1. 每一条记录视为一个独立单元进行统计，不过滤任何行。
    2. 在年龄分布中，为无法解析的出生日期创建“年龄未知”类别。
    3. 保留租金为0的记录，当且仅当它是其所在房间的唯一记录时。
    """
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

    # --- 筛选逻辑 ---
    if name: apply_filter('name', name)
    if room_number: apply_filter('rmno', room_number, exact=True)
    if status:
        if 'sta' not in filtered_df.columns:
            print("警告：数据中不存在 'sta' 列，无法按状态筛选。")
        else:
            # 如果 status 是一个列表 (e.g., ['O', 'R'])，则使用 .isin() 进行多选
            if isinstance(status, list):
                filtered_df = filtered_df[filtered_df['sta'].isin(status)]
            # 如果 status 仍然是单个字符串，则保持原有的逻辑
            elif isinstance(status, str):
                if status == '实际当前在住':  # 'I' (在住) 有特殊的日期检查逻辑
                    if 'dep' in filtered_df.columns:
                        filtered_df = filtered_df[filtered_df['sta'] == 'I'].copy()
                        dep_dates = pd.to_datetime(filtered_df['dep'], errors='coerce')
                        today = pd.to_datetime('today').normalize()
                        filtered_df = filtered_df[dep_dates > today]
                    else:
                        print("警告：缺少 'dep' 列，无法准确筛选在住客人。")
                        # 作为备用方案，只按 'sta' == 'I' 筛选
                        filtered_df = filtered_df[filtered_df['sta'] == 'I']
                else:  # 其他单个状态，如 'O', 'R' 等，直接精确匹配
                    filtered_df = filtered_df[filtered_df['sta'] == status]
    if nation: apply_filter('nation', nation)
    if remark_keyword: apply_filter('remark_y', remark_keyword)
    if start_arr_date or end_arr_date:
        if 'arr' in filtered_df.columns:
            # 确保 'arr' 列是日期时间类型，以便比较
            filtered_df['arr'] = pd.to_datetime(filtered_df['arr'], errors='coerce')

            if start_arr_date:
                try:
                    start_date_dt = pd.to_datetime(start_arr_date)
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() >= start_date_dt]
                except Exception as e:
                    print(f"警告：无法解析开始日期 '{start_arr_date}'，该条件已忽略。错误: {e}")

            if end_arr_date:
                try:
                    end_date_dt = pd.to_datetime(end_arr_date)
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() <= end_arr_date]
                except Exception as e:
                    print(f"警告：无法解析结束日期 '{end_arr_date}'，该条件已忽略。错误: {e}")
        else:
            print("警告：数据中不存在 'arr' 列，无法按入住时间筛选。")

    # --- 不过滤，只计算和筛选 ---
    # 步骤1: 只要 'birth' 列存在，就尝试计算年龄，并保存在新列'age'中
    if 'birth' in filtered_df.columns:
        birth_dates = pd.to_datetime(filtered_df['birth'], errors='coerce')
        # 创建一个临时年龄列，无效日期计算结果为 NaT
        temp_age = (pd.to_datetime('today') - birth_dates).dt.days / 365.25
        # 将计算出的年龄（可能包含NaN）赋值给 'age' 列
        filtered_df['age'] = temp_age

    # 步骤2: 如果传入了年龄筛选参数，则在已生成的 'age' 列上进行筛选
    # 注意: 年龄筛选会自然地过滤掉 'age' 为 NaN 的记录
    if min_age is not None:
        if 'age' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['age'] >= min_age]
        else:
            print("警告: 'birth'列不存在或无法解析，无法按最小年龄筛选。")

    if max_age is not None:
        if 'age' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['age'] <= max_age]
        else:
            print("警告: 'birth'列不存在或无法解析，无法按最大年龄筛选。")
    # --- 新年龄逻辑结束 ---

    # 租金筛选逻辑 (保持不变)
    if min_rent is not None or max_rent is not None:
        if 'full_rate_long' in filtered_df.columns:
            filtered_df['full_rate_long'] = pd.to_numeric(filtered_df['full_rate_long'], errors='coerce')
            filtered_df.dropna(subset=['full_rate_long'], inplace=True)
            if min_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] >= min_rent]
            if max_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] <= max_rent]
        else:
            print(f"警告：数据中不存在 'full_rate_long' 列，租金筛选已忽略。")

    # 总租金计算 (保持不变)
    overall_total_rent = 0
    if 'full_rate_long' in filtered_df.columns:
        rent_data_overall = pd.to_numeric(filtered_df['full_rate_long'], errors='coerce').dropna()
        if not rent_data_overall.empty:
            overall_total_rent = rent_data_overall.sum()

    # 性别筛选 (保持不变)
    if gender:
        gender_map_internal = {'男': '>', '女': '?'}
        internal_gender_code = gender_map_internal.get(gender)
        if internal_gender_code and 'sex_like' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['sex_like'] == internal_gender_code]
        else:
            print(f"警告：无效的性别输入 '{gender}' 或缺少 'sex_like' 列，该筛选条件已忽略。")

    # 最终记录数
    record_count = len(filtered_df)
    if record_count == 0: return {"count": 0, "analysis": None}

    age_dist, nat_dist, gen_dist = [], [], []

    # --- 【新年龄分布统计】 ---
    if 'age' in filtered_df.columns:
        # 1. 筛选出年龄有效的记录
        age_data = filtered_df['age'].dropna().astype(int)

        # 2. 计算年龄无效的记录数
        unknown_age_count = record_count - len(age_data)

        # 3. 对有效年龄进行分段统计
        if not age_data.empty:
            bins, labels = [0, 18, 30, 45, 60, 150], ['18岁以下', '18-30岁', '31-45岁', '46-60岁', '60岁以上']
            age_groups = pd.cut(age_data, bins=bins, labels=labels, right=False)
            age_counts = age_groups.value_counts().sort_index()
            for group, count in age_counts.items():
                age_dist.append(
                    {"group": group, "count": int(count), "percentage": f"{(count / record_count) * 100:.2f}%"})

        # 4. 如果存在未知年龄的记录，将其作为一个单独的类别添加
        if unknown_age_count > 0:
            age_dist.append(
                {"group": "年龄未知", "count": int(unknown_age_count),
                 "percentage": f"{(unknown_age_count / record_count) * 100:.2f}%"})

    # 国籍和性别分布 (保持不变, 分母为 record_count)
    if 'nation' in filtered_df.columns:
        nation_counts = filtered_df['nation'].value_counts()
        top_nations = nation_counts.nlargest(9)
        for nation, count in top_nations.items():
            nat_dist.append({"nation": nation if nation else "未知", "count": int(count),
                             "percentage": f"{(count / record_count) * 100:.2f}%"})
        if len(nation_counts) > 9:
            other_count = nation_counts.iloc[9:].sum()
            nat_dist.append({"nation": "其他", "count": int(other_count),
                             "percentage": f"{(other_count / record_count) * 100:.2f}%"})

    if 'sex_like' in filtered_df.columns:
        gender_map = {'>': '男', '?': '女'}
        gender_counts = filtered_df['sex_like'].map(gender_map).fillna('未知').value_counts()
        for gender_val, count in gender_counts.items():
            gen_dist.append(
                {"gender": gender_val, "count": int(count), "percentage": f"{(count / record_count) * 100:.2f}%"})

    # 租金分析 (保持不变)
    rent_analysis = None
    if 'full_rate_long' in filtered_df.columns and 'rmno' in filtered_df.columns:
        rent_df = filtered_df[['rmno', 'full_rate_long']].copy()
        rent_df['full_rate_long'] = pd.to_numeric(rent_df['full_rate_long'], errors='coerce')
        rent_df.dropna(subset=['full_rate_long', 'rmno'], inplace=True)
        room_counts = rent_df.groupby('rmno')['rmno'].transform('size')
        keep_positive_rent = rent_df['full_rate_long'] > 0
        keep_special_zero_rent = (rent_df['full_rate_long'] == 0) & (room_counts == 1)
        keep_mask = keep_positive_rent | keep_special_zero_rent
        final_rent_df = rent_df[keep_mask]
        rent_data = final_rent_df['full_rate_long']

        if not rent_data.empty:
            # (租金分析的其余部分代码与之前版本相同, 为简洁省略)
            based_on_rent_count = len(rent_data)
            rent_dist = []
            bins = [-float('inf'), 3000, 5000, 7000, 10000, float('inf')]
            labels = ['低于3000', '3000-5000', '5001-7000', '7001-10000', '高于10000']
            rent_groups = pd.cut(rent_data, bins=bins, labels=labels, right=False)
            rent_counts = rent_groups.value_counts().sort_index()
            for group, count in rent_counts.items():
                rent_dist.append(
                    {"range": group, "count": int(count), "percentage": f"{(count / based_on_rent_count) * 100:.2f}%"})
            guests_with_rent_df = filtered_df.loc[final_rent_df.index].copy()
            guests_with_rent_df['full_rate_long'] = pd.to_numeric(guests_with_rent_df['full_rate_long'],
                                                                  errors='coerce')
            gender_rent_dist = []
            if 'sex_like' in guests_with_rent_df.columns:
                gender_map = {'>': '男', '?': '女'}
                gender_counts_in_rent = guests_with_rent_df['sex_like'].map(gender_map).fillna('未知').value_counts()
                for gender_val, count in gender_counts_in_rent.items():
                    gender_rent_dist.append({"gender": gender_val, "count": int(count),
                                             "percentage": f"{(count / based_on_rent_count) * 100:.2f}%"})
            gender_rent_contribution = []
            if overall_total_rent > 0 and 'sex_like' in guests_with_rent_df.columns:
                gender_map = {'>': '男', '?': '女'}
                rent_sum_by_gender = guests_with_rent_df.groupby('sex_like')['full_rate_long'].sum()
                for gender_code, rent_sum in rent_sum_by_gender.items():
                    gender_name = gender_map.get(gender_code, '未知')
                    percentage = (rent_sum / overall_total_rent) * 100
                    gender_rent_contribution.append(
                        {"gender": gender_name, "total_rent": f"{rent_sum:.2f}", "percentage": f"{percentage:.2f}%"})
            rent_analysis = {"average_rent": f"{rent_data.mean():.2f}", "median_rent": f"{rent_data.median():.2f}",
                             "min_rent": f"{rent_data.min():.2f}", "max_rent": f"{rent_data.max():.2f}",
                             "based_on_count": based_on_rent_count, "distribution": rent_dist,
                             "gender_breakdown": gender_rent_dist,
                             "gender_contribution_to_total_rent": gender_rent_contribution}
    else:
        print("警告: 租金分析需要 'full_rate_long' 和 'rmno' 两列数据。")

    return {"count": record_count,
            "analysis": {"based_on": f"基于 {record_count} 条符合条件的入住记录的分析",
                         "age_distribution": age_dist,
                         "nationality_distribution": nat_dist,
                         "gender_distribution": gen_dist,
                         "rent_analysis": rent_analysis}}

def get_filtered_guest_details(df: pd.DataFrame, name: Optional[str] = None, room_number: Optional[str] = None,
                               status: Union[str, List[str]] = None, nation: Optional[str] = None, min_age: Optional[int] = None,
                               max_age: Optional[int] = None, min_rent: Optional[float] = None,
                               max_rent: Optional[float] = None, remark_keyword: Optional[str] = None,
                               gender: Optional[str] = None, start_arr_date: Optional[Any] = None,
                               end_arr_date: Optional[Any] = None) -> pd.DataFrame:
    """
    根据多种筛选条件获取住客的详细信息。
    此函数复用了 get_guest_statistics 中的筛选逻辑，但返回的是一个包含所有符合条件记录的DataFrame。

    :return: 一个包含筛选结果的 pandas DataFrame。如果无结果，则返回一个空的 DataFrame。
    """
    filtered_df = df.copy()

    def apply_filter(column, value, exact=False):
        nonlocal filtered_df
        if column not in filtered_df.columns:
            return
        if pd.isna(value): return
        filtered_df.dropna(subset=[column], inplace=True)
        if exact:
            filtered_df = filtered_df[filtered_df[column] == value]
        else:
            filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(value, case=False, na=False)]

    # --- 筛选逻辑 (与 get_guest_statistics 完全相同) ---
    if name: apply_filter('name', name)
    if room_number: apply_filter('rmno', room_number, exact=True)
    if status:
        if 'sta' not in filtered_df.columns: pass
        else:
            if isinstance(status, list):
                filtered_df = filtered_df[filtered_df['sta'].isin(status)]
            elif isinstance(status, str):
                if status == '实际当前在住':
                    if 'dep' in filtered_df.columns:
                        filtered_df = filtered_df[filtered_df['sta'] == 'I'].copy()
                        dep_dates = pd.to_datetime(filtered_df['dep'], errors='coerce')
                        today = pd.to_datetime('today').normalize()
                        filtered_df = filtered_df[dep_dates > today]
                    else:
                        filtered_df = filtered_df[filtered_df['sta'] == 'I']
                else:
                    filtered_df = filtered_df[filtered_df['sta'] == status]
    if nation: apply_filter('nation', nation)
    if remark_keyword: apply_filter('remark_y', remark_keyword)
    if start_arr_date or end_arr_date:
        if 'arr' in filtered_df.columns:
            filtered_df['arr'] = pd.to_datetime(filtered_df['arr'], errors='coerce')
            if start_arr_date:
                try:
                    start_date_dt = pd.to_datetime(start_arr_date)
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() >= start_date_dt]
                except Exception: pass
            if end_arr_date:
                try:
                    end_date_dt = pd.to_datetime(end_arr_date)
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() <= end_date_dt]
                except Exception: pass
    if 'birth' in filtered_df.columns:
        birth_dates = pd.to_datetime(filtered_df['birth'], errors='coerce')
        temp_age = (pd.to_datetime('today') - birth_dates).dt.days / 365.25
        filtered_df['age'] = temp_age
    if min_age is not None and 'age' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['age'] >= min_age]
    if max_age is not None and 'age' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['age'] <= max_age]
    if min_rent is not None or max_rent is not None:
        if 'full_rate_long' in filtered_df.columns:
            filtered_df['full_rate_long'] = pd.to_numeric(filtered_df['full_rate_long'], errors='coerce')
            filtered_df.dropna(subset=['full_rate_long'], inplace=True)
            if min_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] >= min_rent]
            if max_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] <= max_rent]
    if gender:
        gender_map_internal = {'男': '>', '女': '?'}
        internal_gender_code = gender_map_internal.get(gender)
        if internal_gender_code and 'sex_like' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['sex_like'] == internal_gender_code]

    return filtered_df


def get_filtered_details_as_string(df: pd.DataFrame, name: Optional[str] = None, room_number: Optional[str] = None,
                                   status: Union[str, List[str]] = None, nation: Optional[str] = None,
                                   min_age: Optional[int] = None,
                                   max_age: Optional[int] = None, min_rent: Optional[float] = None,
                                   max_rent: Optional[float] = None, remark_keyword: Optional[str] = None,
                                   gender: Optional[str] = None, start_arr_date: Optional[Any] = None,
                                   end_arr_date: Optional[Any] = None) -> str:
    """
    根据多种筛选条件查询住客信息，并将所有结果整合成一个格式化的字符串。

    :return: 一个包含所有符合条件住客详细信息的、格式化好的单一字符串。
    """
    # 步骤 1: 复用筛选函数，获取符合条件的住客DataFrame
    filtered_guests_df = get_filtered_guest_details(df, name=name, room_number=room_number,
                                                    status=status, nation=nation, min_age=min_age,
                                                    max_age=max_age, min_rent=min_rent,
                                                    max_rent=max_rent, remark_keyword=remark_keyword,
                                                    gender=gender, start_arr_date=start_arr_date,
                                                    end_arr_date=end_arr_date)

    # 步骤 2: 处理查询结果
    if filtered_guests_df.empty:
        return f"--- 未找到符合条件的住客记录 ---"

    all_results = []
    # 定义一个清晰的分隔符，用于区分不同的客人信息
    separator = "\n" + "=" * 50 + "\n"

    # 步骤 3: 遍历结果，并复用格式化函数生成每个客人的信息字符串
    for guest_id in filtered_guests_df['id']:
        # 注意：这里我们向格式化函数传入原始的 df，以确保能找到所有字段
        all_results.append(get_query_result_as_string(df, guest_id))

    # 步骤 4: 将所有客人的信息字符串用分隔符连接成一个最终的大字符串
    # 同时在开头和结尾添加总数统计
    header = f"--- 查询到 {len(all_results)} 条符合条件的记录 ---"
    footer = f"--- 查询结束 ---"

    return header + separator + separator.join(all_results) + separator + footer

def print_stats_results(title: str, stats_result: Dict):
    """一个辅助函数，用于格式化并美观地打印统计结果"""
    print("\n" + "=" * 20 + f" {title} " + "=" * 20)
    print(f"\n查询到的记录总数: {stats_result['count']}")
    if stats_result.get('analysis'):
        analysis = stats_result['analysis']
        print(f"统计概要: {analysis['based_on']}")

        if analysis.get('age_distribution'):
            print("\n年龄分布:")
            for item in analysis['age_distribution']: print(
                f"  - {item['group']:<10}: {item['count']}人 ({item['percentage']})")

        if analysis.get('nationality_distribution'):
            print("\n国籍分布:")
            for item in analysis['nationality_distribution']: print(
                f"  - {item['nation']:<10}: {item['count']}人 ({item['percentage']})")

        if analysis.get('gender_distribution'):
            print("\n性别分布:")
            for item in analysis['gender_distribution']: print(
                f"  - {item['gender']:<10}: {item['count']}人 ({item['percentage']})")

        if analysis.get('rent_analysis'):
            rent_info = analysis['rent_analysis']
            print(f"\n租金分析 (基于 {rent_info['based_on_count']} 名有租金记录的住客):")
            print(f"  - 平均租金: {rent_info['average_rent']} /月")
            print(f"  - 租金中位数: {rent_info['median_rent']} /月")
            print(f"  - 租金范围: {rent_info['min_rent']} - {rent_info['max_rent']} /月")
            if rent_info.get('distribution'):
                print("  - 租金分段:")
                for item in rent_info['distribution']: print(
                    f"    - {item['range']:<12}: {item['count']}人 ({item['percentage']})")

            if rent_info.get('gender_breakdown'):
                print("  - 付费人数男女占比:")
                for item in rent_info['gender_breakdown']:
                    print(f"    - {item['gender']:<12}: {item['count']}人 ({item['percentage']})")

            if rent_info.get('gender_contribution_to_total_rent'):
                print("  - 租金总额贡献占比:")
                for item in rent_info['gender_contribution_to_total_rent']:
                    print(f"    - {item['gender']:<12}: 贡献总额 {item['total_rent']} ({item['percentage']})")

    else:
        print("没有符合条件的住客可以进行分析。")
    print("=" * (42 + len(title)))


if __name__ == "__main__":
    guest_df = load_data_from_xml(XML_FILE_PATH)

    if guest_df is not None:
        status_rent_df = load_status_rent_data_from_xml(XML_STATUS_RENT_PATH)

        if status_rent_df is not None:
            guest_df['id'] = pd.to_numeric(guest_df['id'], errors='coerce')
            status_rent_df['id'] = pd.to_numeric(status_rent_df['id'], errors='coerce')

            print(f"\n正在合并数据...")
            merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
            print("数据合并完成。")
        else:
            merged_df = guest_df
            print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

        df = pd.DataFrame(merged_df)

        column_names = df.columns
        print(column_names)

        print("\n\n--- 将ID 3699 的查询结果存入变量并打印 ---")
        result_variable = get_query_result_as_string(merged_df, 3699)
        print("单个查询结果已成功存入变量 'result_variable'。打印如下：\n")
        print(result_variable)

        stats_result_1 = get_guest_statistics(
            merged_df, status='实际当前在住'
        )
        print_stats_results("示例：所有在住客人统计", stats_result_1)

        stats_result_2 = get_guest_statistics(
            merged_df, gender='女', status='实际当前在住'
        )
        print_stats_results("", stats_result_2)

        details_string_result = get_filtered_details_as_string(
            merged_df,
            status='实际当前在住',
            remark_keyword='宠物'
        )

        print(details_string_result)

    else:
        print("主数据未能成功加载，程序即将退出。")