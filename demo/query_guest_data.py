import pandas as pd
import os
from lxml import etree
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union

# --- 配置 ---
XML_FILE_PATH = 'master_guest.xml'
XML_STATUS_RENT_PATH = 'master_base.xml'

RMTYPE_MAPPING = {
    '1BD': "一房豪华式公寓",
    '1BP': "一房行政豪华式公寓",
    '2BD': "两房行政公寓",
    '3BR': "三房公寓",
    'STD': "豪华单间公寓",
    'STE': "行政单间公寓",
    'STP': "豪华行政单间"
}


# 在精确查询中重点显示的字段 (将 rmtype 替换为 rmtype_name)
IMPORTANT_FIELDS = [
    'id', 'profile_id', 'name', 'sex_like', 'birth', 'language',
    'mobile', 'email', 'nation', 'country', 'state', 'street',
    'id_code', 'id_no', 'hotel_id', 'profile_type', 'times_in', 'remark_y',
    'create_user', 'create_datetime', 'modify_user', 'modify_datetime',
    'sta', 'rmno', 'rmtype_name', 'full_rate_long', 'arr', 'dep'
]
# 字段名的中文映射 (将 rmtype 替换为 rmtype_name)
FIELD_NAME_MAPPING = {
    'id': '主键ID', 'profile_id': '客户档案ID', 'name': '姓名',
    'sex_like': '推断性别', 'birth': '出生日期', 'language': '语言代码',
    'mobile': '手机', 'email': '电子邮件', 'nation': '国籍代码',
    'country': '国家代码', 'state': '省份/州代码', 'street': '街道地址',
    'id_code': '证件类型代码', 'id_no': '证件号码', 'hotel_id': '酒店ID',
    'profile_type': '客户档案类型', 'times_in': '入住次数', 'remark_y': '备注',
    'create_user': '创建用户', 'create_datetime': '创建时间',
    'modify_user': '修改用户', 'modify_datetime': '修改时间',
    'sta': '在住状态', 'rmno': '房间号', 'full_rate_long': '月租金', 'arr': '到达日期', 'dep': '离开日期',
    'rmtype_name': '房间类型' # 更新为新的字段名和对应的中文
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
        # 确保返回的列包含原始的 rmtype
        return df[['id', 'sta', 'full_rate_long', 'dep', 'arr', 'rmno', 'remark', 'rmtype']]
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
                         end_arr_date: Optional[Any] = None, room_type: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
    """
    根据多种筛选条件对客户数据进行统计分析。
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
                        print("警告：缺少 'dep' 列，无法准确筛选在住客人。")
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
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() >= start_date_dt.normalize()]
                except Exception as e:
                    print(f"警告：无法解析开始日期 '{start_arr_date}'，该条件已忽略。错误: {e}")

            if end_arr_date:
                try:
                    end_date_dt = pd.to_datetime(end_arr_date)
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() <= end_date_dt.normalize()]
                except Exception as e:
                    print(f"警告：无法解析结束日期 '{end_arr_date}'，该条件已忽略。错误: {e}")
        else:
            print("警告：数据中不存在 'arr' 列，无法按入住时间筛选。")

    if 'birth' in filtered_df.columns:
        birth_dates = pd.to_datetime(filtered_df['birth'], errors='coerce')
        temp_age = (pd.to_datetime('today') - birth_dates).dt.days / 365.25
        filtered_df['age'] = temp_age

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

    # 按房间类型筛选
    if room_type:
        if 'rmtype_name' not in filtered_df.columns:
            print("警告：数据中不存在 'rmtype_name' 列，无法按房间类型筛选。")
        else:
            # 如果 room_type 是一个列表 (e.g., ["一房豪华式公寓", "两房行政公寓"])，则使用 .isin()
            if isinstance(room_type, list):
                filtered_df = filtered_df[filtered_df['rmtype_name'].isin(room_type)]
            # 如果是单个字符串，则直接精确匹配
            elif isinstance(room_type, str):
                filtered_df = filtered_df[filtered_df['rmtype_name'] == room_type]

    if min_rent is not None or max_rent is not None:
        if 'full_rate_long' in filtered_df.columns:
            filtered_df['full_rate_long'] = pd.to_numeric(filtered_df['full_rate_long'], errors='coerce')
            filtered_df.dropna(subset=['full_rate_long'], inplace=True)
            if min_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] >= min_rent]
            if max_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] <= max_rent]
        else:
            print(f"警告：数据中不存在 'full_rate_long' 列，租金筛选已忽略。")

    overall_total_rent = 0
    if 'full_rate_long' in filtered_df.columns:
        rent_data_overall = pd.to_numeric(filtered_df['full_rate_long'], errors='coerce').dropna()
        if not rent_data_overall.empty:
            overall_total_rent = rent_data_overall.sum()

    if gender:
        gender_map_internal = {'男': '>', '女': '?'}
        internal_gender_code = gender_map_internal.get(gender)
        if internal_gender_code and 'sex_like' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['sex_like'] == internal_gender_code]
        else:
            print(f"警告：无效的性别输入 '{gender}' 或缺少 'sex_like' 列，该筛选条件已忽略。")

    record_count = len(filtered_df)
    if record_count == 0: return {"count": 0, "analysis": None}

    age_dist, nat_dist, gen_dist, room_type_dist = [], [], [], []

    if 'age' in filtered_df.columns:
        age_data = filtered_df['age'].dropna().astype(int)
        unknown_age_count = record_count - len(age_data)
        if not age_data.empty:
            bins, labels = [0, 18, 30, 45, 60, 150], ['18岁以下', '18-30岁', '31-45岁', '46-60岁', '60岁以上']
            age_groups = pd.cut(age_data, bins=bins, labels=labels, right=False)
            age_counts = age_groups.value_counts().sort_index()
            for group, count in age_counts.items():
                age_dist.append(
                    {"group": group, "count": int(count), "percentage": f"{(count / record_count) * 100:.2f}%"})
        if unknown_age_count > 0:
            age_dist.append(
                {"group": "年龄未知", "count": int(unknown_age_count),
                 "percentage": f"{(unknown_age_count / record_count) * 100:.2f}%"})

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

    # --- 房间类型 (rmtype_name) 统计 ---
    if 'rmtype_name' in filtered_df.columns:
        room_type_counts = filtered_df['rmtype_name'].value_counts()
        for room_type_name, count in room_type_counts.items():
            room_type_dist.append({
                "room_type": room_type_name,
                "count": int(count),
                "percentage": f"{(count / record_count) * 100:.2f}%"
            })
    else:
        print("警告：数据中不存在 'rmtype_name' 列，无法进行房间类型统计。")

    rent_analysis = None
    if 'full_rate_long' in filtered_df.columns and 'rmno' in filtered_df.columns:
        rent_df = filtered_df[['rmno', 'full_rate_long']].copy()
        rent_df['full_rate_long'] = pd.to_numeric(rent_df['full_rate_long'], errors='coerce')
        rent_df.dropna(subset=['full_rate_long', 'rmno'], inplace=True)
        room_counts = rent_df.groupby('rmno')['rmno'].transform('size')
        keep_positive_rent = rent_df['full_rate_long'] > 0
        keep_special_zero_rent = (rent_df['full_rate_long'] == 0) & (room_counts == 1)
        final_rent_df = rent_df[keep_positive_rent | keep_special_zero_rent]
        rent_data = final_rent_df['full_rate_long']

        if not rent_data.empty:
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

    summary_stats = {}
    if 'age' in filtered_df.columns:
        valid_ages = filtered_df['age'].dropna()
        if not valid_ages.empty:
            summary_stats['average_age'] = f"{valid_ages.mean():.1f} 岁"
    if 'times_in' in filtered_df.columns:
        times_in_numeric = pd.to_numeric(filtered_df['times_in'], errors='coerce').dropna()
        if not times_in_numeric.empty:
            summary_stats['average_times_in'] = f"{times_in_numeric.mean():.1f} 次"
    if 'arr' in filtered_df.columns and 'dep' in filtered_df.columns:
        arr_dates = pd.to_datetime(filtered_df['arr'], errors='coerce')
        dep_dates = pd.to_datetime(filtered_df['dep'], errors='coerce')
        valid_durations = (dep_dates - arr_dates).dt.days.dropna()
        if not valid_durations.empty:
            summary_stats['average_stay_duration'] = f"{valid_durations.mean():.1f} 天"

    return {"count": record_count,
            "analysis": {"based_on": f"基于 {record_count} 条符合条件的入住记录的分析",
                         "summary_statistics": summary_stats,
                         "age_distribution": age_dist,
                         "nationality_distribution": nat_dist,
                         "gender_distribution": gen_dist,
                         "room_type_distribution": room_type_dist,
                         "rent_analysis": rent_analysis}}

def get_filtered_guest_details(df: pd.DataFrame, name: Optional[str] = None, room_number: Optional[str] = None,
                               status: Union[str, List[str]] = None, nation: Optional[str] = None, min_age: Optional[int] = None,
                               max_age: Optional[int] = None, min_rent: Optional[float] = None,
                               max_rent: Optional[float] = None, remark_keyword: Optional[str] = None,
                               gender: Optional[str] = None, start_arr_date: Optional[Any] = None,
                               end_arr_date: Optional[Any] = None, room_type: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
    """
    根据多种筛选条件获取住客的详细信息。
    """
    filtered_df = df.copy()

    def apply_filter(column, value, exact=False):
        nonlocal filtered_df
        if column not in filtered_df.columns: return
        if pd.isna(value): return
        filtered_df.dropna(subset=[column], inplace=True)
        if exact:
            filtered_df = filtered_df[filtered_df[column] == value]
        else:
            filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(value, case=False, na=False)]

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
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() >= start_date_dt.normalize()]
                except Exception: pass
            if end_arr_date:
                try:
                    end_date_dt = pd.to_datetime(end_arr_date)
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() <= end_date_dt.normalize()]
                except Exception: pass
    if room_type:
        if 'rmtype_name' in filtered_df.columns:
            if isinstance(room_type, list):
                filtered_df = filtered_df[filtered_df['rmtype_name'].isin(room_type)]
            elif isinstance(room_type, str):
                filtered_df = filtered_df[filtered_df['rmtype_name'] == room_type]
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
                                   end_arr_date: Optional[Any] = None, room_type: Optional[Union[str, List[str]]] = None) -> str:
    """
    根据多种筛选条件查询住客信息，并将所有结果整合成一个格式化的字符串。
    """
    filtered_guests_df = get_filtered_guest_details(df, name=name, room_number=room_number,
                                                    status=status, nation=nation, min_age=min_age,
                                                    max_age=max_age, min_rent=min_rent,
                                                    max_rent=max_rent, remark_keyword=remark_keyword,
                                                    gender=gender, start_arr_date=start_arr_date,
                                                    end_arr_date=end_arr_date, room_type=room_type)
    if filtered_guests_df.empty:
        return f"--- 未找到符合条件的住客记录 ---"

    all_results = []
    separator = "\n" + "=" * 50 + "\n"
    for guest_id in filtered_guests_df['id']:
        all_results.append(get_query_result_as_string(df, guest_id))

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

        if analysis.get('summary_statistics'):
            summary = analysis['summary_statistics']
            if summary:
                print("\n核心平均值:")
                if 'average_age' in summary: print(f"  - 平均年龄: {summary['average_age']}")
                if 'average_times_in' in summary: print(f"  - 平均入住次数: {summary['average_times_in']}")
                if 'average_stay_duration' in summary: print(f"  - 平均居住天数: {summary['average_stay_duration']}")

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

        if analysis.get('room_type_distribution'):
            print("\n房间类型分布:")
            for item in analysis['room_type_distribution']: print(
                f"  - {item['room_type']:<20}: {item['count']}间 ({item['percentage']})")

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
            guest_df['id'] = pd.to_numeric(guest_df['id'], errors='coerce').astype('Int64')
            status_rent_df['id'] = pd.to_numeric(status_rent_df['id'], errors='coerce').astype('Int64')
            print(f"\n正在合并数据...")
            merged_df = pd.merge(guest_df.dropna(subset=['id']), status_rent_df.dropna(subset=['id']), on='id', how='left')
            print("数据合并完成。")
        else:
            merged_df = guest_df
            print("\n未加载状态/租金数据，将仅使用主数据进行操作。")

        df = pd.DataFrame(merged_df)

        # 应用房间类型映射
        if 'rmtype' in df.columns:
            print("正在将房间类型代码映射到中文名称...")
            # 使用 .map() 应用字典映射。对于不在字典中的 rmtype，使用 .fillna() 保留其原始值。
            df['rmtype_name'] = df['rmtype'].map(RMTYPE_MAPPING).fillna(df['rmtype'])
            print("映射完成。")

        print("\n\n--- 将ID 3699 的查询结果存入变量并打印 ---")
        result_variable = get_query_result_as_string(merged_df, 3699)
        print("单个查询结果已成功存入变量 'result_variable'。打印如下：\n")
        print(result_variable)

        stats_result_1 = get_guest_statistics(
            df, status='实际当前在住' ,room_type= '行政单间公寓'
        )
        print_stats_results("示例：所有在住客人统计 (使用中文房间类型)", stats_result_1)

        stats_result_2 = get_guest_statistics(
            df, gender='女', status=['I', 'R', 'X'] ,room_type= '行政单间公寓'
        )
        #print(stats_result_2)
        print_stats_results("示例：所有在住、预离和已结账的女性客人统计", stats_result_2)

        details_string_result = get_filtered_details_as_string(
            df,
            status='实际当前在住',
            remark_keyword='宠物',
            nation = 'usa',
            room_type= '行政单间公寓'
        )
        print("\n--- 30岁及以下的在住客人详细列表 ---")
        print(details_string_result)

    else:
        print("主数据未能成功加载，程序即将退出。")