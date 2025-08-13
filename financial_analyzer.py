import pandas as pd
import numpy as np


class ProjectFinancials:

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
            df = pd.read_csv(self.filepath, header=0)
            df.rename(columns={'类别-单位万元': 'MetricName'}, inplace=True)
            for col in df.columns:
                if '期' in col or '年' in col:
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
        # V3修正: 使用 .ffill() 替代过时的 method='ffill'
        indexed_df['MetricName'] = indexed_df['MetricName'].ffill()
        indexed_df.set_index('MetricName', inplace=True)
        return indexed_df

    def _setup_mappings(self):
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
            '总运营支出': ['筹开费', '运营费用', '营销推广费', '财务手续费'],
            '净营业收入': '含委托管理费',
            'NOI利润率': '运营NOI率'
        }

        self.column_mapping = {col.split('_')[-1].split('(')[0]: col for col in self.df.columns if
                               '期' in col or '年' in col}
        self.column_mapping.update({
            '开业前6个月': '筹开期（按项目情况改动）_开业前6个月',
            '开业前5个月': '筹开期（按项目情况改动）_开业前5个月',
            '开业前4个月': '筹开期（按项目情况改动）_开业前4个月',
            '开业前3个月': '筹开期（按项目情况改动）_开业前3个月',
            '开业前2个月': '筹开期（按项目情况改动）_开业前2个月',
            '开业前1个月': '筹开期（按项目情况改动）_开业前1个月',
            '开业首年_1月': '开业首年（按实际开业时间填写）_1月(10月）',
            '开业首年_2月': '开业首年（按实际开业时间填写）_2月（11月）',
            '开业首年_3月': '开业首年（按实际开业时间填写）_3月（12月）',
            '开业首年_4月': '开业首年（按实际开业时间填写）_4月（1月）',
            '开业首年_5月': '开业首年（按实际开业时间填写）_5月（2月）',
            '开业首年_6月': '开业首年（按实际开业时间填写）_6月（3月）',
            '开业首年_7月': '开业首年（按实际开业时间填写）_7月（4月）',
            '开业首年_8月': '开业首年（按实际开业时间填写）_8月（5月）',
            '开业首年_9月': '开业首年（按实际开业时间填写）_9月（6月）',
            '开业首年_10月': '开业首年（按实际开业时间填写）_10月（7月）',
            '开业首年_11月': '开业首年（按实际开业时间填写）_11月(8月）',
            '开业首年_12月': '开业首年（按实际开业时间填写）_12月（9月）',
            '开业第一年': '开业第一年',
            '开业第二年': '开业第二年',
            '开业第三年': '开业第三年',
            '开业第四年': '开业第四年',
            '开业第五年': '开业第五年'
        })

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

        if metric in ['净营业收入', 'NOI利润率']:
            try:
                # V3修正: 查找所有匹配行，并取最后一行，这才是最终的NOI数据
                rows = self.raw_df[self.raw_df['序号'] == actual_metric_key]
                if not rows.empty:
                    value = rows[actual_col].iloc[-1]
                else:
                    return f"错误: 无法在'序号'列中找到 '{actual_metric_key}'。"
            except Exception as e:
                return f"查询特殊指标 '{metric}' 时出错: {e}"
        elif metric == '总运营支出':
            try:
                # .loc[...].sum() 会自动处理NaN为0，所以逻辑是安全的
                value = self.df.loc[actual_metric_key, actual_col].sum()
            except Exception as e:
                return f"计算 '{metric}' 时出错: {e}"
        else:
            try:
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
            return f"查询结果: '{time_period}' 的 '{metric}' 为 {value:,.2f} (单位: 万元)"


# --- 主程序入口 ---
if __name__ == "__main__":
    file_path = '北京中天创业园.csv'
    analyzer = ProjectFinancials(file_path)
    if not analyzer.raw_df.empty:
        print("\n--- 开始查询示例 (修正后) ---")
        print(analyzer.get_data(metric='入住率', time_period='开业第一年'))
        print(analyzer.get_data(metric='平均租金', time_period='开业第三年'))
        print(analyzer.get_data(metric='总收入', time_period='开业首年_3月'))
        print(analyzer.get_data(metric='净营业收入', time_period='开业首年_12月'))
        print(analyzer.get_data(metric='总运营支出', time_period='开业第一年'))
        print(analyzer.get_data(metric='NOI利润率', time_period='开业第五年'))
        print(analyzer.get_data(metric='保险费', time_period='开业前1个月'))
        print(analyzer.get_data(metric='住宅总租金收入', time_period='开业前1个月'))
        print(analyzer.get_data(metric='人力成本', time_period='开业前1个月'))
        print(analyzer.get_data(metric='维修维保费', time_period='开业前1个月'))
        print(analyzer.get_data(metric='营销推广费', time_period='开业前1个月'))
        print(analyzer.get_data(metric='行政及办公费用', time_period='开业前1个月'))
        print(analyzer.get_data(metric='能耗费-公区', time_period='开业前1个月'))
        print(analyzer.get_data(metric='能耗费-客房', time_period='开业前1个月'))
        print(analyzer.get_data(metric='大物业管理费', time_period='开业前1个月'))
        print(analyzer.get_data(metric='经营税金', time_period='开业前1个月'))
