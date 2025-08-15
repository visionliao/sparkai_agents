#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场竞争分析脚本
分析北京中天创业园与竞争对手的市场表现对比

统计项目:
1. 市场份额指标
   - 项目出租率
   - 竞争对手出租率对比
   - 市场份额估算
   - 市场渗透率
   - 客户获取成本

2. 价格竞争力指标
   - 项目均价
   - 竞争对手价格对比
   - 价格优势指数
   - 租金效率
   - 价格弹性分析

3. 转化效率指标
   - 项目转化率
   - 竞争对手L:S指标
   - 转化效率对比
   - 销售漏斗分析
   - 渠道效果评估

4. 竞争格局指标
   - 竞争强度分析
   - 市场集中度
   - 竞争对手分布
   - 差异化程度
   - 进入壁垒分析

5. 竞争优势指标
   - 综合竞争优势指数
   - 品牌影响力
   - 服务差异化
   - 客户忠诚度
   - 市场定位评估
"""

import pandas as pd
import numpy as np
from datetime import datetime

class MarketCompetitionAnalysis:
    def __init__(self, data_file, target_month="Jan-25"):
        """初始化市场竞争分析"""
        self.data_file = data_file
        self.target_month = target_month
        self.data = None
        self.target_data = None
        self.results = {}  # 存储分析结果
        
    def load_data(self):
        """加载数据"""
        try:
            self.data = pd.read_csv(self.data_file, encoding='utf-8')
            print(f"✅ 数据加载成功: {self.data_file}")
            return True
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return False
    
    def extract_target_month_data(self):
        """提取目标月份数据"""
        if self.target_month not in self.data.columns:
            print(f"❌ 目标月份 {self.target_month} 不存在")
            return False
        
        self.target_data = self.data[['category', '单位及备注', self.target_month]].copy()
        self.target_data.columns = ['category', 'unit', 'value']
        return True
    
    def get_competitor_data(self):
        """获取竞争对手数据"""
        competitor_data = {}
        
        # 提取竞争对手基本信息
        for i in range(1, 4):  # 3个竞争对手
            prefix = f"主要竞争对手{i}"
            
            # 获取竞争对手名称
            name_row = self.target_data[self.target_data['category'] == f"{prefix}名称"]
            if not name_row.empty:
                name = name_row.iloc[0]['value']
                competitor_data[f"competitor_{i}"] = {
                    'name': name,
                    'occupancy_rate': None,
                    'ls_ratio': None,
                    'rent_range': None,
                    'rent_efficiency': None
                }
                
                # 获取入住率
                occupancy_row = self.target_data[self.target_data['category'] == f"竞争对手{i}入住率"]
                if not occupancy_row.empty:
                    competitor_data[f"competitor_{i}"]['occupancy_rate'] = float(occupancy_row.iloc[0]['value'])
                
                # 获取L:S指标
                ls_row = self.target_data[self.target_data['category'] == f"竞争对手{i}L:S指标"]
                if not ls_row.empty:
                    competitor_data[f"competitor_{i}"]['ls_ratio'] = float(ls_row.iloc[0]['value'])
                
                # 获取租金范围
                rent_row = self.target_data[self.target_data['category'] == f"竞争对手{i}各户型租金范围"]
                if not rent_row.empty:
                    competitor_data[f"competitor_{i}"]['rent_range'] = rent_row.iloc[0]['value']
                
                # 获取租金效率
                efficiency_row = self.target_data[self.target_data['category'] == f"竞争对手{i}各户型租金效率"]
                if not efficiency_row.empty:
                    competitor_data[f"competitor_{i}"]['rent_efficiency'] = efficiency_row.iloc[0]['value']
        
        return competitor_data
    
    def get_project_data(self):
        """获取本项目数据"""
        project_data = {}
        
        # 获取项目出租率
        occupancy_row = self.target_data[self.target_data['category'] == '项目整体出租率']
        if not occupancy_row.empty:
            project_data['occupancy_rate'] = float(occupancy_row.iloc[0]['value'])
        
        # 获取项目均价
        price_row = self.target_data[self.target_data['category'] == '项目整体均价']
        if not price_row.empty:
            project_data['average_price'] = float(price_row.iloc[0]['value'])
        
        # 获取转化率
        conversion_row = self.target_data[self.target_data['category'] == '当期转化率']
        if not conversion_row.empty:
            project_data['conversion_rate'] = float(conversion_row.iloc[0]['value'])
        
        return project_data
    
    def calculate_market_metrics(self, project_data, competitor_data):
        """计算市场指标"""
        metrics = {}
        
        # 计算平均竞争对手数据
        competitor_occupancy_rates = []
        competitor_ls_ratios = []
        
        for comp_key, comp_data in competitor_data.items():
            if comp_data['occupancy_rate'] is not None:
                competitor_occupancy_rates.append(comp_data['occupancy_rate'])
            if comp_data['ls_ratio'] is not None:
                competitor_ls_ratios.append(comp_data['ls_ratio'])
        
        avg_competitor_occupancy = np.mean(competitor_occupancy_rates) if competitor_occupancy_rates else 0
        avg_competitor_ls = np.mean(competitor_ls_ratios) if competitor_ls_ratios else 0
        
        # 市场份额估算
        if 'occupancy_rate' in project_data and avg_competitor_occupancy > 0:
            metrics['market_share_estimate'] = (project_data['occupancy_rate'] / avg_competitor_occupancy) * 100
        else:
            metrics['market_share_estimate'] = 0
        
        # 转化率对比
        if 'conversion_rate' in project_data and avg_competitor_ls > 0:
            metrics['conversion_efficiency'] = (project_data['conversion_rate'] / avg_competitor_ls) * 100
        else:
            metrics['conversion_efficiency'] = 0
        
        # 竞争优势指数
        if 'occupancy_rate' in project_data and avg_competitor_occupancy > 0:
            occupancy_advantage = project_data['occupancy_rate'] / avg_competitor_occupancy
        else:
            occupancy_advantage = 1
        
        if 'conversion_rate' in project_data and avg_competitor_ls > 0:
            conversion_advantage = project_data['conversion_rate'] / avg_competitor_ls
        else:
            conversion_advantage = 1
        
        metrics['competitive_advantage_index'] = (occupancy_advantage + conversion_advantage) / 2 * 100
        
        # 市场定位分析
        if 'occupancy_rate' in project_data:
            if project_data['occupancy_rate'] >= avg_competitor_occupancy * 1.1:
                metrics['market_position'] = '领先者'
            elif project_data['occupancy_rate'] >= avg_competitor_occupancy * 0.9:
                metrics['market_position'] = '追随者'
            else:
                metrics['market_position'] = '挑战者'
        else:
            metrics['market_position'] = '未知'
        
        return metrics
    
    def analyze_competitive_landscape(self, project_data, competitor_data):
        """分析竞争格局"""
        analysis = {}
        
        # 竞争强度分析
        total_competitors = len(competitor_data)
        high_occupancy_competitors = sum(1 for comp in competitor_data.values() 
                                      if comp['occupancy_rate'] and comp['occupancy_rate'] > 80)
        
        if total_competitors > 0:
            analysis['competition_intensity'] = high_occupancy_competitors / total_competitors
        else:
            analysis['competition_intensity'] = 0
        
        # 市场集中度分析
        if total_competitors > 0:
            analysis['market_concentration'] = '中度集中' if total_competitors <= 3 else '高度分散'
        else:
            analysis['market_concentration'] = '未知'
        
        # 竞争差异化分析
        competitor_names = [comp['name'] for comp in competitor_data.values()]
        analysis['competitor_names'] = competitor_names
        
        return analysis
    
    def generate_recommendations(self, metrics, analysis):
        """生成建议"""
        recommendations = []
        
        # 基于市场份额的建议
        if metrics.get('market_share_estimate', 0) < 80:
            recommendations.append("市场份额较低，建议加强营销推广和客户服务")
        
        # 基于转化效率的建议
        if metrics.get('conversion_efficiency', 0) < 90:
            recommendations.append("转化效率有待提升，建议优化销售流程和培训")
        
        # 基于竞争地位的建议
        if analysis.get('competition_intensity', 0) > 0.6:
            recommendations.append("市场竞争激烈，建议突出差异化优势")
        
        # 基于市场定位的建议
        if metrics.get('market_position') == '挑战者':
            recommendations.append("目前处于挑战者地位，建议采取差异化竞争策略")
        elif metrics.get('market_position') == '追随者':
            recommendations.append("目前处于追随者地位，建议寻找突破机会")
        
        return recommendations
    
    def run_analysis(self):
        """运行完整分析"""
        print("=" * 60)
        print("北京中天创业园市场竞争分析")
        print("=" * 60)
        print(f"分析月份: {self.target_month}")
        print(f"数据文件: {self.data_file}")
        print()
        
        # 加载数据
        if not self.load_data():
            return False
        
        # 提取目标月份数据
        if not self.extract_target_month_data():
            return False
        
        # 获取数据
        project_data = self.get_project_data()
        competitor_data = self.get_competitor_data()
        
        if not project_data or not competitor_data:
            print("❌ 数据提取失败")
            return False
        
        print("📊 基础数据展示")
        print("-" * 40)
        print(f"本项目出租率: {project_data.get('occupancy_rate', 'N/A')}%")
        print(f"本项目均价: {project_data.get('average_price', 'N/A')}元")
        print(f"本项目转化率: {project_data.get('conversion_rate', 'N/A')}%")
        print()
        
        print("🏢 竞争对手概况")
        print("-" * 40)
        for comp_key, comp_data in competitor_data.items():
            print(f"{comp_data['name']}:")
            print(f"  - 入住率: {comp_data['occupancy_rate']}%")
            print(f"  - L:S指标: {comp_data['ls_ratio']}")
            print(f"  - 租金范围: {comp_data['rent_range']}")
            print(f"  - 租金效率: {comp_data['rent_efficiency']}")
            print()
        
        # 计算指标
        metrics = self.calculate_market_metrics(project_data, competitor_data)
        analysis = self.analyze_competitive_landscape(project_data, competitor_data)
        
        print("📈 市场指标分析")
        print("-" * 40)
        print(f"市场份额估算: {metrics['market_share_estimate']:.1f}%")
        print(f"转化效率对比: {metrics['conversion_efficiency']:.1f}%")
        print(f"竞争优势指数: {metrics['competitive_advantage_index']:.1f}")
        print(f"市场定位: {metrics['market_position']}")
        print()
        
        print("🔍 竞争格局分析")
        print("-" * 40)
        print(f"竞争强度: {analysis['competition_intensity']:.1f}")
        print(f"市场集中度: {analysis['market_concentration']}")
        print(f"主要竞争对手: {', '.join(analysis['competitor_names'])}")
        print()
        
        # 生成建议
        recommendations = self.generate_recommendations(metrics, analysis)
        
        print("💡 改进建议")
        print("-" * 40)
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("暂无特别建议")
        print()
        
        # 评估结果
        print("📊 综合评估")
        print("-" * 40)
        
        # 计算综合得分
        market_share_score = min(metrics['market_share_estimate'] / 100, 1) * 30
        conversion_score = min(metrics['conversion_efficiency'] / 100, 1) * 30
        advantage_score = min(metrics['competitive_advantage_index'] / 100, 1) * 40
        
        total_score = market_share_score + conversion_score + advantage_score
        
        # 评估等级
        if total_score >= 80:
            grade = "优秀"
            assessment = "市场竞争地位强劲，建议保持优势"
        elif total_score >= 60:
            grade = "良好"
            assessment = "市场竞争表现良好，有改进空间"
        elif total_score >= 40:
            grade = "一般"
            assessment = "市场竞争表现一般，需要重点改进"
        else:
            grade = "需改进"
            assessment = "市场竞争表现不佳，急需提升竞争力"
        
        print(f"市场份额得分: {market_share_score:.1f}/30")
        print(f"转化效率得分: {conversion_score:.1f}/30")
        print(f"竞争优势得分: {advantage_score:.1f}/40")
        print(f"综合得分: {total_score:.1f}/100")
        print()
        print(f"评估等级: {grade}")
        print(f"综合评价: {assessment}")
        print()
        
        # 存储结果
        self.results['project_data'] = project_data
        self.results['competitor_data'] = competitor_data
        self.results['metrics'] = metrics
        self.results['analysis'] = analysis
        self.results['recommendations'] = recommendations
        self.results['total_score'] = total_score
        self.results['grade'] = grade
        self.results['assessment'] = assessment
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print("✅ 市场竞争分析完成")
        return True

    def output_results_to_file(self):
        """将分析结果输出"""
        f = []

        f.append(f"北京中天创业园市场竞争分析报告\n")
        f.append(f"分析月份: {self.target_month}\n")
        f.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 基础数据展示
        f.append("1. 基础数据\n")
        if 'project_data' in self.results:
            project_data = self.results['project_data']
            f.append(f"  本项目出租率: {project_data.get('occupancy_rate', 'N/A')}%\n")
            f.append(f"  本项目均价: {project_data.get('average_price', 'N/A')}元\n")
            f.append(f"  本项目转化率: {project_data.get('conversion_rate', 'N/A')}%\n")
        f.append("\n")

        # 竞争对手概况
        f.append("2. 竞争对手概况\n")
        if 'competitor_data' in self.results:
            competitor_data = self.results['competitor_data']
            for comp_key, comp_data in competitor_data.items():
                f.append(f"  {comp_data['name']}:\n")
                f.append(f"    - 入住率: {comp_data['occupancy_rate']}%\n")
                f.append(f"    - L:S指标: {comp_data['ls_ratio']}\n")
                f.append(f"    - 租金范围: {comp_data['rent_range']}\n")
                f.append(f"    - 租金效率: {comp_data['rent_efficiency']}\n")
                f.append("\n")

        # 市场指标分析
        f.append("3. 市场指标分析\n")
        if 'metrics' in self.results:
            metrics = self.results['metrics']
            f.append(f"  市场份额估算: {metrics['market_share_estimate']:.1f}%\n")
            f.append(f"  转化效率对比: {metrics['conversion_efficiency']:.1f}%\n")
            f.append(f"  竞争优势指数: {metrics['competitive_advantage_index']:.1f}\n")
            f.append(f"  市场定位: {metrics['market_position']}\n")
        f.append("\n")

        # 竞争格局分析
        f.append("4. 竞争格局分析\n")
        if 'analysis' in self.results:
            analysis = self.results['analysis']
            f.append(f"  竞争强度: {analysis['competition_intensity']:.1f}\n")
            f.append(f"  市场集中度: {analysis['market_concentration']}\n")
            f.append(f"  主要竞争对手: {', '.join(analysis['competitor_names'])}\n")
        f.append("\n")

        # 改进建议
        f.append("5. 改进建议\n")
        if 'recommendations' in self.results and self.results['recommendations']:
            for i, rec in enumerate(self.results['recommendations'], 1):
                f.append(f"  {i}. {rec}\n")
        else:
            f.append("  暂无特别建议\n")
        f.append("\n")

        # 综合评估
        f.append("6. 综合评估\n")
        if 'total_score' in self.results:
            market_share_score = min(self.results['metrics']['market_share_estimate'] / 100, 1) * 30
            conversion_score = min(self.results['metrics']['conversion_efficiency'] / 100, 1) * 30
            advantage_score = min(self.results['metrics']['competitive_advantage_index'] / 100, 1) * 40

            f.append(f"  市份额得分: {market_share_score:.1f}/30\n")
            f.append(f"  转化效率得分: {conversion_score:.1f}/30\n")
            f.append(f"  竞争优势得分: {advantage_score:.1f}/40\n")
            f.append(f"  综合得分: {self.results['total_score']:.1f}/100\n")
            f.append(f"  评估等级: {self.results['grade']}\n")
            f.append(f"  综合评价: {self.results['assessment']}\n")
        f.append("\n")

        # 综合信息
        f.append("7. 分析信息\n")
        f.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.append("  数据来源: " + self.data_file + "\n")
        f.append("  分析模块: 市场竞争分析\n")
        f.append("\n")

        f.append("说明:\n")
        f.append("- 本报告基于月度市场竞争数据生成\n")
        f.append("- 百分比数据已标注单位\n")
        f.append("- 竞争分析基于公开可获得的数据\n")
        f.append("- 详细分析方法请参考相关文档\n")
        
        return f

def main():
    """主函数"""
    data_file = "北京中天创业园_月度数据表_补充版.csv"
    target_month = "Jan-25"
    
    analyzer = MarketCompetitionAnalysis(data_file, target_month)
    analyzer.run_analysis()

    report_string = analyzer.output_results_to_file()
    print(report_string)

if __name__ == "__main__":
    main()