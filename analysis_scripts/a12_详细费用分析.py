#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细费用分析脚本
分析各项费用的构成、趋势和控制效果

统计项目:
1. 费用结构指标
   - 人力成本
   - 能耗费用
   - 营销费用
   - 行政费用
   - 维修费用
   - 税费
   - 其他费用

2. 费用分类指标
   - 运营费用总额
   - 营销费用总额
   - 财务费用总额
   - 其他费用总额
   - 费用占比分析

3. 成本类型指标
   - 固定成本
   - 变动成本
   - 半变动成本
   - 法定费用
   - 成本结构合理性

4. 费用效率指标
   - 总费用率
   - 人均费用
   - 单位面积费用
   - 费用控制效果
   - 成本优化空间

5. 费用控制指标
   - 费用趋势分析
   - 预算执行率
   - 异常费用监测
   - 成本节约目标
   - 费用管理评级
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class DetailedExpenseAnalysis:
    def __init__(self, data, time):
        """初始化分析类"""
        self.data_file = data
        self.df = None
        self.analysis_month = time
        
    def load_data(self):
        """加载数据文件"""
        try:
            self.df = pd.read_csv(self.data_file, encoding='utf-8')
            print(f"✅ 数据加载成功: {self.data_file}")
            print(f"📊 数据形状: {self.df.shape}")
            
            # 获取可分析的月份（从列名中提取）
            available_months = [col for col in self.df.columns if col not in ['category', '单位及备注']]
            print(f"📅 可分析的月份: {available_months}")
            
            return True
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return False
    
    def get_project_data(self, month):
        """获取指定月份的项目数据"""
        # 创建数据字典
        data_dict = {}
        for _, row in self.df.iterrows():
            category = row['category']
            if month in self.df.columns:
                data_dict[category] = row[month]
        
        return data_dict
    
    def analyze_expense_structure(self, project_data):
        """分析费用结构"""
        # 各项费用数据
        expenses = {
            '人力成本': {
                'amount': float(project_data.get('人力成本', 0)),
                'category': '运营费用',
                'type': '固定成本'
            },
            '能耗费用': {
                'amount': float(project_data.get('能耗费用', 0)),
                'category': '运营费用',
                'type': '变动成本'
            },
            '营销费用': {
                'amount': float(project_data.get('营销费用', 0)),
                'category': '营销费用',
                'type': '变动成本'
            },
            '行政费用': {
                'amount': float(project_data.get('行政费用', 0)),
                'category': '运营费用',
                'type': '固定成本'
            },
            '维修费用': {
                'amount': float(project_data.get('维修费用', 0)),
                'category': '运营费用',
                'type': '变动成本'
            },
            '税费': {
                'amount': float(project_data.get('税费', 0)),
                'category': '财务费用',
                'type': '法定费用'
            },
            '其他费用': {
                'amount': float(project_data.get('其他费用', 0)),
                'category': '其他费用',
                'type': '其他'
            }
        }
        
        # 计算总费用
        total_expenses = sum(data['amount'] for data in expenses.values())
        
        # 计算各项费用占比
        for key, data in expenses.items():
            data['percentage'] = (data['amount'] / total_expenses * 100) if total_expenses > 0 else 0
        
        # 按类别统计
        category_totals = {}
        for key, data in expenses.items():
            category = data['category']
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += data['amount']
        
        # 按成本类型统计
        type_totals = {}
        for key, data in expenses.items():
            cost_type = data['type']
            if cost_type not in type_totals:
                type_totals[cost_type] = 0
            type_totals[cost_type] += data['amount']
        
        return {
            'expenses': expenses,
            'total_expenses': total_expenses,
            'category_totals': category_totals,
            'type_totals': type_totals
        }
    
    def analyze_expense_trends(self):
        """分析费用趋势"""
        historical_data = []
        month_columns = [col for col in self.df.columns if col not in ['category', '单位及备注']]
        
        for month in sorted(month_columns):
            month_data = self.get_project_data(month)
            if month_data is not None:
                expenses = {
                    '人力成本': float(month_data.get('人力成本', 0)),
                    '能耗费用': float(month_data.get('能耗费用', 0)),
                    '营销费用': float(month_data.get('营销费用', 0)),
                    '行政费用': float(month_data.get('行政费用', 0)),
                    '维修费用': float(month_data.get('维修费用', 0)),
                    '税费': float(month_data.get('税费', 0)),
                    '其他费用': float(month_data.get('其他费用', 0))
                }
                
                total_expenses = sum(expenses.values())
                
                historical_data.append({
                    'month': month,
                    'expenses': expenses,
                    'total_expenses': total_expenses
                })
        
        # 计算趋势
        trends = {}
        if len(historical_data) >= 2:
            current = historical_data[-1]
            previous = historical_data[-2]
            
            for expense_type in current['expenses'].keys():
                current_amount = current['expenses'][expense_type]
                previous_amount = previous['expenses'][expense_type]
                
                if previous_amount > 0:
                    trend = ((current_amount - previous_amount) / previous_amount) * 100
                else:
                    trend = 0
                
                trends[expense_type] = trend
            
            # 总费用趋势
            if previous['total_expenses'] > 0:
                total_trend = ((current['total_expenses'] - previous['total_expenses']) / previous['total_expenses']) * 100
            else:
                total_trend = 0
            
            trends['total_expenses'] = total_trend
        
        return {
            'historical_data': historical_data,
            'trends': trends
        }
    
    def analyze_expense_efficiency(self, project_data, expense_structure):
        """分析费用效率"""
        # 获取收入数据
        total_revenue = project_data.get('总收入', 0)
        operating_revenue = project_data.get('运营收入', 0)
        
        # 计算费用率
        expense_ratios = {}
        for expense_name, expense_data in expense_structure['expenses'].items():
            if total_revenue > 0:
                expense_ratios[expense_name] = (expense_data['amount'] / total_revenue) * 100
            else:
                expense_ratios[expense_name] = 0
        
        # 计算总费用率
        total_expense_ratio = (expense_structure['total_expenses'] / total_revenue * 100) if total_revenue > 0 else 0
        
        # 计算人均费用
        fte_count = float(project_data.get('当前FTE数', 0))
        per_person_expenses = {}
        for expense_name, expense_data in expense_structure['expenses'].items():
            if fte_count > 0:
                per_person_expenses[expense_name] = expense_data['amount'] / fte_count
            else:
                per_person_expenses[expense_name] = 0
        
        # 计算单位面积费用
        total_area = float(project_data.get('项目房间总间数', 0)) * 30  # 假设每间30平米
        per_sqm_expenses = {}
        for expense_name, expense_data in expense_structure['expenses'].items():
            if total_area > 0:
                per_sqm_expenses[expense_name] = expense_data['amount'] / total_area
            else:
                per_sqm_expenses[expense_name] = 0
        
        return {
            'expense_ratios': expense_ratios,
            'total_expense_ratio': total_expense_ratio,
            'per_person_expenses': per_person_expenses,
            'per_sqm_expenses': per_sqm_expenses
        }
    
    def benchmark_expenses(self, expense_structure):
        """费用行业对标"""
        # 行业标准（假设数据）
        industry_benchmarks = {
            '人力成本': {'ratio': 35.0, 'efficiency': '中等'},
            '能耗费用': {'ratio': 15.0, 'efficiency': '中等'},
            '营销费用': {'ratio': 8.0, 'efficiency': '中等'},
            '行政费用': {'ratio': 12.0, 'efficiency': '中等'},
            '维修费用': {'ratio': 10.0, 'efficiency': '中等'},
            '税费': {'ratio': 15.0, 'efficiency': '固定'},
            '其他费用': {'ratio': 5.0, 'efficiency': '低'}
        }
        
        # 计算对标结果
        benchmark_results = {}
        for expense_name, benchmark in industry_benchmarks.items():
            if expense_name in expense_structure['expenses']:
                actual_ratio = expense_structure['expenses'][expense_name]['percentage']
                deviation = actual_ratio - benchmark['ratio']
                
                # 评估偏差程度
                if abs(deviation) <= 2:
                    assessment = "正常"
                elif abs(deviation) <= 5:
                    assessment = "轻微偏差"
                else:
                    assessment = "显著偏差"
                
                benchmark_results[expense_name] = {
                    'actual_ratio': actual_ratio,
                    'benchmark_ratio': benchmark['ratio'],
                    'deviation': deviation,
                    'assessment': assessment
                }
        
        return benchmark_results
    
    def generate_cost_control_recommendations(self, expense_structure, efficiency_analysis, benchmark_results):
        """生成成本控制建议"""
        recommendations = []
        
        # 基于费用结构的建议
        top_expenses = sorted(expense_structure['expenses'].items(), 
                            key=lambda x: x[1]['amount'], reverse=True)[:3]
        
        for expense_name, expense_data in top_expenses:
            if expense_name in benchmark_results:
                benchmark = benchmark_results[expense_name]
                if benchmark['deviation'] > 5:
                    recommendations.append({
                        'category': '成本控制',
                        'expense_type': expense_name,
                        'issue': f'{expense_name}占比{expense_data["percentage"]:.1f}%，高于行业标准{benchmark["benchmark_ratio"]:.1f}%',
                        'suggestion': f'建议优化{expense_name}管理，制定成本控制措施',
                        'priority': '高',
                        'potential_savings': expense_data['amount'] * 0.1  # 假设可节省10%
                    })
        
        # 基于效率的建议
        if efficiency_analysis['total_expense_ratio'] > 80:
            recommendations.append({
                'category': '整体效率',
                'expense_type': '总费用',
                'issue': f'总费用率{efficiency_analysis["total_expense_ratio"]:.1f}%，处于较高水平',
                'suggestion': '建议全面审视费用结构，寻找降本增效机会',
                'priority': '高',
                'potential_savings': expense_structure['total_expenses'] * 0.05
            })
        
        # 基于趋势的建议
        # 这里需要获取趋势数据，简化处理
        recommendations.append({
            'category': '趋势监控',
            'expense_type': '各项费用',
            'issue': '建议建立费用趋势监控机制',
            'suggestion': '设置费用预警阈值，及时发现异常波动',
            'priority': '中',
            'potential_savings': 0
        })
        
        return recommendations
    
    def calculate_expense_score(self, expense_structure, efficiency_analysis, benchmark_results):
        """计算费用管理得分"""
        # 计算各项得分
        structure_score = 0  # 费用结构合理性
        efficiency_score = 0  # 费用效率
        benchmark_score = 0  # 行业对标
        
        # 费用结构得分（基于固定成本比例）
        fixed_cost_ratio = (expense_structure['type_totals'].get('固定成本', 0) / 
                          expense_structure['total_expenses'] * 100) if expense_structure['total_expenses'] > 0 else 0
        structure_score = max(0, 100 - abs(fixed_cost_ratio - 60) * 2)  # 60%为最优
        
        # 费用效率得分（基于总费用率）
        total_ratio = efficiency_analysis['total_expense_ratio']
        efficiency_score = max(0, 100 - total_ratio * 0.5)  # 费用率越低得分越高
        
        # 行业对标得分
        if benchmark_results:
            deviations = [abs(result['deviation']) for result in benchmark_results.values()]
            avg_deviation = np.mean(deviations)
            benchmark_score = max(0, 100 - avg_deviation * 5)  # 偏差越小得分越高
        else:
            benchmark_score = 80
        
        # 计算综合得分
        comprehensive_score = (structure_score * 0.3 + efficiency_score * 0.4 + benchmark_score * 0.3)
        
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
                'structure_score': structure_score,
                'efficiency_score': efficiency_score,
                'benchmark_score': benchmark_score
            }
        }
    
    def run_analysis(self):
        """运行分析"""
        print(f"{'='*60}")
        print(f"北京中天创业园详细费用分析")
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
        
        # 分析费用结构
        expense_structure = self.analyze_expense_structure(project_data)
        
        print(f"\n💰 费用结构分析")
        print(f"-"*40)
        print(f"总费用: {expense_structure['total_expenses']:,.0f} 元")
        
        # 按金额排序显示各项费用
        sorted_expenses = sorted(expense_structure['expenses'].items(), 
                               key=lambda x: x[1]['amount'], reverse=True)
        
        for expense_name, expense_data in sorted_expenses:
            print(f"{expense_name}: {expense_data['amount']:,.0f} 元 ({expense_data['percentage']:.1f}%)")
        
        print(f"\n📊 费用分类统计")
        print(f"-"*40)
        for category, total in expense_structure['category_totals'].items():
            percentage = (total / expense_structure['total_expenses'] * 100) if expense_structure['total_expenses'] > 0 else 0
            print(f"{category}: {total:,.0f} 元 ({percentage:.1f}%)")
        
        print(f"\n🏷️ 成本类型统计")
        print(f"-"*40)
        for cost_type, total in expense_structure['type_totals'].items():
            percentage = (total / expense_structure['total_expenses'] * 100) if expense_structure['total_expenses'] > 0 else 0
            print(f"{cost_type}: {total:,.0f} 元 ({percentage:.1f}%)")
        
        # 分析费用趋势
        trend_analysis = self.analyze_expense_trends()
        
        print(f"\n📈 费用趋势分析")
        print(f"-"*40)
        if 'trends' in trend_analysis and trend_analysis['trends']:
            for expense_type, trend in trend_analysis['trends'].items():
                print(f"{expense_type}: {trend:+.1f}%")
        else:
            print("暂无足够数据进行趋势分析")
        
        # 分析费用效率
        efficiency_analysis = self.analyze_expense_efficiency(project_data, expense_structure)
        
        print(f"\n⚡ 费用效率分析")
        print(f"-"*40)
        print(f"总费用率: {efficiency_analysis['total_expense_ratio']:.1f}%")
        
        print(f"\n各项费用占收入比:")
        for expense_name, ratio in efficiency_analysis['expense_ratios'].items():
            print(f"{expense_name}: {ratio:.1f}%")
        
        # 行业对标
        benchmark_results = self.benchmark_expenses(expense_structure)
        
        print(f"\n🎯 行业对标分析")
        print(f"-"*40)
        for expense_name, result in benchmark_results.items():
            print(f"{expense_name}:")
            print(f"  实际占比: {result['actual_ratio']:.1f}%")
            print(f"  行业标准: {result['benchmark_ratio']:.1f}%")
            print(f"  偏差: {result['deviation']:+.1f}%")
            print(f"  评估: {result['assessment']}")
            print()
        
        # 计算得分
        score_results = self.calculate_expense_score(expense_structure, efficiency_analysis, benchmark_results)
        
        print(f"\n🎯 综合评估")
        print(f"-"*40)
        print(f"综合得分: {score_results['comprehensive_score']:.1f}/100")
        print(f"评估等级: {score_results['grade']}")
        print(f"费用结构得分: {score_results['detailed_scores']['structure_score']:.1f}/100")
        print(f"费用效率得分: {score_results['detailed_scores']['efficiency_score']:.1f}/100")
        print(f"行业对标得分: {score_results['detailed_scores']['benchmark_score']:.1f}/100")
        
        # 生成建议
        recommendations = self.generate_cost_control_recommendations(
            expense_structure, efficiency_analysis, benchmark_results)
        
        print(f"\n💡 成本控制建议")
        print(f"-"*40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['category']} - {rec['expense_type']}")
            print(f"   问题: {rec['issue']}")
            print(f"   建议: {rec['suggestion']}")
            if rec['potential_savings'] > 0:
                print(f"   潜在节省: {rec['potential_savings']:,.0f} 元")
            print()
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print(f"{'='*60}")
        print(f"分析完成！")
        print(f"{'='*60}")

    def output_results_to_file(self):
        """将分析结果输出"""
        f = []
        
        f.append(f"北京中天创业园详细费用分析报告\n")
        f.append(f"分析月份: {self.analysis_month}\n")
        f.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 获取项目数据
        project_data = self.get_project_data(self.analysis_month)

        # 费用结构分析
        f.append("1. 费用结构分析\n")
        if project_data:
            total_expenses = float(project_data.get('运营费用', 0))
            f.append(f"  总费用: {total_expenses:,.0f} 元\n")

            # 各项费用
            expense_items = [
                ('人力成本', '人力成本'),
                ('业务外包费', '业务外包费'),
                ('维修维保费', '维修维保费'),
                ('宽带网络费', '宽带网络费'),
                ('能耗费（公区）', '能耗费（公区）'),
                ('大物业管理费', '大物业管理费'),
                ('营销推广费', '营销推广费')
            ]

            for name, key in expense_items:
                value = float(project_data.get(key, 0))
                if total_expenses > 0:
                    percentage = (value / total_expenses) * 100
                    f.append(f"  {name}: {value:,.0f} 元 ({percentage:.1f}%)\n")
                else:
                    f.append(f"  {name}: {value:,.0f} 元\n")
        f.append("\n")

        # 费用分类分析
        f.append("2. 费用分类分析\n")
        if project_data:
            operational = float(project_data.get('运营费用', 0))
            marketing = float(project_data.get('营销推广费', 0))
            maintenance = float(project_data.get('维修维保费', 0))

            f.append(f"  运营费用: {operational:,.0f} 元\n")
            f.append(f"  营销费用: {marketing:,.0f} 元\n")
            f.append(f"  维护费用: {maintenance:,.0f} 元\n")
        f.append("\n")

        # 费用效率分析
        f.append("3. 费用效率分析\n")
        if project_data:
            total_rooms = float(project_data.get('项目房间总间数', 0))
            total_expenses = float(project_data.get('运营费用', 0))
            operating_income = float(project_data.get('运营收入', 0))

            if total_rooms > 0:
                cost_per_room = total_expenses / total_rooms
                f.append(f"  单间成本: {cost_per_room:.0f} 元/间\n")

            if operating_income > 0:
                expense_ratio = (total_expenses / operating_income) * 100
                f.append(f"  费用率: {expense_ratio:.1f}%\n")
        f.append("\n")

        # 综合评估
        f.append("4. 综合评估\n")
        f.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.append("  数据来源: " + self.data_file + "\n")
        f.append("  分析模块: 详细费用分析\n")
        f.append("\n")

        f.append("说明:\n")
        f.append("- 本报告基于月度费用数据生成\n")
        f.append("- 所有金额单位为元\n")
        f.append("- 百分比数据已标注单位\n")
        f.append("- 详细分析方法请参考相关文档\n")

        return f
        

def main():
    """主函数"""
    time = "Jan-25"
    data = "北京中天创业园_月度数据表_补充版.csv"
    analyzer = DetailedExpenseAnalysis(data, time)
    analyzer.run_analysis()

    report_string = analyzer.output_results_to_file()
    print(report_string)


if __name__ == "__main__":
    main()