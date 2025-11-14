import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
import json


class ApartmentQueryTool:
    ESSENTIAL_COLUMNS = [
        'Room_number', 'Building_code', 'Floor', 'Room_type', 'Area (square meters)',
        'Orientation', '12 months rent', '6-11 months rent', '2-5 months rent', '1 month rent'
    ]

    def __init__(self, filepath: str):
        self.df = self._load_and_validate_data(filepath)
        if not self.df.empty:
            self._preprocess_data()

        self.lease_columns = {
            '12 months and above': '12 months rent', '6-11 months': '6-11 months rent',
            '2-5 months': '2-5 months rent', '1 month': '1 month rent'
        }

    def _load_and_validate_data(self, filepath: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(filepath)
            # 验证所有必需的列是否存在
            if not all(col in df.columns for col in self.ESSENTIAL_COLUMNS):
                print(f"错误: CSV文件 '{filepath}' 缺少必需的列。")
                missing = [col for col in self.ESSENTIAL_COLUMNS if col not in df.columns]
                print(f"缺少的列: {missing}")
                return pd.DataFrame()
            return df
        except FileNotFoundError:
            print(f"错误: 文件未找到 '{filepath}'")
            return pd.DataFrame()
        except Exception as e:
            print(f"加载或解析文件 '{filepath}' 时出错: {e}")
            return pd.DataFrame()

    def _preprocess_data(self):
        """数据预处理，包括类型转换和性能优化。"""
        self.df['Floor_val'] = self.df['Floor'].str.replace('F', '', regex=False).astype(int)

        numeric_cols = [col for col in self.ESSENTIAL_COLUMNS if 'rent' in col or 'area' in col]
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # 优化: 将低基数列转换为 category 类型以节省内存并提高性能
        categorical_cols = ['Building_code', 'Orientation', 'Room_type']
        for col in categorical_cols:
            self.df[col] = self.df[col].astype('category')

        self.df.dropna(subset=['Area (square meters)', '12 months rent'], inplace=True)

    def _validate_inputs(self, **kwargs) -> Optional[str]:
        """验证查询参数，如果无效则返回错误信息字符串。"""
        if 'floor_range' in kwargs and kwargs['floor_range'] and kwargs['floor_range'][0] > kwargs['floor_range'][1]:
            return "Invalid floor range: the minimum value cannot be greater than the maximum value."
        if 'area_range' in kwargs and kwargs['area_range'] and kwargs['area_range'][0] > kwargs['area_range'][1]:
            return "Invalid area range: the minimum value cannot be greater than the maximum value."
        if 'price_range' in kwargs and kwargs['price_range'] and kwargs['price_range'][0] > kwargs['price_range'][1]:
            return "Invalid price range: the minimum value cannot be greater than the maximum value."
        return None

    def query(self, **kwargs) -> Dict[str, Any]:
        if self.df.empty:
            return {"error": "Data not loaded, unable to execute query."}

        # 优化: 输入验证
        validation_error = self._validate_inputs(**kwargs)
        if validation_error:
            return {"error": validation_error}

        # 优化: 不再使用 .copy()，直接进行链式过滤
        filtered_df = self.df

        price_col = self.lease_columns.get(kwargs.get('lease_term', '12 months and above'), '12 months rent')

        # 精确查询
        if kwargs.get('room_number'):
            filtered_df = filtered_df[filtered_df['Room_number'] == kwargs['room_number']]
        else:
            if building := [b.strip().upper() for b in (kwargs.get('building') or []) if b and b.strip()]:
                filtered_df = filtered_df[filtered_df['Building_code'].str.upper().isin(building)]

            if orientation := [o.strip() for o in (kwargs.get('orientation') or []) if o and o.strip()]:
                facing = '|'.join(orientation)
                filtered_df = filtered_df[filtered_df['Orientation'].str.contains(facing, na=False, regex=True)]

            if room_type := [rt.strip() for rt in (kwargs.get('room_type') or []) if rt and rt.strip()]:
                pattern = '|'.join(room_type)
                filtered_df = filtered_df[filtered_df['Room_type'].str.contains(pattern, na=False, regex=True)]

            # 范围过滤
            if price_range := kwargs.get('price_range'):
                filtered_df = filtered_df[filtered_df[price_col].between(price_range[0], price_range[1])]
            if area_range := kwargs.get('area_range'):
                filtered_df = filtered_df[filtered_df['Area (square meters)'].between(area_range[0], area_range[1])]
            if floor_range := kwargs.get('floor_range'):
                filtered_df = filtered_df[filtered_df['Floor_val'].between(floor_range[0], floor_range[1])]

        # 聚合
        if kwargs.get('aggregation') == 'count':
            return {'count': len(filtered_df)}

        # 排序
        sort_by = kwargs.get('sort_by', 'price')
        sort_col_map = {'price': price_col, 'area': 'Area (square meters)', 'floor': 'Floor_val'}
        sort_col = sort_col_map.get(sort_by, price_col)
        sorted_df = filtered_df.sort_values(by=sort_col, ascending=(kwargs.get('sort_order', 'asc') == 'asc'))

        # 格式化输出
        limit = kwargs.get('limit', 10)
        return_fields = kwargs.get('return_fields')
        results_df = sorted_df.head(limit)
        apartments = []
        # 预先计算租期说明，避免在循环中重复生成
        lease_term_str = f"Based on {kwargs.get('lease_term', '12 months and above')} lease"

        for _, row in results_df.iterrows():
            # 创建一个包含所有【可返回】字段及其值的完整映射
            all_possible_fields = {
                'Room_number': row['Room_number'],
                'Building_code': row['Building_code'],
                'Floor': row['Floor'],
                'Room_type': row['Room_type'],
                'Area (square meters)': round(row['Area (square meters)'], 2),
                'Orientation': row['Orientation'],
                'Reference rent': f"{int(row[price_col])}RMB",
                'Rent Explanation': lease_term_str
            }

            # 如果用户没有指定返回字段，则返回全部默认字段
            if not return_fields:
                apartment_details = all_possible_fields
            # 否则，只从完整映射中挑选用户请求的字段
            else:
                apartment_details = {
                    field: all_possible_fields.get(field)
                    for field in return_fields
                    if field in all_possible_fields
                }

            apartments.append(apartment_details)
        return {"total_found": len(sorted_df), "displaying": len(apartments), "apartments": apartments}


# --- Usage Example ---
if __name__ == '__main__':
    FILE_PATH = "room_base_en.csv"
    tool = ApartmentQueryTool(filepath=FILE_PATH)

    if not tool.df.empty:
        print("✅ Tool initialized successfully, data loaded.")
        print("\n" + "=" * 70 + "\n")

        print("--- Test 1: Case-insensitive query ---")
        result = tool.query(building=['A'], room_type=['One Bedroom Deluxe'])
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + "=" * 70 + "\n")

        print("--- Test 2: Invalid input range ---")
        result = tool.query(price_range=(10000, 20000))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + "=" * 70 + "\n")

        print("--- Test 3: Empty list filter (room_type=[]) ---")
        result = tool.query(building=['B'], room_type=[])
        print(f"Querying all apartments in Building B, total found: {result['total_found']}")

        print("\n" + "=" * 70 + "\n")

        # Example Query 1
        print("--- Example 1: Query for the largest 'one bedroom' apartment in Building A, above 15th floor, south-facing, with annual rent under 25000 ---")
        result1 = tool.query(
            building=['A'],
            floor_range=(15, 100),
            orientation='South',

            price_range=(0, 25000),
            lease_term='12 months and above',
            sort_by='area',
            sort_order='desc',
            return_fields = ['Room_number', 'Area (square meters)', 'Reference rent', 'Orientation', 'Room_type']
        )
        print(json.dumps(result1, indent=2, ensure_ascii=False))