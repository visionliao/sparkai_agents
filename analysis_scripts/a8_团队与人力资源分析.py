#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
团队与人力资源分析脚本
分析北京中天创业园的团队结构和人力资源效率

统计项目:
1. 人力资源配置指标
   - 计划FTE总数
   - 当前FTE数
   - 编制完成率
   - 人员流动率
   - 招聘完成率

2. 团队结构指标
   - 管理团队配置
   - 运营团队配置
   - 工程团队配置
   - 客服团队配置
   - 营销团队配置
   - 财务团队配置

3. 人员效率指标
   - 人均管理房间数
   - 人均收入贡献
   - 人均成本控制
   - 团队效率等级
   - 人员配置合理性

4. 团队建设指标
   - 团队活动次数
   - 培训活动参与率
   - 员工满意度
   - 团队凝聚力得分
   - 人均活动成本

5. 绩效管理指标
   - 绩效目标完成率
   - 培训投入产出比
   - 员工成长指标
   - 激励机制效果
   - 人才保留率
"""

import pandas as pd
import numpy as np
from datetime import datetime

class TeamHRAnalysis:
    def __init__(self, data_file, target_month="Jan-25"):
        """初始化团队与人力资源分析"""
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
    
    def get_hr_data(self):
        """获取人力资源数据"""
        hr_data = {}
        
        # 获取FTE数据
        fte_categories = [
            ('计划FTE总数', 'planned_fte'),
            ('当前FTE数', 'current_fte'),
            ('管理团队FTE数', 'management_fte'),
            ('运营团队FTE数', 'operations_fte'),
            ('工程团队FTE数', 'engineering_fte'),
            ('客服团队FTE数', 'service_fte'),
            ('营销团队FTE数', 'marketing_fte'),
            ('财务团队FTE数', 'finance_fte')
        ]
        
        for category, key in fte_categories:
            row = self.target_data[self.target_data['category'] == category]
            if not row.empty:
                try:
                    hr_data[key] = float(row.iloc[0]['value'])
                except (ValueError, TypeError):
                    hr_data[key] = 0
        
        # 获取编制完成情况
        completion_row = self.target_data[self.target_data['category'] == '编制完成情况']
        if not completion_row.empty:
            try:
                hr_data['completion_rate'] = float(completion_row.iloc[0]['value'])
            except (ValueError, TypeError):
                hr_data['completion_rate'] = 0
        
        return hr_data
    
    def get_team_activities_data(self):
        """获取团队活动数据"""
        activities_data = {}
        
        # 获取团队活动数据
        activity_categories = [
            ('团队生日庆祝活动次数', 'birthday_activities'),
            ('团队建设活动次数', 'teambuilding_activities'),
            ('团队培训活动次数', 'training_activities'),
            ('团队活动总费用', 'total_activity_cost')
        ]
        
        for category, key in activity_categories:
            row = self.target_data[self.target_data['category'] == category]
            if not row.empty:
                try:
                    activities_data[key] = float(row.iloc[0]['value'])
                except (ValueError, TypeError):
                    activities_data[key] = 0
        
        # 计算总活动次数
        activities_data['total_activities'] = (activities_data.get('birthday_activities', 0) + 
                                             activities_data.get('teambuilding_activities', 0) + 
                                             activities_data.get('training_activities', 0))
        
        return activities_data
    
    def get_operational_data(self):
        """获取运营数据"""
        operational_data = {}
        
        # 获取运营和收入数据
        categories = [
            ('项目房间总间数', 'total_rooms'),
            ('经营收入(含税)', 'revenue'),
            ('运营费用', 'operational_expense')
        ]
        
        for category, key in categories:
            row = self.target_data[self.target_data['category'] == category]
            if not row.empty:
                try:
                    operational_data[key] = float(row.iloc[0]['value'])
                except (ValueError, TypeError):
                    operational_data[key] = 0
        
        return operational_data
    
    def calculate_hr_metrics(self, hr_data, operational_data):
        """计算人力资源指标"""
        metrics = {}
        
        planned_fte = hr_data.get('planned_fte', 0)
        current_fte = hr_data.get('current_fte', 0)
        total_rooms = operational_data.get('total_rooms', 894)
        revenue = operational_data.get('revenue', 0)
        
        # 编制完成率
        if planned_fte > 0:
            metrics['completion_rate'] = (current_fte / planned_fte) * 100
        else:
            metrics['completion_rate'] = 0
        
        # 人均管理房间数
        if current_fte > 0:
            metrics['rooms_per_person'] = total_rooms / current_fte
        else:
            metrics['rooms_per_person'] = 0
        
        # 人均效率（人均收入）
        if current_fte > 0:
            metrics['revenue_per_person'] = revenue / current_fte
        else:
            metrics['revenue_per_person'] = 0
        
        # 团队结构分析
        team_structure = {}
        team_keys = ['management_fte', 'operations_fte', 'engineering_fte', 'service_fte', 'marketing_fte', 'finance_fte']
        team_names = ['管理团队', '运营团队', '工程团队', '客服团队', '营销团队', '财务团队']
        
        for key, name in zip(team_keys, team_names):
            if key in hr_data and current_fte > 0:
                team_structure[name] = (hr_data[key] / current_fte) * 100
            else:
                team_structure[name] = 0
        
        metrics['team_structure'] = team_structure
        
        # 人员配置合理性评分
        metrics['staffing_rationality_score'] = self.calculate_staffing_rationality_score(metrics, hr_data)
        
        return metrics
    
    def calculate_staffing_rationality_score(self, metrics, hr_data):
        """计算人员配置合理性得分"""
        score = 0
        
        # 编制完成率得分
        completion_rate = metrics.get('completion_rate', 0)
        if completion_rate >= 90:
            score += 30
        elif completion_rate >= 80:
            score += 25
        elif completion_rate >= 70:
            score += 20
        else:
            score += 10
        
        # 人均效率得分
        rooms_per_person = metrics.get('rooms_per_person', 0)
        if 30 <= rooms_per_person <= 50:
            score += 30
        elif 20 <= rooms_per_person <= 60:
            score += 25
        else:
            score += 15
        
        # 团队结构合理性得分
        current_fte = hr_data.get('current_fte', 0)
        if current_fte > 0:
            management_ratio = hr_data.get('management_fte', 0) / current_fte
            if 0.1 <= management_ratio <= 0.2:  # 管理层占比10-20%较为合理
                score += 40
            else:
                score += 20
        else:
            score += 20
        
        return score
    
    def calculate_team_activities_metrics(self, activities_data, hr_data):
        """计算团队活动指标"""
        metrics = {}
        
        current_fte = hr_data.get('current_fte', 0)
        total_activities = activities_data.get('total_activities', 0)
        total_cost = activities_data.get('total_activity_cost', 0)
        
        # 人均活动次数
        if current_fte > 0:
            metrics['activities_per_person'] = total_activities / current_fte
        else:
            metrics['activities_per_person'] = 0
        
        # 人均活动成本
        if current_fte > 0:
            metrics['cost_per_person'] = total_cost / current_fte
        else:
            metrics['cost_per_person'] = 0
        
        # 活动类型分布
        activity_types = {
            '生日庆祝': activities_data.get('birthday_activities', 0),
            '团队建设': activities_data.get('teambuilding_activities', 0),
            '培训活动': activities_data.get('training_activities', 0)
        }
        
        if total_activities > 0:
            metrics['activity_distribution'] = {k: (v / total_activities) * 100 for k, v in activity_types.items()}
        else:
            metrics['activity_distribution'] = activity_types
        
        # 团队凝聚力评分
        metrics['team_cohesion_score'] = self.calculate_team_cohesion_score(metrics)
        
        return metrics
    
    def calculate_team_cohesion_score(self, metrics):
        """计算团队凝聚力得分"""
        score = 0
        
        # 人均活动次数得分
        activities_per_person = metrics.get('activities_per_person', 0)
        if activities_per_person >= 1:
            score += 40
        elif activities_per_person >= 0.5:
            score += 30
        else:
            score += 15
        
        # 活动类型多样性得分
        activity_distribution = metrics.get('activity_distribution', {})
        activity_types = sum(1 for v in activity_distribution.values() if v > 0)
        
        if activity_types >= 3:
            score += 30
        elif activity_types >= 2:
            score += 20
        else:
            score += 10
        
        # 成本效益得分
        cost_per_person = metrics.get('cost_per_person', 0)
        if 100 <= cost_per_person <= 500:
            score += 30
        elif cost_per_person <= 1000:
            score += 20
        else:
            score += 10
        
        return score
    
    def analyze_team_efficiency(self, hr_data, operational_data):
        """分析团队效率"""
        analysis = {}
        
        current_fte = hr_data.get('current_fte', 0)
        revenue = operational_data.get('revenue', 0)
        operational_expense = operational_data.get('operational_expense', 0)
        
        # 人均营收贡献
        if current_fte > 0:
            analysis['revenue_contribution_per_person'] = revenue / current_fte
        else:
            analysis['revenue_contribution_per_person'] = 0
        
        # 人均成本控制
        if current_fte > 0:
            analysis['cost_control_per_person'] = operational_expense / current_fte
        else:
            analysis['cost_control_per_person'] = 0
        
        # 团队效率等级
        revenue_per_person = analysis['revenue_contribution_per_person']
        if revenue_per_person >= 100000:
            analysis['efficiency_level'] = '高效'
        elif revenue_per_person >= 50000:
            analysis['efficiency_level'] = '中等'
        else:
            analysis['efficiency_level'] = '待提升'
        
        return analysis
    
    def generate_hr_recommendations(self, hr_metrics, activities_metrics, efficiency_analysis):
        """生成人力资源建议"""
        recommendations = []
        
        # 基于编制完成率的建议
        completion_rate = hr_metrics.get('completion_rate', 0)
        if completion_rate < 80:
            recommendations.append("编制完成率较低，建议加快人员招聘和培训")
        elif completion_rate > 100:
            recommendations.append("人员编制超配，建议优化人员结构")
        
        # 基于人均效率的建议
        rooms_per_person = hr_metrics.get('rooms_per_person', 0)
        if rooms_per_person > 60:
            recommendations.append("人均管理房间数过多，建议增加人员配置")
        elif rooms_per_person < 20:
            recommendations.append("人均管理房间数过少，建议优化工作分配")
        
        # 基于团队活动的建议
        activities_per_person = activities_metrics.get('activities_per_person', 0)
        if activities_per_person < 0.5:
            recommendations.append("团队活动较少，建议增加团队建设活动")
        
        # 基于效率等级的建议
        efficiency_level = efficiency_analysis.get('efficiency_level', '待提升')
        if efficiency_level == '待提升':
            recommendations.append("团队效率有待提升，建议加强培训和管理")
        
        # 通用建议
        recommendations.append("建议建立完善的绩效考核体系")
        recommendations.append("可考虑引入员工激励和晋升机制")
        
        return recommendations
    
    def run_analysis(self):
        """运行完整分析"""
        print("=" * 60)
        print("北京中天创业园团队与人力资源分析")
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
        hr_data = self.get_hr_data()
        activities_data = self.get_team_activities_data()
        operational_data = self.get_operational_data()
        
        print("👥 人力资源概况")
        print("-" * 40)
        print(f"计划FTE总数: {hr_data.get('planned_fte', 0)} 人")
        print(f"当前FTE数: {hr_data.get('current_fte', 0)} 人")
        print(f"编制完成率: {hr_data.get('completion_rate', 0):.1f}%")
        print()
        
        print("🏢 团队结构分布")
        print("-" * 40)
        team_structure = {
            '管理团队': hr_data.get('management_fte', 0),
            '运营团队': hr_data.get('operations_fte', 0),
            '工程团队': hr_data.get('engineering_fte', 0),
            '客服团队': hr_data.get('service_fte', 0),
            '营销团队': hr_data.get('marketing_fte', 0),
            '财务团队': hr_data.get('finance_fte', 0)
        }
        
        current_fte = hr_data.get('current_fte', 0)
        for team, count in team_structure.items():
            if current_fte > 0:
                percentage = (count / current_fte) * 100
                print(f"{team}: {count} 人 ({percentage:.1f}%)")
            else:
                print(f"{team}: {count} 人")
        print()
        
        print("🎉 团队活动情况")
        print("-" * 40)
        print(f"生日庆祝活动: {activities_data.get('birthday_activities', 0)} 次")
        print(f"团队建设活动: {activities_data.get('teambuilding_activities', 0)} 次")
        print(f"培训活动: {activities_data.get('training_activities', 0)} 次")
        print(f"活动总费用: {activities_data.get('total_activity_cost', 0):.0f} 元")
        print()
        
        # 计算指标
        hr_metrics = self.calculate_hr_metrics(hr_data, operational_data)
        activities_metrics = self.calculate_team_activities_metrics(activities_data, hr_data)
        efficiency_analysis = self.analyze_team_efficiency(hr_data, operational_data)
        
        print("📊 人力资源指标")
        print("-" * 40)
        print(f"编制完成率: {hr_metrics['completion_rate']:.1f}%")
        print(f"人均管理房间数: {hr_metrics['rooms_per_person']:.1f} 间/人")
        print(f"人均收入贡献: {hr_metrics['revenue_per_person']:.0f} 元/人")
        print(f"人员配置合理性得分: {hr_metrics['staffing_rationality_score']:.1f}/100")
        print()
        
        print("🎯 团队活动指标")
        print("-" * 40)
        print(f"人均活动次数: {activities_metrics['activities_per_person']:.2f} 次/人")
        print(f"人均活动成本: {activities_metrics['cost_per_person']:.0f} 元/人")
        print(f"团队凝聚力得分: {activities_metrics['team_cohesion_score']:.1f}/100")
        print()
        
        print("⚡ 团队效率分析")
        print("-" * 40)
        print(f"人均营收贡献: {efficiency_analysis['revenue_contribution_per_person']:.0f} 元/人")
        print(f"人均成本控制: {efficiency_analysis['cost_control_per_person']:.0f} 元/人")
        print(f"效率等级: {efficiency_analysis['efficiency_level']}")
        print()
        
        # 生成建议
        recommendations = self.generate_hr_recommendations(hr_metrics, activities_metrics, efficiency_analysis)
        
        print("💡 改进建议")
        print("-" * 40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print()
        
        # 评估结果
        print("📊 综合评估")
        print("-" * 40)
        
        # 计算综合得分
        hr_score = hr_metrics['staffing_rationality_score'] * 0.4
        activity_score = activities_metrics['team_cohesion_score'] * 0.3
        efficiency_score = 50 if efficiency_analysis['efficiency_level'] == '高效' else (30 if efficiency_analysis['efficiency_level'] == '中等' else 10)
        
        total_score = hr_score + activity_score + efficiency_score
        
        print(f"人力资源配置得分: {hr_score:.1f}/40")
        print(f"团队凝聚力得分: {activity_score:.1f}/30")
        print(f"运营效率得分: {efficiency_score:.1f}/30")
        print(f"综合得分: {total_score:.1f}/100")
        print()
        
        # 评估等级
        if total_score >= 80:
            grade = "优秀"
            assessment = "团队与人力资源管理优秀，继续保持"
        elif total_score >= 60:
            grade = "良好"
            assessment = "团队与人力资源管理良好，有优化空间"
        elif total_score >= 40:
            grade = "一般"
            assessment = "团队与人力资源管理一般，需要改进"
        else:
            grade = "需改进"
            assessment = "团队与人力资源管理不佳，急需改进"
        
        print(f"评估等级: {grade}")
        print(f"综合评价: {assessment}")
        print()
        
        # 存储结果
        self.results['hr_data'] = hr_data
        self.results['activities_data'] = activities_data
        self.results['hr_metrics'] = hr_metrics
        self.results['activities_metrics'] = activities_metrics
        self.results['efficiency_analysis'] = efficiency_analysis
        self.results['recommendations'] = recommendations
        self.results['total_score'] = total_score
        self.results['grade'] = grade
        self.results['assessment'] = assessment
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print("✅ 团队与人力资源分析完成")
        return True

    def output_results_to_file(self):
        """将分析结果输出"""
        f = []

        f.append(f"北京中天创业园团队与人力资源分析报告\n")
        f.append(f"分析月份: {self.target_month}\n")
        f.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


        # 人力资源概况
        f.append("1. 人力资源概况\n")

        if 'hr_data' in self.results:
            hr_data = self.results['hr_data']
            f.append(f"  计划FTE总数: {hr_data.get('planned_fte', 0)} 人\n")
            f.append(f"  当前FTE数: {hr_data.get('current_fte', 0)} 人\n")
            f.append(f"  编制完成率: {hr_data.get('completion_rate', 0):.1f}%\n")
        f.append("\n")

        # 团队结构分布
        f.append("2. 团队结构分布\n")

        if 'hr_data' in self.results:
            hr_data = self.results['hr_data']
            current_fte = hr_data.get('current_fte', 0)
            team_structure = {
                '管理团队': hr_data.get('management_fte', 0),
                '运营团队': hr_data.get('operations_fte', 0),
                '工程团队': hr_data.get('engineering_fte', 0),
                '客服团队': hr_data.get('service_fte', 0),
                '营销团队': hr_data.get('marketing_fte', 0),
                '财务团队': hr_data.get('finance_fte', 0)
            }
            for team, count in team_structure.items():
                if current_fte > 0:
                    percentage = (count / current_fte) * 100
                    f.append(f"  {team}: {count} 人 ({percentage:.1f}%)\n")
                else:
                    f.append(f"  {team}: {count} 人\n")
        f.append("\n")

        # 团队活动情况
        f.append("3. 团队活动情况\n")

        if 'activities_data' in self.results:
            activities_data = self.results['activities_data']
            f.append(f"  生日庆祝活动: {activities_data.get('birthday_activities', 0)} 次\n")
            f.append(f"  团队建设活动: {activities_data.get('teambuilding_activities', 0)} 次\n")
            f.append(f"  培训活动: {activities_data.get('training_activities', 0)} 次\n")
            f.append(f"  活动总费用: {activities_data.get('total_activity_cost', 0):.0f} 元\n")
        f.append("\n")

        # 人力资源指标
        f.append("4. 人力资源指标\n")

        if 'hr_metrics' in self.results:
            hr_metrics = self.results['hr_metrics']
            f.append(f"  编制完成率: {hr_metrics['completion_rate']:.1f}%\n")
            f.append(f"  人均管理房间数: {hr_metrics['rooms_per_person']:.1f} 间/人\n")
            f.append(f"  人均收入贡献: {hr_metrics['revenue_per_person']:.0f} 元/人\n")
            f.append(f"  人员配置合理性得分: {hr_metrics['staffing_rationality_score']:.1f}/100\n")
        f.append("\n")

        # 团队活动指标
        f.append("5. 团队活动指标\n")

        if 'activities_metrics' in self.results:
            activities_metrics = self.results['activities_metrics']
            f.append(f"  人均活动次数: {activities_metrics['activities_per_person']:.2f} 次/人\n")
            f.append(f"  人均活动成本: {activities_metrics['cost_per_person']:.0f} 元/人\n")
            f.append(f"  团队凝聚力得分: {activities_metrics['team_cohesion_score']:.1f}/100\n")
        f.append("\n")

        # 团队效率分析
        f.append("6. 团队效率分析\n")

        if 'efficiency_analysis' in self.results:
            efficiency_analysis = self.results['efficiency_analysis']
            f.append(f"  人均营收贡献: {efficiency_analysis['revenue_contribution_per_person']:.0f} 元/人\n")
            f.append(f"  人均成本控制: {efficiency_analysis['cost_control_per_person']:.0f} 元/人\n")
            f.append(f"  效率等级: {efficiency_analysis['efficiency_level']}\n")
        f.append("\n")

        # 改进建议
        f.append("7. 改进建议\n")

        if 'recommendations' in self.results:
            for i, rec in enumerate(self.results['recommendations'], 1):
                f.append(f"  {i}. {rec}\n")
        f.append("\n")

        # 综合评估
        f.append("8. 综合评估\n")

        if 'total_score' in self.results:
            hr_score = self.results['hr_metrics']['staffing_rationality_score'] * 0.4
            activity_score = self.results['activities_metrics']['team_cohesion_score'] * 0.3
            efficiency_score = 50 if self.results['efficiency_analysis']['efficiency_level'] == '高效' else (30 if self.results['efficiency_analysis']['efficiency_level'] == '中等' else 10)

            f.append(f"  人力资源配置得分: {hr_score:.1f}/40\n")
            f.append(f"  团队凝聚力得分: {activity_score:.1f}/30\n")
            f.append(f"  运营效率得分: {efficiency_score:.1f}/30\n")
            f.append(f"  综合得分: {self.results['total_score']:.1f}/100\n")
            f.append(f"  评估等级: {self.results['grade']}\n")
            f.append(f"  综合评价: {self.results['assessment']}\n")
        f.append("\n")

        # 分析信息
        f.append("9. 分析信息\n")

        f.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.append("  数据来源: " + self.data_file + "\n")
        f.append("  分析模块: 团队与人力资源分析\n")
        f.append("\n")

        f.append("说明:\n")
        f.append("- 本报告基于月度团队与人力资源数据生成\n")
        f.append("- 人数单位为人，金额单位为元\n")
        f.append("- 比率和百分比数据已标注单位\n")
        f.append("- 详细分析方法请参考相关文档\n")

        return f


def main():
    """主函数"""
    data_file = "北京中天创业园_月度数据表_补充版.csv"
    target_month = "Jan-25"
    
    analyzer = TeamHRAnalysis(data_file, target_month)
    analyzer.run_analysis()

    report_string = analyzer.output_results_to_file()
    print(report_string)

if __name__ == "__main__":
    main()