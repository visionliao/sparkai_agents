import pandas as pd
import numpy as np
import csv

class ProjectFinancials:
    """
    用于分析"北京中天创业园_月度数据表.csv"财务预测数据的工具。
    基于原始脚本修改，适配当前数据文件格式。
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.raw_df = self._load_data()
        self.df = self._setup_indexed_df()
        self._setup_mappings()
        print("财务数据分析器已成功加载并初始化。")

    def _clean_value(self, value):
        if isinstance(value, str):
            value = value.strip().replace(',', '')
            if value == '–' or value == '-':
                return 0.0
            if '%' in value:
                return pd.to_numeric(value.replace('%', ''), errors='coerce') / 100
        return pd.to_numeric(value, errors='coerce')

    def _load_data(self) -> pd.DataFrame:
        try:
            # 手动读取CSV文件以正确处理格式
            with open(self.filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # 清理BOM字符
            if rows and rows[0] and rows[0][0].startswith('\ufeff'):
                rows[0][0] = rows[0][0][1:]
            
            # 确定最大列数
            max_cols = max(len(row) for row in rows)
            
            # 标准化所有行的列数
            standardized_rows = []
            for row in rows:
                if len(row) < max_cols:
                    row.extend([''] * (max_cols - len(row)))
                standardized_rows.append(row)
            
            # 创建DataFrame
            df = pd.DataFrame(standardized_rows[1:], columns=standardized_rows[0])
            
            # 清理数值列
            for col in df.columns:
                if '-' in col and col not in ['单位及备注-例科目范围、口径、数量、单价']:
                    df[col] = df[col].apply(self._clean_value)
            
            return df
        except FileNotFoundError:
            print(f"错误：文件未找到于路径 '{self.filepath}'")
            return pd.DataFrame()
        except Exception as e:
            print(f"加载或处理文件时出错: {e}")
            return pd.DataFrame()

    def _setup_indexed_df(self) -> pd.DataFrame:
        indexed_df = self.raw_df.copy()
        # 第一列就是指标名称，直接设置为索引
        indexed_df.set_index('category', inplace=True)
        return indexed_df

    def _setup_mappings(self):
        # 基于实际数据文件的指标名称更新映射
        self.metric_mapping = {
            '入住率': '项目整体出租率',
            '平均租金': '含管理费均价-长租',
            '住宅总租金收入': '公寓租金收入',
            '总收入': '经营收入(含税)',
            '人力成本': '人力成本',
            '维修维保费': '维修维保费',
            '营销推广费': '营销推广费',
            '行政及办公费用': '行政及办公费用',
            '能耗费-公区': '能耗费（公区）',
            '能耗费-客房': '能耗费（客房）',
            '大物业管理费': '大物业管理费',
            '经营税金': '经营税金',
            '保险费': '保险费',
            '总运营支出': ['筹开费', '运营费用', '营销推广费'],
            '净营业收入': '含委托管理费',
            'NOI利润率': '运营NOI率'
        }

        # 建立时间周期映射，将YYYY-MM格式映射为业务术语
        self.column_mapping = {}
        
        # 遍历所有列，建立时间映射
        for col in self.df.columns:
            if '-' in col and col not in ['单位及备注-例科目范围、口径、数量、单价']:
                # 将YYYY-MM格式映射为业务术语
                if col == '2024-07':
                    self.column_mapping['开业前6个月'] = col
                elif col == '2024-08':
                    self.column_mapping['开业前5个月'] = col
                elif col == '2024-09':
                    self.column_mapping['开业前4个月'] = col
                elif col == '2024-10':
                    self.column_mapping['开业前3个月'] = col
                elif col == '2024-11':
                    self.column_mapping['开业前2个月'] = col
                elif col == '2024-12':
                    self.column_mapping['开业前1个月'] = col
                elif '2025-' in col:
                    month = col.split('-')[1]
                    self.column_mapping[f'开业首年_{month}月'] = col
                elif col == '2026-01':
                    self.column_mapping['开业第二年'] = col
                elif col == '2027-01':
                    self.column_mapping['开业第三年'] = col
                elif col == '2028-01':
                    self.column_mapping['开业第四年'] = col
                elif col == '2029-01':
                    self.column_mapping['开业第五年'] = col
        
        # 添加直接的时间映射，方便查询
        for col in self.df.columns:
            if '-' in col and col not in ['单位及备注-例科目范围、口径、数量、单价']:
                self.column_mapping[col] = col  # 允许直接用日期查询

    def get_data(self, metric: str, time_period: str) -> str:
        if self.raw_df.empty:
            return "错误：数据未加载，无法查询。"

        if metric not in self.metric_mapping:
            return f"错误：未知的指标 '{metric}'。可用指标: {list(self.metric_mapping.keys())}"

        if time_period not in self.column_mapping:
            return f"错误：未知的时间周期 '{time_period}'。可用周期: {list(self.column_mapping.keys())}"

        actual_col = self.column_mapping[time_period]
        actual_metric_key = self.metric_mapping[metric]

        value = np.nan

        try:
            if metric in ['净营业收入', 'NOI利润率']:
                # 特殊指标处理
                value = self.df.loc[actual_metric_key, actual_col]
                if isinstance(value, pd.Series):
                    value = value.dropna().iloc[0] if not value.dropna().empty else np.nan
            elif metric == '总运营支出':
                # 总运营支出是多个指标的总和
                if isinstance(actual_metric_key, list):
                    total = 0
                    for key in actual_metric_key:
                        if key in self.df.index:
                            val = self.df.loc[key, actual_col]
                            if pd.notna(val):
                                total += val
                    value = total
                else:
                    value = self.df.loc[actual_metric_key, actual_col]
            else:
                # 普通指标
                value_series = self.df.loc[actual_metric_key, actual_col]
                if isinstance(value_series, pd.Series):
                    value = value_series.dropna().iloc[0] if not value_series.dropna().empty else np.nan
                else:
                    value = value_series
        except KeyError:
            return f"错误: 无法在DataFrame中定位指标 '{actual_metric_key}'。"
        except Exception as e:
            return f"查询时出错: {e}"

        if pd.isna(value):
            return f"查询结果：在 '{time_period}' 的 '{metric}' 数据为空或为0。"

        if '率' in metric:
            return f"查询结果: '{time_period}' 的 '{metric}' 为 {value:.2%}"
        else:
            return f"查询结果: '{time_period}' 的 '{metric}' 为 {value:,.2f} (单位: 元)"


# --- 主程序入口 ---
if __name__ == "__main__":
    file_path = '北京中天创业园_月度数据表.csv'
    analyzer = ProjectFinancials(file_path)
    if not analyzer.raw_df.empty:
        print("\n--- 开始查询示例 ---")
        
        # 修正查询参数以匹配实际的时间映射
        print(analyzer.get_data(metric='入住率', time_period='2025-09'))
        print(analyzer.get_data(metric='平均租金', time_period='2025-06'))
        print(analyzer.get_data(metric='总收入', time_period='2026-01'))
        print(analyzer.get_data(metric='净营业收入', time_period='2025-12'))
        print(analyzer.get_data(metric='总运营支出', time_period='2025-01'))
        print(analyzer.get_data(metric='NOI利润率', time_period='2029-01'))
        print(analyzer.get_data(metric='总运营支出', time_period='2024-11'))