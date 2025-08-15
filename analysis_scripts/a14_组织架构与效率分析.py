#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组织架构与效率分析脚本
分析组织结构、人员配置和运营效率

统计项目:
1. 组织架构指标
   - 管理团队配置
   - 运营团队配置
   - 工程团队配置
   - 客服团队配置
   - 营销团队配置
   - 财务团队配置
   - 编制完成率

2. 人员配置指标
   - 计划FTE总数
   - 当前FTE总数
   - 人均管理房间数
   - 人均服务住户数
   - 人均创收能力
   - 人员成本占比

3. 组织效能指标
   - 管理跨度
   - 一线人员占比
   - 支持人员占比
   - 人均处理工单数
   - 组织结构合理性

4. 团队效率指标
   - 各团队人均效率
   - 团队成本控制
   - 团队收入贡献
   - 团队协作效果
   - 资源配置优化

5. 组织发展指标
   - 生产力趋势分析
   - 人员配置得分
   - 运营效率得分
   - 组织结构得分
   - 综合组织评级
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

from celery.bin.celery import report


class OrganizationalStructureAnalysis:
    def __init__(self, data, month):
        """初始化分析类"""
        self.data_file = data
        self.df = None
        self.analysis_month = month
        
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
    
    def analyze_organizational_structure(self, project_data):
        """分析组织架构"""
        # 组织架构数据
        organizational_structure = {
            '管理团队': {
                'planned_fte': project_data.get('管理团队计划FTE', 3),
                'current_fte': project_data.get('管理团队当前FTE', 3),
                'roles': ['总经理', '运营经理', '财务经理'],
                'responsibilities': ['战略规划', '运营管理', '财务管理']
            },
            '运营团队': {
                'planned_fte': project_data.get('运营团队计划FTE', 6),
                'current_fte': project_data.get('运营团队当前FTE', 5),
                'roles': ['运营主管', '租赁专员', '客服专员', '物业专员'],
                'responsibilities': ['日常运营', '租赁管理', '客户服务', '物业管理']
            },
            '工程团队': {
                'planned_fte': project_data.get('工程团队计划FTE', 4),
                'current_fte': project_data.get('工程团队当前FTE', 3),
                'roles': ['工程主管', '维修工程师', '设备管理员'],
                'responsibilities': ['工程管理', '维修维护', '设备管理']
            },
            '客服团队': {
                'planned_fte': project_data.get('客服团队计划FTE', 4),
                'current_fte': project_data.get('客服团队当前FTE', 3),
                'roles': ['客服主管', '前台接待', '客户关系专员'],
                'responsibilities': ['客户服务', '前台管理', '客户关系维护']
            },
            '营销团队': {
                'planned_fte': project_data.get('营销团队计划FTE', 2),
                'current_fte': project_data.get('营销团队当前FTE', 1),
                'roles': ['营销主管', '市场专员'],
                'responsibilities': ['营销策划', '市场推广']
            },
            '财务团队': {
                'planned_fte': project_data.get('财务团队计划FTE', 2),
                'current_fte': project_data.get('财务团队当前FTE', 0),
                'roles': ['财务主管', '会计'],
                'responsibilities': ['财务管理', '会计核算']
            }
        }
        
        # 计算编制完成率
        for team_name, team_data in organizational_structure.items():
            if team_data['planned_fte'] > 0:
                team_data['completion_rate'] = (team_data['current_fte'] / team_data['planned_fte']) * 100
            else:
                team_data['completion_rate'] = 0
        
        # 计算总计
        total_planned = sum(team['planned_fte'] for team in organizational_structure.values())
        total_current = sum(team['current_fte'] for team in organizational_structure.values())
        overall_completion_rate = (total_current / total_planned * 100) if total_planned > 0 else 0
        
        return {
            'organizational_structure': organizational_structure,
            'total_planned_fte': total_planned,
            'total_current_fte': total_current,
            'overall_completion_rate': overall_completion_rate
        }
    
    def analyze_staffing_efficiency(self, project_data, org_structure):
        """分析人员配置效率"""
        # 获取运营数据
        total_rooms = project_data.get('项目房间总间数', 0)
        occupied_rooms = project_data.get('长租间数', 0)
        operating_income = project_data.get('运营收入', 0)
        
        # 计算人员配置效率指标
        staffing_metrics = {
            '人均管理房间数': float(total_rooms) / float(org_structure['total_current_fte']) if float(org_structure['total_current_fte']) > 0 else 0,
            '人均服务住户数': float(occupied_rooms) / float(org_structure['total_current_fte']) if float(org_structure['total_current_fte']) > 0 else 0,
            '人均创收': float(operating_income) / float(org_structure['total_current_fte']) if float(org_structure['total_current_fte']) > 0 else 0,
            '人员成本占比': (float(project_data.get('人力成本', 0)) / float(operating_income) * 100) if float(operating_income) > 0 else 0
        }
        
        # 计算各团队效率
        team_efficiency = {}
        for team_name, team_data in org_structure['organizational_structure'].items():
            if float(team_data['current_fte']) > 0:
                team_efficiency[team_name] = {
                    'rooms_per_person': float(total_rooms) / float(team_data['current_fte']),
                    'revenue_per_person': float(operating_income) / float(team_data['current_fte']),
                    'cost_per_person': float(project_data.get('人力成本', 0)) / float(team_data['current_fte'])
                }
            else:
                team_efficiency[team_name] = {
                    'rooms_per_person': 0,
                    'revenue_per_person': 0,
                    'cost_per_person': 0
                }
        
        return {
            'staffing_metrics': staffing_metrics,
            'team_efficiency': team_efficiency
        }
    
    def analyze_organization_effectiveness(self, project_data, org_structure, staffing_efficiency):
        """分析组织效能"""
        # 组织效能指标
        effectiveness_metrics = {
            '管理跨度': float(org_structure['total_current_fte']) / float(org_structure['organizational_structure']['管理团队']['current_fte']) if float(org_structure['organizational_structure']['管理团队']['current_fte']) > 0 else 0,
            '一线人员占比': (float(org_structure['organizational_structure']['运营团队']['current_fte']) + 
                           float(org_structure['organizational_structure']['工程团队']['current_fte']) + 
                           float(org_structure['organizational_structure']['客服团队']['current_fte'])) / float(org_structure['total_current_fte']) * 100 if float(org_structure['total_current_fte']) > 0 else 0,
            '支持人员占比': (float(org_structure['organizational_structure']['营销团队']['current_fte']) + 
                           float(org_structure['organizational_structure']['财务团队']['current_fte'])) / float(org_structure['total_current_fte']) * 100 if float(org_structure['total_current_fte']) > 0 else 0,
            '人均处理工单数': float(project_data.get('PMS系统工单处理数', 0)) / float(org_structure['total_current_fte']) if float(org_structure['total_current_fte']) > 0 else 0
        }
        
        # 组织结构合理性评估
        structure_assessment = {
            '管理跨度': '合理' if 5 <= effectiveness_metrics['管理跨度'] <= 10 else '需调整',
            '一线人员比例': '合理' if 60 <= effectiveness_metrics['一线人员占比'] <= 80 else '需调整',
            '支持人员比例': '合理' if 15 <= effectiveness_metrics['支持人员占比'] <= 25 else '需调整',
            '整体结构': '合理' if all([
                5 <= effectiveness_metrics['管理跨度'] <= 10,
                60 <= effectiveness_metrics['一线人员占比'] <= 80,
                15 <= effectiveness_metrics['支持人员占比'] <= 25
            ]) else '需优化'
        }
        
        return {
            'effectiveness_metrics': effectiveness_metrics,
            'structure_assessment': structure_assessment
        }
    
    def analyze_productivity_trends(self):
        """分析生产力趋势"""
        historical_data = []
        month_columns = [col for col in self.df.columns if col not in ['category', '单位及备注']]
        
        for month in sorted(month_columns):
            month_data = self.get_project_data(month)
            if month_data is not None:
                total_fte = (float(month_data.get('管理团队当前FTE', 0)) + 
                           float(month_data.get('运营团队当前FTE', 0)) + 
                           float(month_data.get('工程团队当前FTE', 0)) + 
                           float(month_data.get('客服团队当前FTE', 0)) + 
                           float(month_data.get('营销团队当前FTE', 0)) + 
                           float(month_data.get('财务团队当前FTE', 0)))
                
                if total_fte > 0:
                    productivity_metrics = {
                        'month': month,
                        'total_fte': total_fte,
                        'revenue_per_person': float(month_data.get('运营收入', 0)) / total_fte,
                        'rooms_per_person': float(month_data.get('项目房间总间数', 0)) / total_fte,
                        'cost_per_person': float(month_data.get('人力成本', 0)) / total_fte
                    }
                    historical_data.append(productivity_metrics)
        
        # 计算趋势
        trends = {}
        if len(historical_data) >= 2:
            current = historical_data[-1]
            previous = historical_data[-2]
            
            trends['revenue_per_person'] = ((current['revenue_per_person'] - previous['revenue_per_person']) / previous['revenue_per_person'] * 100) if previous['revenue_per_person'] > 0 else 0
            trends['rooms_per_person'] = ((current['rooms_per_person'] - previous['rooms_per_person']) / previous['rooms_per_person'] * 100) if previous['rooms_per_person'] > 0 else 0
            trends['cost_per_person'] = ((current['cost_per_person'] - previous['cost_per_person']) / previous['cost_per_person'] * 100) if previous['cost_per_person'] > 0 else 0
        
        return {
            'historical_data': historical_data,
            'trends': trends
        }
    
    def generate_organization_recommendations(self, org_structure, staffing_efficiency, effectiveness_metrics, structure_assessment):
        """生成组织优化建议"""
        recommendations = []
        
        # 基于编制完成率的建议
        if org_structure['overall_completion_rate'] < 80:
            recommendations.append({
                'category': '人员配置',
                'issue': f'整体编制完成率较低({org_structure["overall_completion_rate"]:.1f}%)',
                'suggestion': '建议加强招聘力度，优先补充关键岗位人员',
                'priority': '高',
                'target_teams': self._identify_understaffed_teams(org_structure)
            })
        
        # 基于管理跨度的建议
        if effectiveness_metrics['管理跨度'] > 10:
            recommendations.append({
                'category': '管理结构',
                'issue': f'管理跨度过大({effectiveness_metrics["管理跨度"]:.1f}人)',
                'suggestion': '建议增加中层管理人员或优化管理结构',
                'priority': '中',
                'target_teams': ['管理团队']
            })
        
        # 基于人员效率的建议
        if staffing_efficiency['staffing_metrics']['人均管理房间数'] < 30:
            recommendations.append({
                'category': '人员效率',
                'issue': f'人均管理房间数较少({staffing_efficiency["staffing_metrics"]["人均管理房间数"]:.1f}间)',
                'suggestion': '建议优化工作流程，提高人均管理效率',
                'priority': '中',
                'target_teams': ['运营团队', '工程团队']
            })
        
        # 基于组织结构的建议
        if structure_assessment['整体结构'] == '需优化':
            recommendations.append({
                'category': '组织结构',
                'issue': '组织结构配置不够合理',
                'suggestion': '建议重新评估组织架构，优化人员配置比例',
                'priority': '中',
                'target_teams': ['全部团队']
            })
        
        return recommendations
    
    def _identify_understaffed_teams(self, org_structure):
        """识别人员不足的团队"""
        understaffed_teams = []
        for team_name, team_data in org_structure['organizational_structure'].items():
            if team_data['completion_rate'] < 80:
                understaffed_teams.append(team_name)
        return understaffed_teams
    
    def calculate_organization_score(self, org_structure, staffing_efficiency, effectiveness_metrics, structure_assessment):
        """计算组织管理得分"""
        # 计算各项得分
        staffing_score = 0  # 人员配置得分
        efficiency_score = 0  # 运营效率得分
        structure_score = 0  # 组织结构得分
        
        # 人员配置得分（基于编制完成率）
        staffing_score = min(org_structure['overall_completion_rate'], 100)
        
        # 运营效率得分（基于人均创收和人均管理房间数）
        revenue_per_person_score = min(staffing_efficiency['staffing_metrics']['人均创收'] / 10000 * 10, 100)  # 假设1万元/人/月为满分
        rooms_per_person_score = min(staffing_efficiency['staffing_metrics']['人均管理房间数'] / 50 * 100, 100)  # 假设50间/人为满分
        efficiency_score = (revenue_per_person_score + rooms_per_person_score) / 2
        
        # 组织结构得分（基于管理跨度和人员配置比例）
        span_score = 100 if 5 <= effectiveness_metrics['管理跨度'] <= 10 else max(0, 100 - abs(effectiveness_metrics['管理跨度'] - 7.5) * 10)
        ratio_score = 100 if structure_assessment['整体结构'] == '合理' else 70
        structure_score = (span_score + ratio_score) / 2
        
        # 计算综合得分
        comprehensive_score = (staffing_score * 0.4 + efficiency_score * 0.3 + structure_score * 0.3)
        
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
                'staffing_score': staffing_score,
                'efficiency_score': efficiency_score,
                'structure_score': structure_score
            }
        }
    
    def run_analysis(self):
        """运行分析"""
        print(f"{'='*60}")
        print(f"北京中天创业园组织架构与效率分析")
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
        
        # 分析组织架构
        org_structure = self.analyze_organizational_structure(project_data)
        
        print(f"\n🏢 组织架构分析")
        print(f"-"*40)
        print(f"计划FTE总数: {org_structure['total_planned_fte']} 人")
        print(f"当前FTE总数: {org_structure['total_current_fte']} 人")
        print(f"编制完成率: {org_structure['overall_completion_rate']:.1f}%")
        
        print(f"\n各团队编制情况:")
        for team_name, team_data in org_structure['organizational_structure'].items():
            print(f"{team_name}: {team_data['current_fte']}/{team_data['planned_fte']} 人 ({team_data['completion_rate']:.1f}%)")
        
        # 分析人员配置效率
        staffing_efficiency = self.analyze_staffing_efficiency(project_data, org_structure)
        
        print(f"\n⚡ 人员配置效率")
        print(f"-"*40)
        for metric_name, value in staffing_efficiency['staffing_metrics'].items():
            if isinstance(value, float):
                print(f"{metric_name}: {value:.2f}")
            else:
                print(f"{metric_name}: {value}")
        
        # 分析组织效能
        effectiveness_analysis = self.analyze_organization_effectiveness(project_data, org_structure, staffing_efficiency)
        
        print(f"\n📊 组织效能分析")
        print(f"-"*40)
        for metric_name, value in effectiveness_analysis['effectiveness_metrics'].items():
            if isinstance(value, float):
                print(f"{metric_name}: {value:.2f}")
            else:
                print(f"{metric_name}: {value}")
        
        print(f"\n结构评估:")
        for assessment_name, assessment in effectiveness_analysis['structure_assessment'].items():
            print(f"{assessment_name}: {assessment}")
        
        # 分析生产力趋势
        productivity_trends = self.analyze_productivity_trends()
        
        print(f"\n📈 生产力趋势")
        print(f"-"*40)
        if 'trends' in productivity_trends and productivity_trends['trends']:
            for metric_name, trend in productivity_trends['trends'].items():
                print(f"{metric_name}: {trend:+.1f}%")
        else:
            print("暂无足够数据进行趋势分析")
        
        # 计算得分
        score_results = self.calculate_organization_score(
            org_structure, staffing_efficiency, effectiveness_analysis['effectiveness_metrics'], 
            effectiveness_analysis['structure_assessment'])
        
        print(f"\n🎯 综合评估")
        print(f"-"*40)
        print(f"综合得分: {score_results['comprehensive_score']:.1f}/100")
        print(f"评估等级: {score_results['grade']}")
        print(f"人员配置得分: {score_results['detailed_scores']['staffing_score']:.1f}/100")
        print(f"运营效率得分: {score_results['detailed_scores']['efficiency_score']:.1f}/100")
        print(f"组织结构得分: {score_results['detailed_scores']['structure_score']:.1f}/100")
        
        # 生成建议
        recommendations = self.generate_organization_recommendations(
            org_structure, staffing_efficiency, effectiveness_analysis['effectiveness_metrics'], 
            effectiveness_analysis['structure_assessment'])
        
        print(f"\n💡 组织优化建议")
        print(f"-"*40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['category']}")
            print(f"   问题: {rec['issue']}")
            print(f"   建议: {rec['suggestion']}")
            if 'target_teams' in rec:
                print(f"   目标团队: {', '.join(rec['target_teams'])}")
            print()
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print(f"{'='*60}")
        print(f"分析完成！")
        print(f"{'='*60}")

    def output_results_to_file(self):
        """将分析结果输出"""
        f = []
        
        f.append(f"北京中天创业园组织架构与效率分析报告\n")
        f.append(f"分析月份: {self.analysis_month}\n")
        f.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 获取项目数据
        project_data = self.get_project_data(self.analysis_month)

        # 组织架构分析
        f.append("1. 组织架构分析\n")
        if project_data:
            org_structure = self.analyze_organizational_structure(project_data)
            f.append(f"  计划FTE总数: {org_structure['total_planned_fte']} 人\n")
            f.append(f"  当前FTE总数: {org_structure['total_current_fte']} 人\n")
            f.append(f"  编制完成率: {org_structure['overall_completion_rate']:.1f}%\n")

            f.append("\n  各团队编制情况:\n")
            for team_name, team_data in org_structure['organizational_structure'].items():
                f.append(f"  {team_name}: {team_data['current_fte']}/{team_data['planned_fte']} 人 ({team_data['completion_rate']:.1f}%)\n")
        f.append("\n")

        # 人员配置效率
        f.append("2. 人员配置效率\n")
        if project_data:
            total_rooms = float(project_data.get('项目房间总间数', 0))
            occupied_rooms = float(project_data.get('长租间数', 0))
            operating_income = float(project_data.get('运营收入', 0))

            org_structure = self.analyze_organizational_structure(project_data)
            total_fte = float(org_structure['total_current_fte'])

            if total_fte > 0:
                rooms_per_person = total_rooms / total_fte
                occupancy_per_person = occupied_rooms / total_fte
                revenue_per_person = operating_income / total_fte

                f.append(f"  人均管理房间数: {rooms_per_person:.1f} 间/人\n")
                f.append(f"  人均服务住户数: {occupancy_per_person:.1f} 人/人\n")
                f.append(f"  人均创收: {revenue_per_person:,.0f} 元/人\n")
        f.append("\n")

        # 组织效能分析
        f.append("3. 组织效能分析\n")
        if project_data:
            org_structure = self.analyze_organizational_structure(project_data)
            staffing_efficiency = self.analyze_staffing_efficiency(project_data, org_structure)
            effectiveness_analysis = self.analyze_organization_effectiveness(project_data, org_structure, staffing_efficiency)

            effectiveness_metrics = effectiveness_analysis['effectiveness_metrics']
            structure_assessment = effectiveness_analysis['structure_assessment']

            f.append(f"  管理跨度: {effectiveness_metrics['管理跨度']:.1f}\n")
            f.append(f"  一线人员占比: {effectiveness_metrics['一线人员占比']:.1f}%\n")
            f.append(f"  支持人员占比: {effectiveness_metrics['支持人员占比']:.1f}%\n")
            f.append(f"  人均处理工单数: {effectiveness_metrics['人均处理工单数']:.1f}\n")

            f.append("\n  结构评估:\n")
            for assessment_name, assessment in structure_assessment.items():
                f.append(f"  {assessment_name}: {assessment}\n")
        f.append("\n")

        # 综合评估
        f.append("4. 综合评估\n")
        f.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.append("  数据来源: " + self.data_file + "\n")
        f.append("  分析模块: 组织架构与效率分析\n")
        f.append("\n")

        f.append("说明:\n")
        f.append("- 本报告基于组织架构和效率数据生成\n")
        f.append("- 人员数量单位为人\n")
        f.append("- 效率指标已标注单位\n")
        f.append("- 详细分析方法请参考相关文档\n")

        return f
        

def main():
    """主函数"""
    data = "北京中天创业园_月度数据表_补充版.csv"
    month = "Jan-25"
    analyzer = OrganizationalStructureAnalysis(data, month)
    analyzer.run_analysis()

    report = analyzer.output_results_to_file()
    print(report)

if __name__ == "__main__":
    main()