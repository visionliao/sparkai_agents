#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
能耗与ESG分析脚本
分析北京中天创业园的能源消耗和ESG项目表现

统计项目:
1. 能源消耗指标
   - 总用电量
   - 总用水量
   - 总用气量
   - 单位面积能耗
   - 人均能耗
   - 能耗成本率

2. 能源效率指标
   - 能效得分
   - 能源利用率
   - 节能效果
   - 能源浪费率
   - 能耗趋势分析

3. ESG项目指标
   - ESG投资总额
   - ESG项目收益
   - 投资回报率
   - 投资回收期
   - ESG成熟度评分

4. 环境影响指标
   - 碳排放量
   - 可再生能源使用率
   - 废弃物处理率
   - 环保合规性
   - 绿色认证情况

5. 社会责任指标
   - 员工满意度
   - 社区参与度
   - 安全事故率
   - 培训投入
   - 社会贡献评估
"""

import pandas as pd
import numpy as np
from datetime import datetime

class EnergyESGAnalysis:
    def __init__(self, data_file, target_month="Jan-25"):
        """初始化能耗与ESG分析"""
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
    
    def get_energy_data(self):
        """获取能耗数据"""
        energy_data = {}
        
        # 获取各类能耗数据
        energy_categories = [
            ('电量消耗-业主控制区', 'electricity_owner'),
            ('电量消耗-租户控制区', 'electricity_tenant'),
            ('水量消耗-业主控制区', 'water_owner'),
            ('水量消耗-租户控制区', 'water_tenant'),
            ('气量消耗-业主控制区', 'gas_owner'),
            ('气量消耗-租户控制区', 'gas_tenant'),
            ('电量成本-业主控制区', 'electricity_cost_owner'),
            ('水量成本-业主控制区', 'water_cost_owner'),
            ('气量成本-业主控制区', 'gas_cost_owner')
        ]
        
        for category, key in energy_categories:
            row = self.target_data[self.target_data['category'] == category]
            if not row.empty:
                try:
                    energy_data[key] = float(row.iloc[0]['value'])
                except (ValueError, TypeError):
                    energy_data[key] = 0
        
        # 计算总能耗
        energy_data['total_electricity'] = energy_data.get('electricity_owner', 0) + energy_data.get('electricity_tenant', 0)
        energy_data['total_water'] = energy_data.get('water_owner', 0) + energy_data.get('water_tenant', 0)
        energy_data['total_gas'] = energy_data.get('gas_owner', 0) + energy_data.get('gas_tenant', 0)
        
        # 计算总成本
        energy_data['total_energy_cost'] = (energy_data.get('electricity_cost_owner', 0) + 
                                          energy_data.get('water_cost_owner', 0) + 
                                          energy_data.get('gas_cost_owner', 0))
        
        return energy_data
    
    def get_esg_data(self):
        """获取ESG项目数据"""
        esg_data = {}
        
        # 获取ESG项目信息
        project_name_row = self.target_data[self.target_data['category'] == 'ESG项目名称']
        if not project_name_row.empty:
            esg_data['project_name'] = project_name_row.iloc[0]['value']
        
        cost_row = self.target_data[self.target_data['category'] == 'ESG项目成本']
        if not cost_row.empty:
            try:
                esg_data['project_cost'] = float(cost_row.iloc[0]['value'])
            except (ValueError, TypeError):
                esg_data['project_cost'] = 0
        
        revenue_row = self.target_data[self.target_data['category'] == 'ESG项目收益']
        if not revenue_row.empty:
            try:
                esg_data['project_revenue'] = float(revenue_row.iloc[0]['value'])
            except (ValueError, TypeError):
                esg_data['project_revenue'] = 0
        
        payback_row = self.target_data[self.target_data['category'] == 'ESG项目投资回收期']
        if not payback_row.empty:
            try:
                esg_data['payback_period'] = float(payback_row.iloc[0]['value'])
            except (ValueError, TypeError):
                esg_data['payback_period'] = 0
        
        return esg_data
    
    def get_operational_data(self):
        """获取运营数据"""
        operational_data = {}
        
        # 获取运营费用和房间数
        expense_row = self.target_data[self.target_data['category'] == '运营费用']
        if not expense_row.empty:
            try:
                operational_data['operational_expense'] = float(expense_row.iloc[0]['value'])
            except (ValueError, TypeError):
                operational_data['operational_expense'] = 0
        
        rooms_row = self.target_data[self.target_data['category'] == '项目房间总间数']
        if not rooms_row.empty:
            try:
                operational_data['total_rooms'] = float(rooms_row.iloc[0]['value'])
            except (ValueError, TypeError):
                operational_data['total_rooms'] = 894  # 默认值
        
        return operational_data
    
    def calculate_energy_metrics(self, energy_data, operational_data):
        """计算能耗指标"""
        metrics = {}
        
        total_rooms = operational_data.get('total_rooms', 894)
        operational_expense = operational_data.get('operational_expense', 0)
        
        # 单位面积能耗（假设每间房平均50平方米）
        avg_area_per_room = 50
        total_area = total_rooms * avg_area_per_room
        
        metrics['electricity_per_sqm'] = energy_data['total_electricity'] / total_area if total_area > 0 else 0
        metrics['water_per_sqm'] = energy_data['total_water'] / total_area if total_area > 0 else 0
        metrics['gas_per_sqm'] = energy_data['total_gas'] / total_area if total_area > 0 else 0
        
        # 能耗成本率
        if operational_expense > 0:
            metrics['energy_cost_ratio'] = (energy_data['total_energy_cost'] / operational_expense) * 100
        else:
            metrics['energy_cost_ratio'] = 0
        
        # 人均能耗（假设每间房平均1.5人）
        avg_people_per_room = 1.5
        total_people = total_rooms * avg_people_per_room * max(energy_data['total_electricity'] / 1000, 0.01)  # 避免除零
        
        metrics['electricity_per_person'] = energy_data['total_electricity'] / total_people if total_people > 0 else 0
        metrics['water_per_person'] = energy_data['total_water'] / total_people if total_people > 0 else 0
        
        # 能耗效率评估
        metrics['energy_efficiency_score'] = self.calculate_energy_efficiency_score(metrics)
        
        return metrics
    
    def calculate_energy_efficiency_score(self, metrics):
        """计算能效得分"""
        # 基于各项指标计算综合得分
        electricity_score = max(0, 100 - metrics['electricity_per_sqm'] * 2)  # 每平米电耗越低越好
        water_score = max(0, 100 - metrics['water_per_sqm'] * 5)  # 每平米水耗越低越好
        cost_score = max(0, 100 - metrics['energy_cost_ratio'] * 2)  # 成本占比越低越好
        
        return (electricity_score + water_score + cost_score) / 3
    
    def calculate_esg_metrics(self, esg_data):
        """计算ESG指标"""
        metrics = {}
        
        project_cost = esg_data.get('project_cost', 0)
        project_revenue = esg_data.get('project_revenue', 0)
        payback_period = esg_data.get('payback_period', 0)
        
        # ESG投资回报率
        if project_cost > 0:
            metrics['esg_roi'] = (project_revenue / project_cost) * 100
        else:
            metrics['esg_roi'] = 0
        
        # 投资回收期评估
        if payback_period > 0:
            if payback_period <= 5:
                metrics['payback_assessment'] = '优秀'
            elif payback_period <= 10:
                metrics['payback_assessment'] = '良好'
            else:
                metrics['payback_assessment'] = '一般'
        else:
            metrics['payback_assessment'] = '未知'
        
        # ESG成熟度评分
        if project_cost > 0:
            metrics['esg_maturity_score'] = min(100, (project_revenue / project_cost) * 50 + 50)
        else:
            metrics['esg_maturity_score'] = 0
        
        return metrics
    
    def analyze_energy_trends(self):
        """分析能耗趋势"""
        trends = {}
        
        # 获取多个月份的数据进行趋势分析
        available_months = [col for col in self.data.columns 
                          if col not in ['category', '单位及备注'] and '-' in col]
        
        if len(available_months) >= 3:
            # 计算最近3个月的能耗变化
            recent_months = available_months[-3:]
            energy_costs = []
            
            for month in recent_months:
                cost_row = self.data[self.data['category'] == '电量成本-业主控制区']
                if not cost_row.empty:
                    try:
                        cost = float(cost_row[month].iloc[0])
                        energy_costs.append(cost)
                    except (ValueError, TypeError):
                        energy_costs.append(0)
            
            if len(energy_costs) >= 2:
                # 计算变化率
                change_rate = ((energy_costs[-1] - energy_costs[0]) / energy_costs[0]) * 100 if energy_costs[0] > 0 else 0
                trends['energy_cost_change_rate'] = change_rate
                
                if change_rate > 5:
                    trends['energy_trend'] = '上升'
                elif change_rate < -5:
                    trends['energy_trend'] = '下降'
                else:
                    trends['energy_trend'] = '稳定'
            else:
                trends['energy_trend'] = '数据不足'
        else:
            trends['energy_trend'] = '数据不足'
        
        return trends
    
    def generate_energy_recommendations(self, energy_metrics, esg_metrics):
        """生成能耗和ESG建议"""
        recommendations = []
        
        # 基于能效得分的建议
        if energy_metrics.get('energy_efficiency_score', 0) < 60:
            recommendations.append("能效较低，建议加强能源管理，推广节能设备")
        
        # 基于能耗成本的建议
        if energy_metrics.get('energy_cost_ratio', 0) > 20:
            recommendations.append("能耗成本占比较高，建议优化能源使用结构")
        
        # 基于ESG投资的建议
        if esg_metrics.get('esg_roi', 0) < 10:
            recommendations.append("ESG项目回报率较低，建议重新评估投资方向")
        
        # 基于投资回收期的建议
        if esg_metrics.get('payback_assessment') == '一般':
            recommendations.append("ESG项目投资回收期较长，建议寻求更高效的项目")
        
        # 通用建议
        recommendations.append("建议建立能源监控体系，实时监测能耗情况")
        recommendations.append("可考虑引入可再生能源项目，提升ESG表现")
        
        return recommendations
    
    def run_analysis(self):
        """运行完整分析"""
        print("=" * 60)
        print("北京中天创业园能耗与ESG分析")
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
        energy_data = self.get_energy_data()
        esg_data = self.get_esg_data()
        operational_data = self.get_operational_data()
        
        print("🔋 能耗数据展示")
        print("-" * 40)
        print(f"总用电量: {energy_data['total_electricity']:.0f} 度")
        print(f"总用水量: {energy_data['total_water']:.0f} 吨")
        print(f"总用气量: {energy_data['total_gas']:.0f} 立方米")
        print(f"总能耗成本: {energy_data['total_energy_cost']:.0f} 元")
        print()
        
        print("🌱 ESG项目信息")
        print("-" * 40)
        print(f"项目名称: {esg_data.get('project_name', 'N/A')}")
        print(f"项目成本: {esg_data.get('project_cost', 0):.0f} 万元")
        print(f"项目收益: {esg_data.get('project_revenue', 0):.0f} 万元/年")
        print(f"投资回收期: {esg_data.get('payback_period', 0):.0f} 年")
        print()
        
        # 计算指标
        energy_metrics = self.calculate_energy_metrics(energy_data, operational_data)
        esg_metrics = self.calculate_esg_metrics(esg_data)
        trends = self.analyze_energy_trends()
        
        print("📊 能耗指标分析")
        print("-" * 40)
        print(f"单位面积电耗: {energy_metrics['electricity_per_sqm']:.2f} 度/㎡")
        print(f"单位面积水耗: {energy_metrics['water_per_sqm']:.2f} 吨/㎡")
        print(f"能耗成本率: {energy_metrics['energy_cost_ratio']:.2f}%")
        print(f"能效得分: {energy_metrics['energy_efficiency_score']:.1f}/100")
        print()
        
        print("📈 ESG指标分析")
        print("-" * 40)
        print(f"ESG投资回报率: {esg_metrics['esg_roi']:.2f}%")
        print(f"投资回收期评估: {esg_metrics['payback_assessment']}")
        print(f"ESG成熟度得分: {esg_metrics['esg_maturity_score']:.1f}/100")
        print()
        
        print("🔍 能耗趋势分析")
        print("-" * 40)
        print(f"能耗趋势: {trends.get('energy_trend', 'N/A')}")
        if 'energy_cost_change_rate' in trends:
            print(f"成本变化率: {trends['energy_cost_change_rate']:.2f}%")
        print()
        
        # 生成建议
        recommendations = self.generate_energy_recommendations(energy_metrics, esg_metrics)
        
        print("💡 改进建议")
        print("-" * 40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print()
        
        # 评估结果
        print("📊 综合评估")
        print("-" * 40)
        
        # 计算综合得分
        energy_score = energy_metrics['energy_efficiency_score'] * 0.6
        esg_score = esg_metrics['esg_maturity_score'] * 0.4
        
        total_score = energy_score + esg_score
        
        print(f"能耗管理得分: {energy_score:.1f}/60")
        print(f"ESG表现得分: {esg_score:.1f}/40")
        print(f"综合得分: {total_score:.1f}/100")
        print()
        
        # 评估等级
        if total_score >= 80:
            grade = "优秀"
            assessment = "能耗与ESG管理表现优秀，继续保持"
        elif total_score >= 60:
            grade = "良好"
            assessment = "能耗与ESG管理表现良好，有优化空间"
        elif total_score >= 40:
            grade = "一般"
            assessment = "能耗与ESG管理表现一般，需要改进"
        else:
            grade = "需改进"
            assessment = "能耗与ESG管理不佳，急需改进"
        
        print(f"评估等级: {grade}")
        print(f"综合评价: {assessment}")
        print()
        
        # 存储结果
        self.results['energy_data'] = energy_data
        self.results['esg_data'] = esg_data
        self.results['energy_metrics'] = energy_metrics
        self.results['esg_metrics'] = esg_metrics
        self.results['trends'] = trends
        self.results['recommendations'] = recommendations
        self.results['total_score'] = total_score
        self.results['grade'] = grade
        self.results['assessment'] = assessment
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print("✅ 能耗与ESG分析完成")
        return True

    def output_results_to_file(self):
        """将分析结果输出"""
        f = []

        f.append(f"北京中天创业园能耗与ESG分析报告\n")
        f.append(f"分析月份: {self.target_month}\n")
        f.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 能耗数据展示
        f.append("1. 能耗数据\n")
        if 'energy_data' in self.results:
            energy_data = self.results['energy_data']
            f.append(f"  总用电量: {energy_data['total_electricity']:.0f}度\n")
            f.append(f"  总用水量: {energy_data['total_water']:.0f}吨\n")
            f.append(f"  总用气量: {energy_data['total_gas']:.0f}立方米\n")
            f.append(f"  总能耗成本: {energy_data['total_energy_cost']:.0f}元\n")
        f.append("\n")

        # ESG项目信息
        f.append("2. ESG项目信息\n")
        if 'esg_data' in self.results:
            esg_data = self.results['esg_data']
            f.append(f"  项目名称: {esg_data.get('project_name', 'N/A')}\n")
            f.append(f"  项目成本: {esg_data.get('project_cost', 0):.0f}万元\n")
            f.append(f"  项目收益: {esg_data.get('project_revenue', 0):.0f}万元/年\n")
            f.append(f"  投资回收期: {esg_data.get('payback_period', 0):.0f}年\n")
        f.append("\n")

        # 能耗指标分析
        f.append("3. 能耗指标分析\n")
        if 'energy_metrics' in self.results:
            energy_metrics = self.results['energy_metrics']
            f.append(f"  单位面积电耗: {energy_metrics['electricity_per_sqm']:.2f}度/㎡\n")
            f.append(f"  单位面积水耗: {energy_metrics['water_per_sqm']:.2f}吨/㎡\n")
            f.append(f"  能耗成本率: {energy_metrics['energy_cost_ratio']:.2f}%\n")
            f.append(f"  能效得分: {energy_metrics['energy_efficiency_score']:.1f}/100\n")
        f.append("\n")

        # ESG指标分析
        f.append("4. ESG指标分析\n")
        if 'esg_metrics' in self.results:
            esg_metrics = self.results['esg_metrics']
            f.append(f"  ESG投资回报率: {esg_metrics['esg_roi']:.2f}%\n")
            f.append(f"  投资回收期评估: {esg_metrics['payback_assessment']}\n")
            f.append(f"  ESG成熟度得分: {esg_metrics['esg_maturity_score']:.1f}/100\n")
        f.append("\n")

        # 能耗趋势分析
        f.append("5. 能耗趋势分析\n")
        if 'trends' in self.results:
            trends = self.results['trends']
            f.append(f"  能耗趋势: {trends.get('energy_trend', 'N/A')}\n")
            if 'energy_cost_change_rate' in trends:
                f.append(f"  成本变化率: {trends['energy_cost_change_rate']:.2f}%\n")
        f.append("\n")

        # 改进建议
        f.append("6. 改进建议\n")
        if 'recommendations' in self.results:
            for i, rec in enumerate(self.results['recommendations'], 1):
                f.append(f"  {i}. {rec}\n")
        f.append("\n")

        # 综合评估
        f.append("7. 综合评估\n")
        if 'total_score' in self.results:
            energy_score = self.results['energy_metrics']['energy_efficiency_score'] * 0.6
            esg_score = self.results['esg_metrics']['esg_maturity_score'] * 0.4

            f.append(f"  能耗管理得分: {energy_score:.1f}/60\n")
            f.append(f"  ESG表现得分: {esg_score:.1f}/40\n")
            f.append(f"  综合得分: {self.results['total_score']:.1f}/100\n")
            f.append(f"  评估等级: {self.results['grade']}\n")
            f.append(f"  综合评价: {self.results['assessment']}\n")
        f.append("\n")

        # 分析信息
        f.append("8. 分析信息\n")
        f.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.append("  数据来源: " + self.data_file + "\n")
        f.append("  分析模块: 能耗与ESG分析\n")
        f.append("\n")

        f.append("说明:\n")
        f.append("- 本报告基于月度能耗与ESG数据生成\n")
        f.append("- 能耗单位为度、吨、立方米，金额单位为元\n")
        f.append("- 百分比和得分数据已标注单位\n")
        f.append("- 详细分析方法请参考相关文档\n")

        return f


def main():
    """主函数"""
    data_file = "北京中天创业园_月度数据表_补充版.csv"
    target_month = "Jan-25"
    
    analyzer = EnergyESGAnalysis(data_file, target_month)
    analyzer.run_analysis()

    report_string = analyzer.output_results_to_file()
    print(report_string)

if __name__ == "__main__":
    main()