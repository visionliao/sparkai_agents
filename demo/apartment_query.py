import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
import json


class ApartmentQueryTool:
    """
    一个健壮且优化的公寓信息查询工具。
    它从CSV加载数据，并提供一个带有输入验证的结构化查询接口。
    """
    ESSENTIAL_COLUMNS = [
        '房号', '楼栋', '楼层', '房型', '面积(平方米)',
        '朝向', '12个月租金', '6-11个月租金', '2-5个月租金', '1个月租金'
    ]

    def __init__(self, filepath: str):
        self.df = self._load_and_validate_data(filepath)
        if not self.df.empty:
            self._preprocess_data()

        self.lease_columns = {
            '12个月及以上': '12个月租金', '6-11个月': '6-11个月租金',
            '2-5个月': '2-5个月租金', '1个月': '1个月租金'
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
        self.df['楼层_val'] = self.df['楼层'].str.replace('F', '', regex=False).astype(int)

        numeric_cols = [col for col in self.ESSENTIAL_COLUMNS if '租金' in col or '面积' in col]
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # 优化: 将低基数列转换为 category 类型以节省内存并提高性能
        categorical_cols = ['楼栋', '朝向', '房型']
        for col in categorical_cols:
            self.df[col] = self.df[col].astype('category')

        self.df.dropna(subset=['面积(平方米)', '12个月租金'], inplace=True)

    def _validate_inputs(self, **kwargs) -> Optional[str]:
        """验证查询参数，如果无效则返回错误信息字符串。"""
        if 'floor_range' in kwargs and kwargs['floor_range'] and kwargs['floor_range'][0] > kwargs['floor_range'][1]:
            return "楼层范围无效：最小值不能大于最大值。"
        if 'area_range' in kwargs and kwargs['area_range'] and kwargs['area_range'][0] > kwargs['area_range'][1]:
            return "面积范围无效：最小值不能大于最大值。"
        if 'price_range' in kwargs and kwargs['price_range'] and kwargs['price_range'][0] > kwargs['price_range'][1]:
            return "价格范围无效：最小值不能大于最大值。"
        return None

    def query(self, **kwargs) -> Dict[str, Any]:
        if self.df.empty:
            return {"error": "数据未加载，无法执行查询。"}

        # 优化: 输入验证
        validation_error = self._validate_inputs(**kwargs)
        if validation_error:
            return {"error": validation_error}

        # 优化: 不再使用 .copy()，直接进行链式过滤
        filtered_df = self.df

        price_col = self.lease_columns.get(kwargs.get('lease_term', '12个月及以上'), '12个月租金')

        # 精确查询
        if kwargs.get('room_number'):
            filtered_df = filtered_df[filtered_df['房号'] == kwargs['room_number']]
        else:
            if building := [b.strip().upper() for b in (kwargs.get('building') or []) if b and b.strip()]:
                filtered_df = filtered_df[filtered_df['楼栋'].str.upper().isin(building)]

            if orientation := [o.strip() for o in (kwargs.get('orientation') or []) if o and o.strip()]:
                facing = '|'.join(orientation)
                filtered_df = filtered_df[filtered_df['朝向'].str.contains(facing, na=False, regex=True)]

            if room_type := [rt.strip() for rt in (kwargs.get('room_type') or []) if rt and rt.strip()]:
                pattern = '|'.join(room_type)
                filtered_df = filtered_df[filtered_df['房型'].str.contains(pattern, na=False, regex=True)]

            # 范围过滤
            if price_range := kwargs.get('price_range'):
                filtered_df = filtered_df[filtered_df[price_col].between(price_range[0], price_range[1])]
            if area_range := kwargs.get('area_range'):
                filtered_df = filtered_df[filtered_df['面积(平方米)'].between(area_range[0], area_range[1])]
            if floor_range := kwargs.get('floor_range'):
                filtered_df = filtered_df[filtered_df['楼层_val'].between(floor_range[0], floor_range[1])]

        # 聚合
        if kwargs.get('aggregation') == 'count':
            return {'count': len(filtered_df)}

        # 排序
        sort_by = kwargs.get('sort_by', 'price')
        sort_col_map = {'price': price_col, 'area': '面积(平方米)', 'floor': '楼层_val'}
        sort_col = sort_col_map.get(sort_by, price_col)
        sorted_df = filtered_df.sort_values(by=sort_col, ascending=(kwargs.get('sort_order', 'asc') == 'asc'))

        # 格式化输出
        limit = kwargs.get('limit', 10)
        return_fields = kwargs.get('return_fields')
        results_df = sorted_df.head(limit)
        apartments = []
        # 预先计算租期说明，避免在循环中重复生成
        lease_term_str = f"基于 {kwargs.get('lease_term', '12个月及以上')} 租期"

        for _, row in results_df.iterrows():
            # 创建一个包含所有【可返回】字段及其值的完整映射
            all_possible_fields = {
                '房号': row['房号'],
                '楼栋': row['楼栋'],
                '楼层': row['楼层'],
                '房型': row['房型'],
                '面积(平方米)': round(row['面积(平方米)'], 2),
                '朝向': row['朝向'],
                '参考租金': f"{int(row[price_col])}人民币",
                '租金说明': lease_term_str
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


# --- 使用示例 ---
if __name__ == '__main__':
    FILE_PATH = "公寓信息汇总.csv"
    tool = ApartmentQueryTool(filepath=FILE_PATH)

    if not tool.df.empty:
        print("✅ 工具初始化成功，数据已加载。")
        print("\n" + "=" * 70 + "\n")

        print("--- 测试1: 大小写不敏感查询 ---")
        result = tool.query(building=['a'], room_type=['行政单间 '])
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + "=" * 70 + "\n")

        print("--- 测试2: 无效输入范围 ---")
        result = tool.query(price_range=(30000, 10000))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + "=" * 70 + "\n")

        print("--- 测试3: 空列表过滤器 (room_type=[]) ---")
        result = tool.query(building=['B'], room_type=[])
        print(f"查询B座所有房源，总数: {result['total_found']}")

        print("✅ 工具初始化成功，数据已加载。")
        print("\n" + "=" * 70 + "\n")

        # --- 示例查询 1 (不会报错) ---
        print("--- 示例1: 查询A座、15层以上、朝南、年租金2万5以内、面积最大的'一房'公寓 ---")
        result1 = tool.query(
            building=['A'],
            floor_range=(15, 100),
            orientation=['南'],
            room_type=['一房'],
            price_range=(0, 25000),
            lease_term='12个月及以上',
            sort_by='area',
            sort_order='desc',
            return_fields = ['房号', '面积(平方米)', '参考租金', '朝向']
        )
        print(json.dumps(result1, indent=2, ensure_ascii=False))
