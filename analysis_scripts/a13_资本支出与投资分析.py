#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资本支出与投资分析脚本
分析资本支出、投资项目回报和资产效率

统计项目:
1. 资本支出指标
   - 装修改造费用
   - 设备购置费用
   - 系统升级费用
   - 家具更新费用
   - 总资本支出
   - 月度折旧费用

2. 投资项目指标
   - 初始投资额
   - 年收益回报
   - 投资回报率(ROI)
   - 投资回收期
   - 净现值(NPV)
   - 内部收益率(IRR)

3. 资产效率指标
   - 资产周转率
   - 资本支出比率
   - 折旧费用率
   - 维护性资本支出比率
   - 资产使用效率

4. 资本预算指标
   - 可用投资额
   - 所需投资额
   - 预算利用率
   - 投资能力
   - 投资优先级

5. 投资效益指标
   - 投资回报得分
   - 资产效率得分
   - 预算管理得分
   - 综合投资得分
   - 投资风险评估
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class CapitalExpenditureAnalysis:
    def __init__(self):
        """初始化分析类"""
        self.data_file = "北京中天创业园_月度数据表_补充版.csv"
        self.df = None
        self.analysis_month = "Jan-25"
        
    def load_data(self):
        """加载数据文件"""
        try:
            self.df = pd.read_csv(self.data_file, encoding='utf-8')
            print(f"✅ 数据加载成功: {self.data_file}")
            print(f"📊 数据形状: {self.df.shape}")
            
            # 获取可分析的月份
            available_months = self.df['月份'].unique().tolist()
            print(f"📅 可分析的月份: {available_months}")
            
            return True
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return False
    
    def get_project_data(self, month):
        """获取指定月份的项目数据"""
        month_data = self.df[self.df['月份'] == month]
        if len(month_data) == 0:
            return None
        return month_data.iloc[0]
    
    def analyze_capital_expenditure(self, project_data):
        """分析资本支出"""
        # 资本性支出数据
        capital_expenditures = {
            '装修改造': {
                'amount': project_data.get('装修改造费用', 0),
                'category': '改善性支出',
                'depreciation_period': 5,  # 5年折旧
                'monthly_depreciation': 0
            },
            '设备购置': {
                'amount': project_data.get('设备购置费用', 0),
                'category': '设备投资',
                'depreciation_period': 3,  # 3年折旧
                'monthly_depreciation': 0
            },
            '系统升级': {
                'amount': project_data.get('系统升级费用', 0),
                'category': '技术投资',
                'depreciation_period': 3,  # 3年折旧
                'monthly_depreciation': 0
            },
            '家具更新': {
                'amount': project_data.get('家具更新费用', 0),
                'category': '资产更新',
                'depreciation_period': 2,  # 2年折旧
                'monthly_depreciation': 0
            }
        }
        
        # 计算月度折旧
        for item_name, item_data in capital_expenditures.items():
            if item_data['depreciation_period'] > 0:
                item_data['monthly_depreciation'] = item_data['amount'] / (item_data['depreciation_period'] * 12)
        
        # 计算总资本支出
        total_capex = sum(item['amount'] for item in capital_expenditures.values())
        total_monthly_depreciation = sum(item['monthly_depreciation'] for item in capital_expenditures.values())
        
        # 按类别统计
        category_totals = {}
        for item_name, item_data in capital_expenditures.items():
            category = item_data['category']
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += item_data['amount']
        
        return {
            'capital_expenditures': capital_expenditures,
            'total_capex': total_capex,
            'total_monthly_depreciation': total_monthly_depreciation,
            'category_totals': category_totals
        }
    
    def analyze_investment_projects(self, project_data):
        """分析投资项目"""
        # 投资项目数据
        investment_projects = {
            '太阳能板项目': {
                'initial_investment': 500000,  # 50万元
                'annual_return': 0,  # 当前年收益
                'project_lifetime': 25,  # 25年寿命
                'payback_period': 8,  # 8年回收期
                'category': '绿色能源',
                'status': '进行中',
                'monthly_return': 0
            },
            '智能化系统': {
                'initial_investment': 300000,  # 30万元
                'annual_return': 36000,  # 年节省3.6万元
                'project_lifetime': 10,  # 10年寿命
                'payback_period': 8.3,  # 8.3年回收期
                'category': '技术升级',
                'status': '进行中',
                'monthly_return': 3000  # 月节省3000元
            },
            '节能改造': {
                'initial_investment': 200000,  # 20万元
                'annual_return': 24000,  # 年节省2.4万元
                'project_lifetime': 15,  # 15年寿命
                'payback_period': 8.3,  # 8.3年回收期
                'category': '节能改造',
                'status': '进行中',
                'monthly_return': 2000  # 月节省2000元
            }
        }
        
        # 计算投资回报指标
        for project_name, project_data in investment_projects.items():
            # 计算ROI
            if project_data['initial_investment'] > 0:
                project_data['roi'] = (project_data['annual_return'] / project_data['initial_investment']) * 100
            else:
                project_data['roi'] = 0
            
            # 计算NPV（简化计算，假设折现率5%）
            discount_rate = 0.05
            npv = -project_data['initial_investment']
            for year in range(1, project_data['project_lifetime'] + 1):
                npv += project_data['annual_return'] / ((1 + discount_rate) ** year)
            project_data['npv'] = npv
            
            # 计算IRR（简化计算）
            if project_data['annual_return'] > 0:
                project_data['irr'] = (project_data['annual_return'] / project_data['initial_investment']) * 100
            else:
                project_data['irr'] = 0
        
        # 计算总投资
        total_investment = sum(project['initial_investment'] for project in investment_projects.values())
        total_annual_return = sum(project['annual_return'] for project in investment_projects.values())
        
        return {
            'investment_projects': investment_projects,
            'total_investment': total_investment,
            'total_annual_return': total_annual_return
        }
    
    def analyze_asset_efficiency(self, project_data, capex_analysis, investment_analysis):
        """分析资产效率"""
        # 获取资产相关数据
        total_assets = project_data.get('总资产', 0) or 10000000  # 假设总资产1000万元
        operating_income = project_data.get('运营收入', 0)
        
        # 计算资产效率指标
        asset_metrics = {
            '资产周转率': (operating_income / total_assets) if total_assets > 0 else 0,
            '资本支出比率': (capex_analysis['total_capex'] / operating_income) if operating_income > 0 else 0,
            '投资回报率': (investment_analysis['total_annual_return'] / investment_analysis['total_investment']) * 100 if investment_analysis['total_investment'] > 0 else 0,
            '折旧费用率': (capex_analysis['total_monthly_depreciation'] * 12 / operating_income) * 100 if operating_income > 0 else 0
        }
        
        # 计算资产维护指标
        maintenance_capex = sum(item['amount'] for item in capex_analysis['capital_expenditures'].values() 
                             if item['category'] in ['改善性支出', '资产更新'])
        maintenance_ratio = (maintenance_capex / total_assets) * 100 if total_assets > 0 else 0
        
        asset_metrics['维护性资本支出比率'] = maintenance_ratio
        
        return asset_metrics
    
    def analyze_capital_budgeting(self, project_data, capex_analysis, investment_analysis):
        """分析资本预算"""
        # 获取运营数据
        operating_income = project_data.get('运营收入', 0)
        cash_flow = project_data.get('期末可用现金余额', 0)
        
        # 资本预算分析
        capital_budget = {
            'available_for_investment': cash_flow * 0.3,  # 30%的现金可用于投资
            'required_investment': capex_analysis['total_capex'] + investment_analysis['total_investment'],
            'budget_utilization': 0,
            'investment_capacity': 0
        }
        
        # 计算预算利用率
        if capital_budget['available_for_investment'] > 0:
            capital_budget['budget_utilization'] = (capital_budget['required_investment'] / capital_budget['available_for_investment']) * 100
        
        # 计算投资能力
        if operating_income > 0:
            capital_budget['investment_capacity'] = (capital_budget['available_for_investment'] / operating_income) * 100
        
        # 资本支出优先级建议
        spending_priorities = []
        
        # 基于ROI排序投资项目
        sorted_projects = sorted(investment_analysis['investment_projects'].items(), 
                               key=lambda x: x[1]['roi'], reverse=True)
        
        for project_name, project_data in sorted_projects:
            if project_data['roi'] > 0:
                spending_priorities.append({
                    'project': project_name,
                    'priority': '高' if project_data['roi'] > 10 else '中',
                    'roi': project_data['roi'],
                    'payback_period': project_data['payback_period'],
                    'recommendation': '建议继续投资' if project_data['roi'] > 5 else '建议重新评估'
                })
        
        return {
            'capital_budget': capital_budget,
            'spending_priorities': spending_priorities
        }
    
    def generate_investment_recommendations(self, capex_analysis, investment_analysis, asset_metrics, capital_budgeting):
        """生成投资建议"""
        recommendations = []
        
        # 基于投资回报的建议
        for project_name, project_data in investment_analysis['investment_projects'].items():
            if project_data['roi'] < 5:
                recommendations.append({
                    'category': '投资优化',
                    'project': project_name,
                    'issue': f'{project_name}投资回报率较低({project_data["roi"]:.1f}%)',
                    'suggestion': '建议重新评估项目可行性或寻找提高回报的方案',
                    'priority': '高',
                    'potential_improvement': project_data['initial_investment'] * 0.1
                })
            elif project_data['roi'] > 15:
                recommendations.append({
                    'category': '投资扩展',
                    'project': project_name,
                    'issue': f'{project_name}投资回报率较高({project_data["roi"]:.1f}%)',
                    'suggestion': '考虑扩大投资规模或复制成功模式',
                    'priority': '中',
                    'potential_improvement': project_data['initial_investment'] * 0.2
                })
        
        # 基于资本预算的建议
        if capital_budgeting['capital_budget']['budget_utilization'] > 100:
            recommendations.append({
                'category': '预算管理',
                'project': '整体投资',
                'issue': f'资本预算利用率过高({capital_budgeting["capital_budget"]["budget_utilization"]:.1f}%)',
                'suggestion': '建议优化投资计划，分阶段实施或寻找融资渠道',
                'priority': '高',
                'potential_improvement': 0
            })
        
        # 基于资产效率的建议
        if asset_metrics['资产周转率'] < 0.5:
            recommendations.append({
                'category': '资产效率',
                'project': '资产运营',
                'issue': f'资产周转率较低({asset_metrics["资产周转率"]:.2f})',
                'suggestion': '建议提高资产使用效率，考虑资产盘活或业务模式优化',
                'priority': '中',
                'potential_improvement': 0
            })
        
        return recommendations
    
    def calculate_investment_score(self, investment_analysis, asset_metrics, capital_budgeting):
        """计算投资管理得分"""
        # 计算各项得分
        roi_score = 0  # 投资回报得分
        efficiency_score = 0  # 资产效率得分
        budget_score = 0  # 预算管理得分
        
        # 投资回报得分
        total_roi = investment_analysis['total_annual_return'] / investment_analysis['total_investment'] * 100 if investment_analysis['total_investment'] > 0 else 0
        roi_score = min(total_roi * 2, 100)  # ROI越高得分越高
        
        # 资产效率得分
        asset_turnover = asset_metrics['资产周转率']
        efficiency_score = min(asset_turnover * 100, 100)  # 资产周转率越高得分越高
        
        # 预算管理得分
        budget_utilization = capital_budgeting['capital_budget']['budget_utilization']
        if budget_utilization <= 80:
            budget_score = 100
        elif budget_utilization <= 100:
            budget_score = 100 - (budget_utilization - 80) * 2
        else:
            budget_score = 60
        
        # 计算综合得分
        comprehensive_score = (roi_score * 0.4 + efficiency_score * 0.3 + budget_score * 0.3)
        
        # 确定等级
        if comprehensive_score >= 85:
            grade = "优秀"
        elif comprehensive_score >= 75:
            grade = "良好"
        elif comprehensive_score >= 65:
            grade = "一般"
        else:
            grade = "需改进"
        
        return {
            'comprehensive_score': comprehensive_score,
            'grade': grade,
            'detailed_scores': {
                'roi_score': roi_score,
                'efficiency_score': efficiency_score,
                'budget_score': budget_score
            }
        }
    
    def run_analysis(self):
        """运行分析"""
        print(f"{'='*60}")
        print(f"北京中天创业园资本支出与投资分析")
        print(f"{'='*60}")
        print(f"分析月份: {self.analysis_month}")
        print(f"数据文件: {self.data_file}")
        
        # 加载数据
        if not self.load_data():
            return
        
        # 获取项目数据
        project_data = self.get_project_data(self.analysis_month)
        if project_data is None:
            print(f"❌ 未找到{self.analysis_month}的数据")
            return
        
        # 分析资本支出
        capex_analysis = self.analyze_capital_expenditure(project_data)
        
        print(f"\n🏗️ 资本支出分析")
        print(f"-"*40)
        print(f"总资本支出: {capex_analysis['total_capex']:,.0f} 元")
        print(f"月度折旧总额: {capex_analysis['total_monthly_depreciation']:,.0f} 元")
        
        print(f"\n各项资本支出:")
        for item_name, item_data in capex_analysis['capital_expenditures'].items():
            print(f"{item_name}: {item_data['amount']:,.0f} 元 (月折旧: {item_data['monthly_depreciation']:,.0f} 元)")
        
        print(f"\n按类别统计:")
        for category, total in capex_analysis['category_totals'].items():
            percentage = (total / capex_analysis['total_capex'] * 100) if capex_analysis['total_capex'] > 0 else 0
            print(f"{category}: {total:,.0f} 元 ({percentage:.1f}%)")
        
        # 分析投资项目
        investment_analysis = self.analyze_investment_projects(project_data)
        
        print(f"\n💼 投资项目分析")
        print(f"-"*40)
        print(f"总投资: {investment_analysis['total_investment']:,.0f} 元")
        print(f"年收益: {investment_analysis['total_annual_return']:,.0f} 元")
        
        print(f"\n各投资项目详情:")
        for project_name, project_data in investment_analysis['investment_projects'].items():
            print(f"{project_name}:")
            print(f"  - 初始投资: {project_data['initial_investment']:,.0f} 元")
            print(f"  - 年收益: {project_data['annual_return']:,.0f} 元")
            print(f"  - ROI: {project_data['roi']:.1f}%")
            print(f"  - 回收期: {project_data['payback_period']:.1f} 年")
            print(f"  - NPV: {project_data['npv']:,.0f} 元")
            print(f"  - 状态: {project_data['status']}")
        
        # 分析资产效率
        asset_metrics = self.analyze_asset_efficiency(project_data, capex_analysis, investment_analysis)
        
        print(f"\n⚡ 资产效率分析")
        print(f"-"*40)
        for metric_name, value in asset_metrics.items():
            if isinstance(value, float):
                print(f"{metric_name}: {value:.2f}")
            else:
                print(f"{metric_name}: {value}")
        
        # 分析资本预算
        capital_budgeting = self.analyze_capital_budgeting(project_data, capex_analysis, investment_analysis)
        
        print(f"\n💰 资本预算分析")
        print(f"-"*40)
        budget = capital_budgeting['capital_budget']
        print(f"可用投资额: {budget['available_for_investment']:,.0f} 元")
        print(f"所需投资额: {budget['required_investment']:,.0f} 元")
        print(f"预算利用率: {budget['budget_utilization']:.1f}%")
        print(f"投资能力: {budget['investment_capacity']:.1f}%")
        
        print(f"\n投资优先级建议:")
        for priority in capital_budgeting['spending_priorities']:
            print(f"  - {priority['project']}: {priority['priority']}优先级 (ROI: {priority['roi']:.1f}%)")
        
        # 计算得分
        score_results = self.calculate_investment_score(investment_analysis, asset_metrics, capital_budgeting)
        
        print(f"\n🎯 综合评估")
        print(f"-"*40)
        print(f"综合得分: {score_results['comprehensive_score']:.1f}/100")
        print(f"评估等级: {score_results['grade']}")
        print(f"投资回报得分: {score_results['detailed_scores']['roi_score']:.1f}/100")
        print(f"资产效率得分: {score_results['detailed_scores']['efficiency_score']:.1f}/100")
        print(f"预算管理得分: {score_results['detailed_scores']['budget_score']:.1f}/100")
        
        # 生成建议
        recommendations = self.generate_investment_recommendations(
            capex_analysis, investment_analysis, asset_metrics, capital_budgeting)
        
        print(f"\n💡 投资建议")
        print(f"-"*40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['category']} - {rec['project']}")
            print(f"   问题: {rec['issue']}")
            print(f"   建议: {rec['suggestion']}")
            if rec['potential_improvement'] > 0:
                print(f"   潜在改善: {rec['potential_improvement']:,.0f} 元")
            print()
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print(f"{'='*60}")
        print(f"分析完成！")
        print(f"{'='*60}")
'''    
    def output_results_to_file(self):
        """将分析结果输出到文件"""
        filename = f"资本支出与投资分析_{self.analysis_month}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"北京中天创业园资本支出与投资分析报告\n")
            f.write(f"分析月份: {self.analysis_month}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            # 获取项目数据
            project_data = self.get_project_data(self.analysis_month)
            
            # 资本支出分析
            f.write("1. 资本支出分析\n")
            f.write("-"*40 + "\n")
            if project_data:
                total_capex = float(project_data.get('资本性支出', 0))
                f.write(f"  总资本支出: {total_capex:,.0f} 元\n")
                
                # 各项资本支出
                capex_items = [
                    ('太阳能板投资', '太阳能板投资'),
                    ('智能化系统投资', '智能化系统投资'),
                    ('节能改造投资', '节能改造投资'),
                    ('设备更新投资', '设备更新投资')
                ]
                
                for name, key in capex_items:
                    value = float(project_data.get(key, 0))
                    if total_capex > 0:
                        percentage = (value / total_capex) * 100
                        f.write(f"  {name}: {value:,.0f} 元 ({percentage:.1f}%)\n")
                    else:
                        f.write(f"  {name}: {value:,.0f} 元\n")
            f.write("\n")
            
            # 投资项目分析
            f.write("2. 投资项目分析\n")
            f.write("-"*40 + "\n")
            investment_projects = [
                ('太阳能板项目', '太阳能板投资', 20, 10),
                ('智能化系统项目', '智能化系统投资', 15, 8),
                ('节能改造项目', '节能改造投资', 12, 6),
                ('设备更新项目', '设备更新投资', 8, 4)
            ]
            
            for name, key, roi, lifespan in investment_projects:
                if project_data:
                    investment = float(project_data.get(key, 0))
                    annual_return = investment * roi / 100
                    f.write(f"  {name}:\n")
                    f.write(f"    投资金额: {investment:,.0f} 元\n")
                    f.write(f"    预期ROI: {roi}%\n")
                    f.write(f"    年回报: {annual_return:,.0f} 元\n")
                    f.write(f"    回收期: {lifespan} 年\n")
            f.write("\n")
            
            # 综合评估
            f.write("3. 综合评估\n")
            f.write("-"*40 + "\n")
            f.write("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
            f.write("  数据来源: " + self.data_file + "\n")
            f.write("  分析模块: 资本支出与投资分析\n")
            f.write("\n")
            
            f.write("说明:\n")
            f.write("- 本报告基于资本支出和投资数据生成\n")
            f.write("- 所有金额单位为元\n")
            f.write("- ROI为年化投资回报率\n")
            f.write("- 回收期为静态投资回收期\n")
            f.write("- 详细分析方法请参考相关文档\n")
        
        print(f"✅ 分析结果已保存到: {filename}")
'''
def main():
    """主函数"""
    analyzer = CapitalExpenditureAnalysis()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()