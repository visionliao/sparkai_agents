import pandas as pd
import os
from lxml import etree
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union

# --- 配置 ---
XML_FILE_PATH = 'master_guest.xml'
XML_STATUS_RENT_PATH = 'master_base.xml'

RMTYPE_MAPPING = {
    '1BD': "One Bedroom Deluxe",
    '1BP': "One Bedroom Premier",
    '2BD': "Two Bedrooms Executive",
    '3BR': "Three-bedroom",
    'STD': "Studio Deluxe",
    'STE': "Studio Executive",
    'STP': "Studio Premier"
}

# 在精确查询中重点显示的字段
IMPORTANT_FIELDS = [
    'id', 'profile_id', 'name', 'sex_like', 'birth', 'language',
    'mobile', 'email', 'nation', 'country', 'state', 'street',
    'id_code', 'id_no', 'hotel_id', 'profile_type', 'times_in', 'remark_y',
    'create_user', 'create_datetime', 'modify_user', 'modify_datetime',
    'sta', 'rmno', 'rmtype_name', 'full_rate_long', 'arr', 'dep'
]
# 字段名的中文映射
FIELD_NAME_MAPPING = {
    'id': 'Primary ID', 'profile_id': 'Customer Profile ID', 'name': 'Name',
    'sex_like': 'Inferred Gender', 'birth': 'Date of Birth', 'language': 'Language Code',
    'mobile': 'Mobile', 'email': 'Email', 'nation': 'Nationality Code',
    'country': 'Country Code', 'state': 'Province/State Code', 'street': 'Street Address',
    'id_code': 'ID Type Code', 'id_no': 'ID Number', 'hotel_id': 'Hotel ID',
    'profile_type': 'Customer Profile Type', 'times_in': 'Number of Stays', 'remark_y': 'Remark',
    'create_user': 'Created By', 'create_datetime': 'Creation Time',
    'modify_user': 'Modified By', 'modify_datetime': 'Modification Time',
    'sta': 'Stay Status', 'rmno': 'Room Number', 'full_rate_long': 'Monthly Rent', 'arr': 'Arrival Date', 'dep': 'Departure Date',
    'rmtype_name': 'room_type'
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
        print(f"Error: File '{file_path}' does not exist.") # 翻译
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

        print(f"Successfully loaded and processed {len(df)} master records from '{file_path}'.") # 翻译
        return df
    except Exception as e:
        print(f"Error loading or processing '{file_path}': {e}") # 翻译
        return None


def load_status_rent_data_from_xml(file_path: str) -> pd.DataFrame:
    """从XML文件加载客户的状态和租金信息"""
    if not os.path.exists(file_path):
        print(f"Info: Status/rent file '{file_path}' does not exist, skipping load.") # 翻译
        return None
    try:
        tree = etree.parse(file_path)
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = tree.xpath('.//ss:Row', namespaces=ns)
        if not rows: return None

        header = [cell.text for cell in rows[0].xpath('.//ss:Data', namespaces=ns)]
        if 'id' not in header:
            print(f"Error: Missing key merge column 'id' in '{file_path}'.") # 翻译
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

        print(f"Successfully loaded {len(df)} status/rent records from '{file_path}'.") # 翻译
        return df[['id', 'sta', 'full_rate_long', 'dep', 'arr', 'rmno', 'remark', 'rmtype']]
    except Exception as e:
        print(f"Error loading or processing '{file_path}': {e}") # 翻译
        return None


def get_query_result_as_string(df: pd.DataFrame, query_id: int) -> str:
    """根据单个ID查询并格式化输出客户的核心数据"""
    result = df[df['id'] == query_id]
    if result.empty: return f"--- Record with ID {query_id} not found ---" # 翻译
    record = result.iloc[0]
    output_lines = [f"--- Core data for ID: {query_id} ---"] # 翻译
    max_label_width = 15
    for field in IMPORTANT_FIELDS:
        if field in record:
            display_name = FIELD_NAME_MAPPING.get(field, field)
            value = record[field]
            display_value = value if pd.notna(value) and str(value).strip() != '' else "[Empty]" # 翻译
            if field == 'sex_like': display_value = {">": "Male", "?": "Female"}.get(display_value, display_value) # 翻译
            padding_spaces = " " * (max_label_width - get_display_width(display_name))
            output_lines.append(f"{display_name}{padding_spaces}: {display_value}")
        else:
            output_lines.append(f"{FIELD_NAME_MAPPING.get(field, field)}: [Field not found]") # 翻译
    output_lines.append("----------------------------")
    return "\n".join(output_lines)


def get_multiple_query_results_as_string(df: pd.DataFrame, query_ids_str: str) -> str:
    """支持用逗号分隔的字符串查询多个ID"""
    all_results = []
    invalid_ids = []
    separator = "\n\n" + "=" * 60 + "\n\n"
    raw_ids = [id_str.strip() for id_str in query_ids_str.split(',') if id_str.strip()]
    if not raw_ids: return "Input is empty or does not contain valid IDs." # 翻译
    for id_part in raw_ids:
        try:
            q_id = int(id_part)
            all_results.append(get_query_result_as_string(df, q_id))
        except ValueError:
            invalid_ids.append(id_part)
    output_str = separator.join(all_results) if all_results else "No valid records found." # 翻译
    if invalid_ids:
        output_str += f"\n\n--- Note: The following IDs are invalid or could not be parsed and were skipped: {', '.join(invalid_ids)} ---" # 翻译
    return output_str


def get_guest_statistics(df: pd.DataFrame, name: Optional[str] = None, room_number: Optional[str] = None,
                         status: Union[str, List[str]] = None, nation: Optional[str] = None, min_age: Optional[int] = None,
                         max_age: Optional[int] = None, min_rent: Optional[float] = None,
                         max_rent: Optional[float] = None, remark_keyword: Optional[str] = None,
                         gender: Optional[str] = None, start_arr_date: Optional[Any] = None, room_type: Optional[Union[str, List[str]]] = None,
                         end_arr_date: Optional[Any] = None) -> Dict[str, Any]:
    filtered_df = df.copy()

    def apply_filter(column, value, exact=False):
        nonlocal filtered_df
        if column not in filtered_df.columns:
            print(f"Warning: Column '{column}' does not exist in data; related filter condition ignored.") # 翻译
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
            print("Warning: 'sta' column does not exist in data, cannot filter by status.") # 翻译
        else:
            # 如果 status 是一个列表 (e.g., ['O', 'R'])，则使用 .isin() 进行多选
            if isinstance(status, list):
                filtered_df = filtered_df[filtered_df['sta'].isin(status)]
            # 如果 status 仍然是单个字符串，则保持原有的逻辑
            elif isinstance(status, str):
                if status == 'Currently residing on-site':  # 'I' (在住) 有特殊的日期检查逻辑 # 翻译
                    if 'dep' in filtered_df.columns:
                        filtered_df = filtered_df[filtered_df['sta'] == 'I'].copy()
                        dep_dates = pd.to_datetime(filtered_df['dep'], errors='coerce')
                        today = pd.to_datetime('today').normalize()
                        filtered_df = filtered_df[dep_dates > today]
                    else:
                        print("Warning: Missing 'dep' column, cannot accurately filter current residents.") # 翻译
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
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() >= start_date_dt.normalize()]
                except Exception as e:
                    print(f"Warning: Could not parse start date '{start_arr_date}', condition ignored. Error: {e}") # 翻译

            if end_arr_date:
                try:
                    end_date_dt = pd.to_datetime(end_arr_date)
                    filtered_df = filtered_df[filtered_df['arr'].dt.normalize() <= end_date_dt.normalize()]
                except Exception as e:
                    print(f"Warning: Could not parse end date '{end_arr_date}', condition ignored. Error: {e}") # 翻译
        else:
            print("Warning: 'arr' column does not exist in data, cannot filter by arrival date.") # 翻译

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
            print("Warning: 'birth' column does not exist or could not be parsed, cannot filter by minimum age.") # 翻译

    if max_age is not None:
        if 'age' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['age'] <= max_age]
        else:
            print("Warning: 'birth' column does not exist or could not be parsed, cannot filter by maximum age.") # 翻译

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

    # 租金筛选逻辑 (保持不变)
    if min_rent is not None or max_rent is not None:
        if 'full_rate_long' in filtered_df.columns:
            filtered_df['full_rate_long'] = pd.to_numeric(filtered_df['full_rate_long'], errors='coerce')
            filtered_df.dropna(subset=['full_rate_long'], inplace=True)
            if min_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] >= min_rent]
            if max_rent is not None: filtered_df = filtered_df[filtered_df['full_rate_long'] <= max_rent]
        else:
            print(f"Warning: 'full_rate_long' column does not exist in data, rent filter ignored.") # 翻译

    # 总租金计算 (保持不变)
    overall_total_rent = 0
    if 'full_rate_long' in filtered_df.columns:
        rent_data_overall = pd.to_numeric(filtered_df['full_rate_long'], errors='coerce').dropna()
        if not rent_data_overall.empty:
            overall_total_rent = rent_data_overall.sum()

    # 性别筛选 (保持不变)
    if gender:
        gender_map_internal = {'Male': '>', 'Female': '?'} # 翻译
        internal_gender_code = gender_map_internal.get(gender)
        if internal_gender_code and 'sex_like' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['sex_like'] == internal_gender_code]
        else:
            print(f"Warning: Invalid gender input '{gender}' or missing 'sex_like' column, condition ignored.") # 翻译

    # 最终记录数
    record_count = len(filtered_df)
    if record_count == 0: return {"count": 0, "analysis": None}

    age_dist, nat_dist, gen_dist, room_type_dist = [], [], [], []

    # --- 【新年龄分布统计】 ---
    if 'age' in filtered_df.columns:
        # 1. 筛选出年龄有效的记录
        age_data = filtered_df['age'].dropna().astype(int)

        # 2. 计算年龄无效的记录数
        unknown_age_count = record_count - len(age_data)

        # 3. 对有效年龄进行分段统计
        if not age_data.empty:
            bins, labels = [0, 18, 30, 45, 60, 150], ['Under 18', '18-30', '31-45', '46-60', 'Over 60'] # 翻译
            age_groups = pd.cut(age_data, bins=bins, labels=labels, right=False)
            age_counts = age_groups.value_counts().sort_index()
            for group, count in age_counts.items():
                age_dist.append(
                    {"group": group, "count": int(count), "percentage": f"{(count / record_count) * 100:.2f}%"})

        # 4. 如果存在未知年龄的记录，将其作为一个单独的类别添加
        if unknown_age_count > 0:
            age_dist.append(
                {"group": "Unknown Age", "count": int(unknown_age_count), # 翻译
                 "percentage": f"{(unknown_age_count / record_count) * 100:.2f}%"})

    # 国籍和性别分布 (保持不变, 分母为 record_count)
    if 'nation' in filtered_df.columns:
        nation_counts = filtered_df['nation'].value_counts()
        top_nations = nation_counts.nlargest(9)
        for nation, count in top_nations.items():
            nat_dist.append({"nation": nation if nation else "Unknown", "count": int(count), # 翻译
                             "percentage": f"{(count / record_count) * 100:.2f}%"})
        if len(nation_counts) > 9:
            other_count = nation_counts.iloc[9:].sum()
            nat_dist.append({"nation": "Other", "count": int(other_count), # 翻译
                             "percentage": f"{(other_count / record_count) * 100:.2f}%"})

    if 'sex_like' in filtered_df.columns:
        gender_map = {'>': 'Male', '?': 'Female'} # 翻译
        gender_counts = filtered_df['sex_like'].map(gender_map).fillna('Unknown').value_counts() # 翻译
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

    # 租金分析
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
            # (租金分析的其余部分代码与之前版本相同, 为简洁省略)
            based_on_rent_count = len(rent_data)
            rent_dist = []
            bins = [-float('inf'), 3000, 5000, 7000, 10000, float('inf')]
            labels = ['Below 3000', '3000-5000', '5001-7000', '7001-10000', 'Above 10000'] # 翻译
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
                gender_map = {'>': 'Male', '?': 'Female'} # 翻译
                gender_counts_in_rent = guests_with_rent_df['sex_like'].map(gender_map).fillna('Unknown').value_counts() # 翻译
                for gender_val, count in gender_counts_in_rent.items():
                    gender_rent_dist.append({"gender": gender_val, "count": int(count),
                                             "percentage": f"{(count / based_on_rent_count) * 100:.2f}%"})
            gender_rent_contribution = []
            if overall_total_rent > 0 and 'sex_like' in guests_with_rent_df.columns:
                gender_map = {'>': 'Male', '?': 'Female'} # 翻译
                rent_sum_by_gender = guests_with_rent_df.groupby('sex_like')['full_rate_long'].sum()
                for gender_code, rent_sum in rent_sum_by_gender.items():
                    gender_name = gender_map.get(gender_code, 'Unknown') # 翻译
                    percentage = (rent_sum / overall_total_rent) * 100
                    gender_rent_contribution.append(
                        {"gender": gender_name, "total_rent": f"{rent_sum:.2f}", "percentage": f"{percentage:.2f}%"})
            rent_analysis = {"average_rent": f"{rent_data.mean():.2f}", "median_rent": f"{rent_data.median():.2f}",
                             "min_rent": f"{rent_data.min():.2f}", "max_rent": f"{rent_data.max():.2f}",
                             "based_on_count": based_on_rent_count, "distribution": rent_dist,
                             "gender_breakdown": gender_rent_dist,
                             "gender_contribution_to_total_rent": gender_rent_contribution}
    else:
        print("Warning: Rent analysis requires both 'full_rate_long' and 'rmno' columns.")

    # --- 计算各项平均值 ---
    summary_stats = {}
    # 1. 平均年龄
    if 'age' in filtered_df.columns:
        valid_ages = filtered_df['age'].dropna()
        if not valid_ages.empty:
            summary_stats['average_age'] = f"{valid_ages.mean():.1f} years" # 翻译

    # 2. 平均入住次数
    if 'times_in' in filtered_df.columns:
        times_in_numeric = pd.to_numeric(filtered_df['times_in'], errors='coerce').dropna()
        if not times_in_numeric.empty:
            summary_stats['average_times_in'] = f"{times_in_numeric.mean():.1f} times" # 翻译

    # 3. 平均居住天数
    if 'arr' in filtered_df.columns and 'dep' in filtered_df.columns:
        # 确保 arr 和 dep 是日期时间格式，忽略无法转换的错误
        arr_dates = pd.to_datetime(filtered_df['arr'], errors='coerce')
        dep_dates = pd.to_datetime(filtered_df['dep'], errors='coerce')

        # 计算有效的居住天数（即 arr 和 dep 都有效）
        valid_durations = (dep_dates - arr_dates).dt.days.dropna()
        if not valid_durations.empty:
            summary_stats['average_stay_duration'] = f"{valid_durations.mean():.1f} days" # 翻译


    return {"count": record_count,
            "analysis": {"based_on": f"Analysis based on {record_count} matching stay records", # 翻译
                         "summary_statistics": summary_stats,  ### 新增：将平均值字典加入返回结果
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
                if status == 'Currently residing on-site': # 翻译
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
        gender_map_internal = {'Male': '>', 'Female': '?'} # 翻译
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

    :return: 一个包含所有符合条件住客详细信息的、格式化好的单一字符串。
    """
    # 步骤 1: 复用筛选函数，获取符合条件的住客DataFrame
    filtered_guests_df = get_filtered_guest_details(df, name=name, room_number=room_number,
                                                    status=status, nation=nation, min_age=min_age,
                                                    max_age=max_age, min_rent=min_rent,
                                                    max_rent=max_rent, remark_keyword=remark_keyword,
                                                    gender=gender, start_arr_date=start_arr_date,
                                                    end_arr_date=end_arr_date, room_type=room_type)

    # 步骤 2: 处理查询结果
    if filtered_guests_df.empty:
        return f"--- No guest records found matching the criteria ---" # 翻译

    all_results = []
    # 定义一个清晰的分隔符，用于区分不同的客人信息
    separator = "\n" + "=" * 50 + "\n"

    # 步骤 3: 遍历结果，并复用格式化函数生成每个客人的信息字符串
    for guest_id in filtered_guests_df['id']:
        # 注意：这里我们向格式化函数传入原始的 df，以确保能找到所有字段
        all_results.append(get_query_result_as_string(df, guest_id))

    # 步骤 4: 将所有客人的信息字符串用分隔符连接成一个最终的大字符串
    # 同时在开头和结尾添加总数统计
    header = f"--- {len(all_results)} records found matching the criteria ---" # 翻译
    footer = f"--- Query finished ---" # 翻译

    return header + separator + separator.join(all_results) + separator + footer

def print_stats_results(title: str, stats_result: Dict):
    """一个辅助函数，用于格式化并美观地打印统计结果"""
    print("\n" + "=" * 20 + f" {title} " + "=" * 20)
    print(f"\nTotal records found: {stats_result['count']}") # 翻译
    if stats_result.get('analysis'):
        analysis = stats_result['analysis']
        print(f"Statistical Summary: {analysis['based_on']}") # 翻译

        # --- 打印核心平均值 ---
        if analysis.get('summary_statistics'):
            summary = analysis['summary_statistics']
            if summary:  # 确保字典不为空
                print("\nCore Averages:") # 翻译
                if 'average_age' in summary:
                    print(f"  - Average Age: {summary['average_age']}") # 翻译
                if 'average_times_in' in summary:
                    print(f"  - Average Number of Stays: {summary['average_times_in']}") # 翻译
                if 'average_stay_duration' in summary:
                    print(f"  - Average Stay Duration: {summary['average_stay_duration']}") # 翻译

        if analysis.get('age_distribution'):
            print("\nAge Distribution:") # 翻译
            for item in analysis['age_distribution']: print(
                f"  - {item['group']:<10}: {item['count']} people ({item['percentage']})") # 翻译

        if analysis.get('nationality_distribution'):
            print("\nNationality Distribution:") # 翻译
            for item in analysis['nationality_distribution']: print(
                f"  - {item['nation']:<10}: {item['count']} people ({item['percentage']})") # 翻译

        if analysis.get('gender_distribution'):
            print("\nGender Distribution:") # 翻译
            for item in analysis['gender_distribution']: print(
                f"  - {item['gender']:<10}: {item['count']} people ({item['percentage']})") # 翻译

        if analysis.get('room_type_distribution'):
            print("\n房间类型分布:")
            for item in analysis['room_type_distribution']: print(
                f"  - {item['room_type']:<20}: {item['count']}间 ({item['percentage']})")

        if analysis.get('rent_analysis'):
            rent_info = analysis['rent_analysis']
            print(f"\nRent Analysis (based on {rent_info['based_on_count']} guests with rent records):") # 翻译
            print(f"  - Average Rent: {rent_info['average_rent']} /month") # 翻译
            print(f"  - Median Rent: {rent_info['median_rent']} /month") # 翻译
            print(f"  - Rent Range: {rent_info['min_rent']} - {rent_info['max_rent']} /month") # 翻译
            if rent_info.get('distribution'):
                print("  - Rent Segmentation:") # 翻译
                for item in rent_info['distribution']: print(
                    f"    - {item['range']:<12}: {item['count']} people ({item['percentage']})") # 翻译

            if rent_info.get('gender_breakdown'):
                print("  - Gender Breakdown of Payers:") # 翻译
                for item in rent_info['gender_breakdown']:
                    print(f"    - {item['gender']:<12}: {item['count']} people ({item['percentage']})") # 翻译

            if rent_info.get('gender_contribution_to_total_rent'):
                print("  - Gender Contribution to Total Rent:") # 翻译
                for item in rent_info['gender_contribution_to_total_rent']:
                    print(f"    - {item['gender']:<12}: Total Contribution {item['total_rent']} ({item['percentage']})") # 翻译

    else:
        print("No eligible guests found for analysis.") # 翻译
    print("=" * (42 + len(title)))


if __name__ == "__main__":
    guest_df = load_data_from_xml(XML_FILE_PATH)

    if guest_df is not None:
        status_rent_df = load_status_rent_data_from_xml(XML_STATUS_RENT_PATH)

        if status_rent_df is not None:
            guest_df['id'] = pd.to_numeric(guest_df['id'], errors='coerce')
            status_rent_df['id'] = pd.to_numeric(status_rent_df['id'], errors='coerce')

            print(f"\nMerging data...") # 翻译
            merged_df = pd.merge(guest_df, status_rent_df, on='id', how='left')
            print("Data merge complete.") # 翻译
        else:
            merged_df = guest_df
            print("\nStatus/rent data not loaded; operations will proceed with master data only.") # 翻译

        df = pd.DataFrame(merged_df)

        column_names = df.columns
        print(column_names)

        print("\n\n--- Storing and printing query result for ID 3699 ---") # 翻译
        result_variable = get_query_result_as_string(merged_df, 3699)
        print("Single query result successfully stored in variable 'result_variable'. Printing below:\n") # 翻译
        print(result_variable)

        stats_result_1 = get_guest_statistics(
            merged_df, status='Currently residing on-site' # Keep the Chinese filter value, as it's an internal code
        )
        print_stats_results("Example: Statistics for all current residents", stats_result_1) # 翻译

        stats_result_2 = get_guest_statistics(
            merged_df, gender='Female', status='Currently residing on-site' # Keep Chinese filter values
        )
        print_stats_results("Example: Statistics for all female current residents", stats_result_2) # 翻译

        details_string_result = get_filtered_details_as_string(
            merged_df,
            status='Currently residing on-site',
            remark_keyword='宠物'
        )

        print(details_string_result)

    else:
        print("Master data failed to load, program will exit.") # 翻译