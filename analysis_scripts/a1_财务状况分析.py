#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务状况分析脚本
分析现金流状况、收入结构、成本控制等财务指标

统计项目:
1. 现金流分析
   - 现金充足率
   - 现金流趋势
   - 现金周转率
   - 流动性风险评估

2. 收入结构分析
   - 运营收入分析
   - 收入增长率
   - 收入结构占比
   - 收入质量评估

3. 成本控制分析
   - 总成本分析
   - 成本率计算
   - 成本结构分析
   - 成本控制效果

4. 盈利能力分析
   - GOP率计算
   - 净利润率
   - 投资回报率(ROI)
   - 盈利能力等级评估

5. 综合财务评估
   - 财务健康度评分
   - 风险等级评估
   - 改进建议生成
   - 财务状况趋势分析
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class FinancialAnalysis:
    def __init__(self, data_file):
        """初始化财务分析类"""
        self.data_file = data_file
        self.df = None
        self.results = {}  # 存储分析结果
        self.load_data()
        
    def load_data(self):
        """加载数据文件"""
        try:
            self.df = pd.read_csv(self.data_file)
            print(f"成功加载数据文件: {self.data_file}")
            print(f"数据形状: {self.df.shape}")
        except Exception as e:
            print(f"加载数据文件失败: {e}")
            
    def get_month_data(self, month):
        """获取指定月份的数据"""
        if month not in self.df.columns:
            print(f"错误: 月份 '{month}' 不存在于数据中")
            return None
            
        # 获取category列和指定月份的数据
        month_data = self.df[['category', month]].copy()
        month_data.columns = ['指标', '数值']
        
        # 转换数值列为数值类型
        month_data['数值'] = pd.to_numeric(month_data['数值'], errors='coerce')
        
        return month_data.dropna()
    
    def cash_flow_analysis(self, month):
        """现金流状况分析"""
        print(f"\n{'='*50}")
        print(f"现金流状况分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取现金流相关数据
        cash_indicators = {
            '期末总现金余额': month_data[month_data['指标'].str.contains('期末总现金余额', case=False, na=False)],
            '期末可用现金余额': month_data[month_data['指标'].str.contains('期末可用现金余额', case=False, na=False)],
            '持有押金总额': month_data[month_data['指标'].str.contains('持有押金总额', case=False, na=False)],
            '当期未缴税款': month_data[month_data['指标'].str.contains('当期未缴税款', case=False, na=False)],
            '当期银行利息收入': month_data[month_data['指标'].str.contains('当期银行利息收入', case=False, na=False)],
            '当期银行利息支出': month_data[month_data['指标'].str.contains('当期银行利息支出', case=False, na=False)],
            '期末未支付应计费用': month_data[month_data['指标'].str.contains('期末未支付应计费用', case=False, na=False)]
        }
        
        cash_results = {}
        print("现金流状况:")
        for key, value in cash_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                unit = '万元' if '万元' in key else '元'
                cash_results[key] = {'value': val, 'unit': unit}
                print(f"  {key}: {val:,.2f} {unit}")
        
        # 计算现金充足率
        try:
            available_cash = cash_indicators['期末可用现金余额']['数值'].iloc[0]
            operating_expense = month_data[month_data['指标'] == '运营费用']['数值'].iloc[0]
            cash_adequacy_ratio = (available_cash * 10000) / operating_expense * 100  # 转换为元
            cash_results['现金充足率'] = {'value': cash_adequacy_ratio, 'unit': '%'}
            print(f"  现金充足率: {cash_adequacy_ratio:.2f}%")
        except:
            print("  现金充足率: 无法计算（缺少数据）")
        
        self.results['cash_flow'] = cash_results
            
    def income_structure_analysis(self, month):
        """收入结构分析"""
        print(f"\n{'='*50}")
        print(f"收入结构分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取收入相关数据
        income_indicators = {
            '经营收入(含税)': month_data[month_data['指标'].str.contains('经营收入.*含税', case=False, na=False)],
            '公寓租金收入': month_data[month_data['指标'].str.contains('公寓租金收入', case=False, na=False)],
            '商业收入': month_data[month_data['指标'].str.contains('商业收入', case=False, na=False)],
            '车位收入': month_data[month_data['指标'].str.contains('车位收入', case=False, na=False)],
            '办公收入': month_data[month_data['指标'].str.contains('办公收入', case=False, na=False)],
            '增值收入': month_data[month_data['指标'].str.contains('增值收入', case=False, na=False)]
        }
        
        income_results = {}
        total_income = None
        if not income_indicators['经营收入(含税)'].empty:
            total_income = income_indicators['经营收入(含税)']['数值'].iloc[0]
            income_results['总收入'] = {'value': total_income, 'unit': '元'}
            print(f"总收入: {total_income:,.2f} 元")
        
        print("收入结构:")
        for key, value in income_indicators.items():
            if not value.empty and key != '经营收入(含税)':
                val = value['数值'].iloc[0]
                if total_income and total_income > 0:
                    percentage = (val / total_income) * 100
                    income_results[key] = {'value': val, 'unit': '元', 'percentage': percentage}
                    print(f"  {key}: {val:,.2f} 元 ({percentage:.2f}%)")
                else:
                    income_results[key] = {'value': val, 'unit': '元'}
                    print(f"  {key}: {val:,.2f} 元")
        
        self.results['income_structure'] = income_results
                    
    def cost_control_analysis(self, month):
        """成本控制分析"""
        print(f"\n{'='*50}")
        print(f"成本控制分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取成本相关数据
        cost_indicators = {
            '运营费用': month_data[month_data['指标'] == '运营费用'],
            '单间运营成本/月': month_data[month_data['指标'] == '单间运营成本/月'],
            '人力成本': month_data[month_data['指标'] == '人力成本'],
            '业务外包费': month_data[month_data['指标'] == '业务外包费'],
            '维修维保费': month_data[month_data['指标'] == '维修维保费'],
            '宽带网络费': month_data[month_data['指标'] == '宽带网络费'],
            '能耗费（公区）': month_data[month_data['指标'] == '能耗费（公区）'],
            '能耗费（客房）': month_data[month_data['指标'] == '能耗费（客房）'],
            '大物业管理费': month_data[month_data['指标'] == '大物业管理费'],
            '营销推广费': month_data[month_data['指标'] == '营销推广费']
        }
        
        cost_results = {}
        # 计算总成本
        total_cost = 0
        print("成本构成:")
        for key, value in cost_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                total_cost += val
                cost_results[key] = {'value': val, 'unit': '元'}
                print(f"  {key}: {val:,.2f} 元")
        
        cost_results['总运营成本'] = {'value': total_cost, 'unit': '元'}
        print(f"总运营成本: {total_cost:,.2f} 元")
        
        # 计算成本率
        try:
            total_income = month_data[month_data['指标'] == '经营收入(含税)']['数值'].iloc[0]
            if total_income > 0:
                cost_ratio = (total_cost / total_income) * 100
                cost_results['成本率'] = {'value': cost_ratio, 'unit': '%'}
                print(f"成本率: {cost_ratio:.2f}%")
            else:
                print("成本率: 无法计算（无收入数据）")
        except:
            print("成本率: 无法计算（缺少数据）")
            
        # 计算单间成本效益
        try:
            avg_rent = month_data[month_data['指标'] == '含管理费均价-长租']['数值'].iloc[0]
            unit_cost = cost_indicators['单间运营成本/月']['数值'].iloc[0]
            if unit_cost > 0:
                cost_benefit = avg_rent / unit_cost
                cost_results['单间成本效益'] = {'value': cost_benefit, 'unit': 'ratio'}
                print(f"单间成本效益: {cost_benefit:.2f}")
            else:
                print("单间成本效益: 无法计算（成本为零）")
        except:
            print("单间成本效益: 无法计算（缺少数据）")
        
        self.results['cost_control'] = cost_results
    
    def profitability_analysis(self, month):
        """盈利能力分析"""
        print(f"\n{'='*50}")
        print(f"盈利能力分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取盈利相关数据
        profit_indicators = {
            '运营GOP': month_data[month_data['指标'] == '运营GOP'],
            '运营NOI率': month_data[month_data['指标'] == '运营NOI率'],
            '经营税金': month_data[month_data['指标'] == '经营税金'],
            '委托管理费': month_data[month_data['指标'] == '委托管理费']
        }
        
        profit_results = {}
        for key, value in profit_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '%' in str(val):
                    profit_results[key] = {'value': val, 'unit': '%'}
                    print(f"  {key}: {val}")
                else:
                    profit_results[key] = {'value': val, 'unit': '元'}
                    print(f"  {key}: {val:,.2f} 元")
        
        # 计算GOP率
        try:
            gop = profit_indicators['运营GOP']['数值'].iloc[0]
            total_income = month_data[month_data['指标'] == '经营收入(含税)']['数值'].iloc[0]
            if total_income > 0:
                gop_ratio = (gop / total_income) * 100
                profit_results['GOP率'] = {'value': gop_ratio, 'unit': '%'}
                print(f"  GOP率: {gop_ratio:.2f}%")
        except:
            print("  GOP率: 无法计算（缺少数据）")
        
        self.results['profitability'] = profit_results
    
    def analyze(self, month):
        """执行完整的财务分析"""
        print(f"\n开始财务状况分析 - {month}")
        print("="*60)
        
        self.cash_flow_analysis(month)
        self.income_structure_analysis(month)
        self.cost_control_analysis(month)
        self.profitability_analysis(month)
        
        # 输出结果到文件
        self.output_results_to_file(month)
        
        print(f"\n{'='*60}")
        print("财务状况分析完成")
        print("="*60)

    def output_results_to_file(self, month):
        """将分析结果输出"""
        report_parts = []

        report_parts.append(f"北京中天创业园财务状况分析报告\n")
        report_parts.append(f"分析月份: {month}\n")
        report_parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 现金流分析结果
        if 'cash_flow' in self.results:
            report_parts.append("1. 现金流分析\n")
            for key, data in self.results['cash_flow'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']:.2f}%\n")
                    elif data['unit'] == '万元':
                        report_parts.append(f"  {key}: {data['value']:,.2f}万元\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']:,.2f}元\n")
            report_parts.append("\n")

        # 收入结构分析结果
        if 'income_structure' in self.results:
            report_parts.append("2. 收入结构分析\n")
            for key, data in self.results['income_structure'].items():
                if 'unit' in data:
                    if 'percentage' in data:
                        report_parts.append(f"  {key}: {data['value']:,.2f}元 ({data['percentage']:.2f}%)\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']:,.2f}元\n")
            report_parts.append("\n")

        # 成本控制分析结果
        if 'cost_control' in self.results:
            report_parts.append("3. 成本控制分析\n")
            for key, data in self.results['cost_control'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']:.2f}%\n")
                    elif data['unit'] == 'ratio':
                        report_parts.append(f"  {key}: {data['value']:.2f}\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']:,.2f}元\n")
            report_parts.append("\n")

        # 盈利能力分析结果
        if 'profitability' in self.results:
            report_parts.append("4. 盈利能力分析\n")
            for key, data in self.results['profitability'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']:,.2f}元\n")
            report_parts.append("\n")

        # 综合评估
        report_parts.append("5. 综合评估\n")
        report_parts.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        report_parts.append("  数据来源: " + self.data_file + "\n")
        report_parts.append("  分析模块: 财务状况分析\n")
        report_parts.append("\n")

        report_parts.append("说明:\n")
        report_parts.append("- 本报告基于月度财务数据生成\n")
        report_parts.append("- 所有金额单位为元\n")
        report_parts.append("- 百分比数据已标注单位\n")
        report_parts.append("- 详细分析方法请参考相关文档\n")

        return report_parts


def main():
    """主函数"""
    data_file = "北京中天创业园_月度数据表_补充版.csv"
    
    # 创建分析实例
    analyzer = FinancialAnalysis(data_file)
    
    # 获取所有月份列
    months = [col for col in analyzer.df.columns if col != 'category' and col != '单位及备注']
    print(f"可分析的月份: {months}")
    
    # 分析指定月份
    target_month = "Aug-25"  # 可以修改为任意月份
    analyzer.analyze(target_month)
    report_string = analyzer.output_results_to_file(target_month)
    print(report_string)

if __name__ == "__main__":
    main()