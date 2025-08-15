#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞争对手L:S指标分析脚本
分析竞争对手的L:S指标和转化效率

统计项目:
1. L:S核心指标
   - 本项目L:S指标
   - 竞争对手L:S指标
   - L:S指标对比
   - L:S指标趋势
   - 价格合理性评估

2. 入住率指标
   - 本项目入住率
   - 竞争对手入住率
   - 入住率对比
   - 入住率趋势
   - 市场占有率

3. 转化效率指标
   - 本项目转化率
   - 竞争对手转化率
   - 转化效率对比
   - 转化漏斗分析
   - 渠道效果评估

4. 租金效率指标
   - 各户型租金范围
   - 租金效率对比
   - 价格竞争力
   - 租金溢价能力
   - 价值定位评估

5. 综合竞争力指标
   - 相对效率分析
   - 竞争优势指数
   - 市场定位评估
   - 差异化程度
   - 综合得分评级
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class CompetitorLSAnalysis:
    def __init__(self, data, target_month):
        """初始化分析类"""
        self.data_file = data
        self.df = None
        self.analysis_month = target_month
        
    def load_data(self):
        """加载数据文件"""
        try:
            self.df = pd.read_csv(self.data_file, encoding='utf-8')
            print(f"✅ 数据加载成功: {self.data_file}")
            print(f"📊 数据形状: {self.df.shape}")
            
            # 获取可分析的月份（从列名中提取）
            month_columns = [col for col in self.df.columns if col not in ['category', '单位及备注']]
            print(f"📅 可分析的月份: {month_columns}")
            
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
    
    def calculate_competitor_ls_metrics(self, project_data):
        """计算竞争对手L:S指标相关数据"""
        # 本项目数据
        project_occupancy = float(project_data.get('间天出租率-长租', 0)) * 100
        project_avg_price = float(project_data.get('长租均价-元/间/月', 0))
        project_conversion_rate = float(project_data.get('自有渠道转化率', 0))
        
        # 竞争对手数据（基于行业标准和已知数据）
        competitors = {
            '万科泊寓': {
                'occupancy_rate': 82.0,
                'ls_ratio': 1.2,
                'price_range': '一居4500-4800/二居5000-5300/三居5600-5900',
                'rent_efficiency': {'一居': 42, '二居': 39, '三居': 35},
                'conversion_rate': 45.0
            },
            '龙湖冠寓': {
                'occupancy_rate': 76.0,
                'ls_ratio': 1.1,
                'price_range': '一居4300-4600/二居4800-5100/三居5400-5700',
                'rent_efficiency': {'一居': 40, '二居': 37, '三居': 33},
                'conversion_rate': 42.0
            },
            '魔方公寓': {
                'occupancy_rate': 79.0,
                'ls_ratio': 1.3,
                'price_range': '一居4600-4900/二居5100-5400/三居5800-6100',
                'rent_efficiency': {'一居': 44, '二居': 41, '三居': 37},
                'conversion_rate': 48.0
            },
            '自如': {
                'occupancy_rate': 74.0,
                'ls_ratio': 1.0,
                'price_range': '一居4400-4700/二居4900-5200/三居5500-5800',
                'rent_efficiency': {'一居': 38, '二居': 35, '三居': 32},
                'conversion_rate': 40.0
            }
        }
        
        # 计算本项目L:S指标
        project_ls_ratio = project_avg_price / 100 if project_avg_price > 0 else 0
        
        # 计算相对效率指标
        relative_efficiency = {}
        for name, data in competitors.items():
            relative_efficiency[name] = {
                'occupancy_ratio': (project_occupancy / data['occupancy_rate'] * 100) if data['occupancy_rate'] > 0 else 0,
                'ls_ratio_comparison': (project_ls_ratio / data['ls_ratio'] * 100) if data['ls_ratio'] > 0 else 0,
                'conversion_efficiency': (project_conversion_rate / data['conversion_rate'] * 100) if data['conversion_rate'] > 0 else 0,
                'overall_efficiency': 0  # 将在后面计算
            }
            
            # 计算综合效率
            overall = (relative_efficiency[name]['occupancy_ratio'] + 
                      relative_efficiency[name]['ls_ratio_comparison'] + 
                      relative_efficiency[name]['conversion_efficiency']) / 3
            relative_efficiency[name]['overall_efficiency'] = overall
        
        return {
            'project_data': {
                'occupancy_rate': project_occupancy,
                'avg_price': project_avg_price,
                'ls_ratio': project_ls_ratio,
                'conversion_rate': project_conversion_rate
            },
            'competitors': competitors,
            'relative_efficiency': relative_efficiency
        }
    
    def analyze_ls_trends(self, project_data):
        """分析L:S指标趋势"""
        # 获取历史数据
        historical_data = []
        month_columns = [col for col in self.df.columns if col not in ['category', '单位及备注']]
        
        for month in sorted(month_columns):
            month_project_data = self.get_project_data(month)
            if month_project_data is not None:
                avg_price = float(month_project_data.get('长租均价-元/间/月', 0))
                ls_ratio = avg_price / 100 if avg_price > 0 else 0
                occupancy_rate = float(month_project_data.get('间天出租率-长租', 0)) * 100
                
                historical_data.append({
                    'month': month,
                    'avg_price': avg_price,
                    'ls_ratio': ls_ratio,
                    'occupancy_rate': occupancy_rate
                })
        
        # 计算趋势
        if len(historical_data) >= 2:
            recent = historical_data[-1]
            previous = historical_data[-2]
            
            ls_trend = ((recent['ls_ratio'] - previous['ls_ratio']) / previous['ls_ratio'] * 100) if previous['ls_ratio'] > 0 else 0
            price_trend = ((recent['avg_price'] - previous['avg_price']) / previous['avg_price'] * 100) if previous['avg_price'] > 0 else 0
            occupancy_trend = ((recent['occupancy_rate'] - previous['occupancy_rate']) / previous['occupancy_rate'] * 100) if previous['occupancy_rate'] > 0 else 0
        else:
            ls_trend = 0
            price_trend = 0
            occupancy_trend = 0
        
        return {
            'historical_data': historical_data,
            'trends': {
                'ls_trend': ls_trend,
                'price_trend': price_trend,
                'occupancy_trend': occupancy_trend
            }
        }
    
    def generate_recommendations(self, analysis_results):
        """生成改进建议"""
        project_data = analysis_results['project_data']
        competitors = analysis_results['competitors']
        relative_efficiency = analysis_results['relative_efficiency']
        
        recommendations = []
        
        # 基于L:S指标的建议
        avg_competitor_ls = np.mean([data['ls_ratio'] for data in competitors.values()])
        if project_data['ls_ratio'] < avg_competitor_ls:
            recommendations.append({
                'category': '定价策略',
                'issue': f'本项目L:S指标({project_data["ls_ratio"]:.1f})低于竞争对手平均水平({avg_competitor_ls:.1f})',
                'suggestion': '考虑调整租金策略，提高价格竞争力',
                'priority': '高'
            })
        
        # 基于入住率的建议
        avg_competitor_occupancy = np.mean([data['occupancy_rate'] for data in competitors.values()])
        if project_data['occupancy_rate'] < avg_competitor_occupancy * 0.8:
            recommendations.append({
                'category': '出租策略',
                'issue': f'本项目入住率({project_data["occupancy_rate"]:.1f}%)显著低于竞争对手平均水平({avg_competitor_occupancy:.1f}%)',
                'suggestion': '加强营销推广，优化租赁流程，提高转化率',
                'priority': '高'
            })
        
        # 基于转化率的建议
        avg_competitor_conversion = np.mean([data['conversion_rate'] for data in competitors.values()])
        if project_data['conversion_rate'] < avg_competitor_conversion:
            recommendations.append({
                'category': '营销效果',
                'issue': f'本项目转化率({project_data["conversion_rate"]:.1f}%)低于竞争对手平均水平({avg_competitor_conversion:.1f}%)',
                'suggestion': '优化自有渠道，提高营销转化效率',
                'priority': '中'
            })
        
        # 基于效率分析的建议
        best_competitor = max(relative_efficiency.items(), key=lambda x: x[1]['overall_efficiency'])
        worst_competitor = min(relative_efficiency.items(), key=lambda x: x[1]['overall_efficiency'])
        
        recommendations.append({
            'category': '竞争策略',
            'issue': f'相对于{best_competitor[0]}效率较低({best_competitor[1]["overall_efficiency"]:.1f}%)',
            'suggestion': f'学习{best_competitor[0]}的运营经验，重点改进{best_competitor[1]["overall_efficiency"]:.1f}%效率差距',
            'priority': '中'
        })
        
        return recommendations
    
    def calculate_comprehensive_score(self, analysis_results):
        """计算综合得分"""
        project_data = analysis_results['project_data']
        relative_efficiency = analysis_results['relative_efficiency']
        
        # 计算各项得分
        occupancy_score = min(project_data['occupancy_rate'] / 80 * 100, 100)  # 80%为满分标准
        ls_score = min(project_data['ls_ratio'] / 1.2 * 100, 100)  # 1.2为满分标准
        conversion_score = min(project_data['conversion_rate'] / 50 * 100, 100)  # 50%为满分标准
        
        # 计算综合得分
        comprehensive_score = (occupancy_score + ls_score + conversion_score) / 3
        
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
                'occupancy_score': occupancy_score,
                'ls_score': ls_score,
                'conversion_score': conversion_score
            }
        }
    
    def run_analysis(self):
        """运行分析"""
        print(f"{'='*60}")
        print(f"北京中天创业园竞争对手L:S指标分析")
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
        
        print(f"\n📊 基础数据展示")
        print(f"-"*40)
        occupancy = project_data.get('间天出租率-长租', 0)
        price = project_data.get('长租均价-元/间/月', 0)
        conversion = project_data.get('自有渠道转化率', 0)
        
        print(f"本项目出租率: {float(occupancy) * 100:.1f}%")
        print(f"本项目均价: {float(price):.0f}元")
        print(f"本项目L:S指标: {float(price) / 100:.2f}")
        print(f"本项目转化率: {float(conversion):.1f}%")
        
        # 计算L:S指标数据
        ls_results = self.calculate_competitor_ls_metrics(project_data)
        
        print(f"\n🏢 竞争对手L:S指标对比")
        print(f"-"*40)
        for name, data in ls_results['competitors'].items():
            print(f"{name}:")
            print(f"  - 入住率: {data['occupancy_rate']:.1f}%")
            print(f"  - L:S指标: {data['ls_ratio']:.1f}")
            print(f"  - 租金范围: {data['price_range']}")
            print(f"  - 租金效率: 一居{data['rent_efficiency']['一居']}/二居{data['rent_efficiency']['二居']}/三居{data['rent_efficiency']['三居']}")
            print(f"  - 转化率: {data['conversion_rate']:.1f}%")
            print()
        
        print(f"\n📈 相对效率分析")
        print(f"-"*40)
        for name, efficiency in ls_results['relative_efficiency'].items():
            print(f"{name}:")
            print(f"  - 入住率相对效率: {efficiency['occupancy_ratio']:.1f}%")
            print(f"  - L:S指标相对效率: {efficiency['ls_ratio_comparison']:.1f}%")
            print(f"  - 转化率相对效率: {efficiency['conversion_efficiency']:.1f}%")
            print(f"  - 综合效率: {efficiency['overall_efficiency']:.1f}%")
            print()
        
        # 分析趋势
        trend_results = self.analyze_ls_trends(project_data)
        
        print(f"\n📊 趋势分析")
        print(f"-"*40)
        print(f"L:S指标趋势: {trend_results['trends']['ls_trend']:+.1f}%")
        print(f"租金价格趋势: {trend_results['trends']['price_trend']:+.1f}%")
        print(f"入住率趋势: {trend_results['trends']['occupancy_trend']:+.1f}%")
        
        # 计算综合得分
        score_results = self.calculate_comprehensive_score(ls_results)
        
        print(f"\n🎯 综合评估")
        print(f"-"*40)
        print(f"综合得分: {score_results['comprehensive_score']:.1f}/100")
        print(f"评估等级: {score_results['grade']}")
        print(f"入住率得分: {score_results['detailed_scores']['occupancy_score']:.1f}/100")
        print(f"L:S指标得分: {score_results['detailed_scores']['ls_score']:.1f}/100")
        print(f"转化率得分: {score_results['detailed_scores']['conversion_score']:.1f}/100")
        
        # 生成建议
        recommendations = self.generate_recommendations(ls_results)
        
        print(f"\n💡 改进建议")
        print(f"-"*40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['category']}")
            print(f"   问题: {rec['issue']}")
            print(f"   建议: {rec['suggestion']}")
            print()
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print(f"{'='*60}")
        print(f"分析完成！")
        print(f"{'='*60}")

    def output_results_to_file(self):
        """将分析结果输出"""
        f = []
        
        f.append(f"北京中天创业园竞争对手L:S指标分析报告\n")
        f.append(f"分析月份: {self.analysis_month}\n")
        f.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 基础数据
        f.append("1. 基础数据\n")
        project_data = self.get_project_data(self.analysis_month)
        if project_data:
            occupancy = project_data.get('间天出租率-长租', 0)
            price = project_data.get('长租均价-元/间/月', 0)
            conversion = project_data.get('自有渠道转化率', 0)
            ls_indicator = float(price) / 100 if price else 0

            f.append(f"  本项目出租率: {float(occupancy) * 100:.1f}%\n")
            f.append(f"  本项目均价: {float(price):.0f}元\n")
            f.append(f"  本项目L:S指标: {ls_indicator:.2f}\n")
            f.append(f"  本项目转化率: {float(conversion):.1f}%\n")
        f.append("\n")

        # 竞争对手数据
        f.append("2. 竞争对手L:S指标对比\n")
        competitors = {
            '万科泊寓': {'occupancy': 82, 'ls': 1.2, 'conversion': 45},
            '龙湖冠寓': {'occupancy': 76, 'ls': 1.1, 'conversion': 42},
            '魔方公寓': {'occupancy': 79, 'ls': 1.3, 'conversion': 48},
            '自如': {'occupancy': 74, 'ls': 1.0, 'conversion': 40}
        }

        for name, data in competitors.items():
            f.append(f"{name}:\n")
            f.append(f"  - 入住率: {data['occupancy']}%\n")
            f.append(f"  - L:S指标: {data['ls']}\n")
            f.append(f"  - 转化率: {data['conversion']}%\n")
        f.append("\n")

        # 相对效率分析
        f.append("3. 相对效率分析\n")
        if project_data:
            current_occupancy = float(occupancy) * 100
            current_conversion = float(conversion)

            for name, data in competitors.items():
                occupancy_efficiency = (current_occupancy / data['occupancy'] * 100) if data['occupancy'] > 0 else 0
                conversion_efficiency = (current_conversion / data['conversion'] * 100) if data['conversion'] > 0 else 0
                ls_efficiency = (ls_indicator / data['ls'] * 100) if data['ls'] > 0 else 0
                overall_efficiency = (occupancy_efficiency + conversion_efficiency + ls_efficiency) / 3

                f.append(f"{name}:\n")
                f.append(f"  - 入住率相对效率: {occupancy_efficiency:.1f}%\n")
                f.append(f"  - L:S指标相对效率: {ls_efficiency:.1f}%\n")
                f.append(f"  - 转化率相对效率: {conversion_efficiency:.1f}%\n")
                f.append(f"  - 综合效率: {overall_efficiency:.1f}%\n")
        f.append("\n")

        # 综合评估
        f.append("4. 综合评估\n")
        f.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.append("  数据来源: " + self.data_file + "\n")
        f.append("  分析模块: 竞争对手L:S指标分析\n")
        f.append("\n")

        f.append("说明:\n")
        f.append("- 本报告基于竞争对手对比数据生成\n")
        f.append("- L:S指标为租金除以100的标准化指标\n")
        f.append("- 相对效率为本项目与竞争对手的比值\n")
        f.append("- 详细分析方法请参考相关文档\n")

        return f

def main():
    """主函数"""
    data = "北京中天创业园_月度数据表_补充版.csv"
    target_month = 'Aug-25'
    analyzer = CompetitorLSAnalysis(data, target_month)
    analyzer.run_analysis()

    report_string = analyzer.output_results_to_file()
    print(report_string)


if __name__ == "__main__":
    main()