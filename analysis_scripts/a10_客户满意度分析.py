#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户满意度分析脚本
分析北京中天创业园的客户满意度和服务质量

统计项目:
1. 满意度调研指标
   - 调研发送数
   - 调研回复数
   - 调研回复率
   - 进一步联系意愿
   - 调研覆盖面

2. 服务满意度指标
   - 客户关系满意度
   - 客房服务满意度
   - 工程服务满意度
   - IT服务满意度
   - 整体满意度评分

3. 服务质量指标
   - 服务请求数
   - 平均维修响应时间
   - 维修完成率
   - 服务响应效率
   - 服务质量指数

4. 客户行为指标
   - 活动参与率
   - 活动互动数据
   - 续租意愿
   - 推荐意愿
   - 客户粘性指数

5. 客户细分指标
   - 参与度水平分析
   - 忠诚度水平分析
   - 服务需求分析
   - 客户价值分层
   - 流失风险评估
"""

import pandas as pd
import numpy as np
from datetime import datetime

class CustomerSatisfactionAnalysis:
    def __init__(self, data, target_month):
        """初始化客户满意度分析"""
        self.data_file = data
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
    
    def get_satisfaction_data(self):
        """获取满意度数据"""
        satisfaction_data = {}
        
        # 获取满意度调研数据
        survey_categories = [
            ('调研发送数', 'surveys_sent'),
            ('调研回复数', 'surveys_responded'),
            ('同意进一步联系反馈数', 'follow_up_contacts'),
            ('客户关系满意度得分', 'relationship_satisfaction'),
            ('客房服务满意度得分', 'room_service_satisfaction'),
            ('工程服务满意度得分', 'engineering_satisfaction'),
            ('IT服务满意度得分', 'it_service_satisfaction'),
            ('住户活动参与率', 'activity_participation_rate'),
            ('住户活动互动数据', 'activity_interaction_data'),
            ('续租意愿百分比', 'renewal_intention')
        ]
        
        for category, key in survey_categories:
            row = self.target_data[self.target_data['category'] == category]
            if not row.empty:
                try:
                    satisfaction_data[key] = float(row.iloc[0]['value'])
                except (ValueError, TypeError):
                    satisfaction_data[key] = 0
        
        return satisfaction_data
    
    def get_service_data(self):
        """获取服务数据"""
        service_data = {}
        
        # 获取服务相关数据
        service_categories = [
            ('当期处理服务请求数', 'service_requests'),
            ('平均维修响应时间', 'maintenance_response_time'),
            ('维修完成率', 'maintenance_completion_rate'),
            ('在住总人数', 'total_residents'),
            ('在住总单元数', 'total_units')
        ]
        
        for category, key in service_categories:
            row = self.target_data[self.target_data['category'] == category]
            if not row.empty:
                try:
                    service_data[key] = float(row.iloc[0]['value'])
                except (ValueError, TypeError):
                    service_data[key] = 0
        
        return service_data
    
    def calculate_satisfaction_metrics(self, satisfaction_data):
        """计算满意度指标"""
        metrics = {}
        
        surveys_sent = satisfaction_data.get('surveys_sent', 0)
        surveys_responded = satisfaction_data.get('surveys_responded', 0)
        
        # 调研回复率
        if surveys_sent > 0:
            metrics['response_rate'] = (surveys_responded / surveys_sent) * 100
        else:
            metrics['response_rate'] = 0
        
        # 满意度综合评分
        satisfaction_scores = [
            satisfaction_data.get('relationship_satisfaction', 0),
            satisfaction_data.get('room_service_satisfaction', 0),
            satisfaction_data.get('engineering_satisfaction', 0),
            satisfaction_data.get('it_service_satisfaction', 0)
        ]
        
        valid_scores = [score for score in satisfaction_scores if score > 0]
        if valid_scores:
            metrics['overall_satisfaction'] = np.mean(valid_scores)
        else:
            metrics['overall_satisfaction'] = 0
        
        # 各项满意度得分
        metrics['satisfaction_breakdown'] = {
            '客户关系': satisfaction_data.get('relationship_satisfaction', 0),
            '客房服务': satisfaction_data.get('room_service_satisfaction', 0),
            '工程服务': satisfaction_data.get('engineering_satisfaction', 0),
            'IT服务': satisfaction_data.get('it_service_satisfaction', 0)
        }
        
        # 客户粘性指数
        renewal_intention = satisfaction_data.get('renewal_intention', 0)
        activity_participation = satisfaction_data.get('activity_participation_rate', 0)
        metrics['customer_loyalty_index'] = (renewal_intention + activity_participation) / 2
        
        return metrics
    
    def calculate_service_quality_metrics(self, service_data):
        """计算服务质量指标"""
        metrics = {}
        
        service_requests = service_data.get('service_requests', 0)
        response_time = service_data.get('maintenance_response_time', 0)
        completion_rate = service_data.get('maintenance_completion_rate', 0)
        
        # 服务响应效率
        if response_time > 0:
            metrics['response_efficiency'] = 1 / response_time
        else:
            metrics['response_efficiency'] = 0
        
        # 服务完成质量
        metrics['service_quality'] = completion_rate
        
        # 服务质量指数
        metrics['service_quality_index'] = (metrics['response_efficiency'] * 50 + metrics['service_quality'] * 50) / 100
        
        return metrics
    
    def analyze_customer_segments(self, satisfaction_data, service_data):
        """分析客户细分"""
        analysis = {}
        
        # 客户参与度分析
        activity_participation = satisfaction_data.get('activity_participation_rate', 0)
        if activity_participation >= 70:
            analysis['participation_level'] = '高参与度'
        elif activity_participation >= 40:
            analysis['participation_level'] = '中等参与度'
        else:
            analysis['participation_level'] = '低参与度'
        
        # 客户忠诚度分析
        renewal_intention = satisfaction_data.get('renewal_intention', 0)
        if renewal_intention >= 70:
            analysis['loyalty_level'] = '高忠诚度'
        elif renewal_intention >= 40:
            analysis['loyalty_level'] = '中等忠诚度'
        else:
            analysis['loyalty_level'] = '低忠诚度'
        
        # 服务需求分析
        service_requests = service_data.get('service_requests', 0)
        total_units = service_data.get('total_units', 1)
        
        if total_units > 0:
            requests_per_unit = service_requests / total_units
            if requests_per_unit >= 2:
                analysis['service_demand'] = '高需求'
            elif requests_per_unit >= 1:
                analysis['service_demand'] = '中等需求'
            else:
                analysis['service_demand'] = '低需求'
        else:
            analysis['service_demand'] = '未知'
        
        return analysis
    
    def generate_satisfaction_recommendations(self, satisfaction_metrics, service_metrics, customer_analysis):
        """生成满意度改进建议"""
        recommendations = []
        
        # 基于满意度的建议
        overall_satisfaction = satisfaction_metrics.get('overall_satisfaction', 0)
        if overall_satisfaction < 3.5:
            recommendations.append("整体满意度较低，建议全面审视服务质量")
        elif overall_satisfaction < 4.0:
            recommendations.append("满意度有提升空间，建议重点改进薄弱环节")
        
        # 基于调研回复率的建议
        response_rate = satisfaction_metrics.get('response_rate', 0)
        if response_rate < 30:
            recommendations.append("调研回复率较低，建议改进调研方式和激励机制")
        
        # 基于服务质量的建议
        service_quality_index = service_metrics.get('service_quality_index', 0)
        if service_quality_index < 70:
            recommendations.append("服务质量有待提升，建议加强员工培训和流程优化")
        
        # 基于客户忠诚度的建议
        loyalty_level = customer_analysis.get('loyalty_level', '低忠诚度')
        if loyalty_level == '低忠诚度':
            recommendations.append("客户忠诚度较低，建议提升客户关系管理")
        
        # 基于参与度的建议
        participation_level = customer_analysis.get('participation_level', '低参与度')
        if participation_level == '低参与度':
            recommendations.append("客户参与度较低，建议丰富活动内容和形式")
        
        # 通用建议
        recommendations.append("建议建立客户反馈快速响应机制")
        recommendations.append("可考虑引入客户忠诚度奖励计划")
        
        return recommendations
    
    def run_analysis(self):
        """运行完整分析"""
        print("=" * 60)
        print("北京中天创业园客户满意度分析")
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
        satisfaction_data = self.get_satisfaction_data()
        service_data = self.get_service_data()
        
        print("📊 满意度调研概况")
        print("-" * 40)
        print(f"调研发送数: {satisfaction_data.get('surveys_sent', 0)} 份")
        print(f"调研回复数: {satisfaction_data.get('surveys_responded', 0)} 份")
        print(f"同意进一步联系: {satisfaction_data.get('follow_up_contacts', 0)} 人")
        print()
        
        print("⭐ 满意度得分详情")
        print("-" * 40)
        satisfaction_breakdown = {
            '客户关系满意度': satisfaction_data.get('relationship_satisfaction', 0),
            '客房服务满意度': satisfaction_data.get('room_service_satisfaction', 0),
            '工程服务满意度': satisfaction_data.get('engineering_satisfaction', 0),
            'IT服务满意度': satisfaction_data.get('it_service_satisfaction', 0)
        }
        
        for service, score in satisfaction_breakdown.items():
            print(f"{service}: {score:.1f} 分")
        print()
        
        print("🎯 客户行为指标")
        print("-" * 40)
        print(f"住户活动参与率: {satisfaction_data.get('activity_participation_rate', 0):.1f}%")
        print(f"续租意愿: {satisfaction_data.get('renewal_intention', 0):.1f}%")
        print(f"住户活动互动数据: {satisfaction_data.get('activity_interaction_data', 0)}")
        print()
        
        print("🔧 服务质量指标")
        print("-" * 40)
        print(f"服务请求数: {service_data.get('service_requests', 0)} 次")
        print(f"平均维修响应时间: {service_data.get('maintenance_response_time', 0):.1f} 小时")
        print(f"维修完成率: {service_data.get('maintenance_completion_rate', 0):.1f}%")
        print()
        
        # 计算指标
        satisfaction_metrics = self.calculate_satisfaction_metrics(satisfaction_data)
        service_metrics = self.calculate_service_quality_metrics(service_data)
        customer_analysis = self.analyze_customer_segments(satisfaction_data, service_data)
        
        print("📈 满意度分析指标")
        print("-" * 40)
        print(f"调研回复率: {satisfaction_metrics['response_rate']:.1f}%")
        print(f"整体满意度: {satisfaction_metrics['overall_satisfaction']:.2f} 分")
        print(f"客户粘性指数: {satisfaction_metrics['customer_loyalty_index']:.1f}%")
        print()
        
        print("🔍 服务质量分析")
        print("-" * 40)
        print(f"服务响应效率: {service_metrics['response_efficiency']:.3f}")
        print(f"服务质量指数: {service_metrics['service_quality_index']:.1f}/100")
        print()
        
        print("👥 客户细分分析")
        print("-" * 40)
        print(f"参与度水平: {customer_analysis['participation_level']}")
        print(f"忠诚度水平: {customer_analysis['loyalty_level']}")
        print(f"服务需求: {customer_analysis['service_demand']}")
        print()
        
        # 生成建议
        recommendations = self.generate_satisfaction_recommendations(
            satisfaction_metrics, service_metrics, customer_analysis
        )
        
        print("💡 改进建议")
        print("-" * 40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print()
        
        # 评估结果
        print("📊 综合评估")
        print("-" * 40)
        
        # 计算综合得分
        satisfaction_score = (satisfaction_metrics['overall_satisfaction'] / 5) * 40
        response_score = min(satisfaction_metrics['response_rate'] / 100, 1) * 20
        loyalty_score = satisfaction_metrics['customer_loyalty_index'] * 0.2
        service_score = service_metrics['service_quality_index'] * 0.2
        
        total_score = satisfaction_score + response_score + loyalty_score + service_score
        
        print(f"满意度得分: {satisfaction_score:.1f}/40")
        print(f"调研参与得分: {response_score:.1f}/20")
        print(f"客户忠诚度得分: {loyalty_score:.1f}/20")
        print(f"服务质量得分: {service_score:.1f}/20")
        print(f"综合得分: {total_score:.1f}/100")
        print()
        
        # 评估等级
        if total_score >= 80:
            grade = "优秀"
            assessment = "客户满意度表现优秀，服务质量良好"
        elif total_score >= 60:
            grade = "良好"
            assessment = "客户满意度表现良好，有提升空间"
        elif total_score >= 40:
            grade = "一般"
            assessment = "客户满意度表现一般，需要重点改进"
        else:
            grade = "需改进"
            assessment = "客户满意度不佳，急需全面提升"
        
        print(f"评估等级: {grade}")
        print(f"综合评价: {assessment}")
        print()
        
        # 存储结果
        self.results['satisfaction_data'] = satisfaction_data
        self.results['service_data'] = service_data
        self.results['satisfaction_metrics'] = satisfaction_metrics
        self.results['service_metrics'] = service_metrics
        self.results['customer_analysis'] = customer_analysis
        self.results['recommendations'] = recommendations
        self.results['total_score'] = total_score
        self.results['grade'] = grade
        self.results['assessment'] = assessment
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print("✅ 客户满意度分析完成")
        return True

    def output_results_to_file(self):
        """将分析结果输出"""
        f = []

        f.append(f"北京中天创业园客户满意度分析报告\n")
        f.append(f"分析月份: {self.target_month}\n")
        f.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 满意度调研概况
        f.append("1. 满意度调研概况\n")
        if 'satisfaction_data' in self.results:
            satisfaction_data = self.results['satisfaction_data']
            f.append(f"  调研发送数: {satisfaction_data.get('surveys_sent', 0)} 份\n")
            f.append(f"  调研回复数: {satisfaction_data.get('surveys_responded', 0)} 份\n")
            f.append(f"  同意进一步联系: {satisfaction_data.get('follow_up_contacts', 0)} 人\n")
        f.append("\n")

        # 满意度得分详情
        f.append("2. 满意度得分详情\n")
        if 'satisfaction_data' in self.results:
            satisfaction_data = self.results['satisfaction_data']
            f.append(f"  客户关系满意度: {satisfaction_data.get('relationship_satisfaction', 0):.1f} 分\n")
            f.append(f"  客房服务满意度: {satisfaction_data.get('room_service_satisfaction', 0):.1f} 分\n")
            f.append(f"  工程服务满意度: {satisfaction_data.get('engineering_satisfaction', 0):.1f} 分\n")
            f.append(f"  IT服务满意度: {satisfaction_data.get('it_service_satisfaction', 0):.1f} 分\n")
        f.append("\n")

        # 客户行为指标
        f.append("3. 客户行为指标\n")
        if 'satisfaction_data' in self.results:
            satisfaction_data = self.results['satisfaction_data']
            f.append(f"  住户活动参与率: {satisfaction_data.get('activity_participation_rate', 0):.1f}%\n")
            f.append(f"  续租意愿: {satisfaction_data.get('renewal_intention', 0):.1f}%\n")
            f.append(f"  住户活动互动数据: {satisfaction_data.get('activity_interaction_data', 0)}\n")
        f.append("\n")

        # 服务质量指标
        f.append("4. 服务质量指标\n")
        if 'service_data' in self.results:
            service_data = self.results['service_data']
            f.append(f"  服务请求数: {service_data.get('service_requests', 0)} 次\n")
            f.append(f"  平均维修响应时间: {service_data.get('maintenance_response_time', 0):.1f} 小时\n")
            f.append(f"  维修完成率: {service_data.get('maintenance_completion_rate', 0):.1f}%\n")
        f.append("\n")

        # 满意度分析指标
        f.append("5. 满意度分析指标\n")
        if 'satisfaction_metrics' in self.results:
            satisfaction_metrics = self.results['satisfaction_metrics']
            f.append(f"  调研回复率: {satisfaction_metrics['response_rate']:.1f}%\n")
            f.append(f"  整体满意度: {satisfaction_metrics['overall_satisfaction']:.2f} 分\n")
            f.append(f"  客户粘性指数: {satisfaction_metrics['customer_loyalty_index']:.1f}%\n")
        f.append("\n")

        # 服务质量分析
        f.append("6. 服务质量分析\n")
        if 'service_metrics' in self.results:
            service_metrics = self.results['service_metrics']
            f.append(f"  服务响应效率: {service_metrics['response_efficiency']:.3f}\n")
            f.append(f"  服务质量指数: {service_metrics['service_quality_index']:.1f}/100\n")
        f.append("\n")

        # 客户细分分析
        f.append("7. 客户细分分析\n")
        if 'customer_analysis' in self.results:
            customer_analysis = self.results['customer_analysis']
            f.append(f"  参与度水平: {customer_analysis['participation_level']}\n")
            f.append(f"  忠诚度水平: {customer_analysis['loyalty_level']}\n")
            f.append(f"  服务需求: {customer_analysis['service_demand']}\n")
        f.append("\n")

        # 改进建议
        f.append("8. 改进建议\n")
        if 'recommendations' in self.results:
            for i, rec in enumerate(self.results['recommendations'], 1):
                f.append(f"  {i}. {rec}\n")
        f.append("\n")

        # 综合评估
        f.append("9. 综合评估\n")
        if 'total_score' in self.results:
            satisfaction_score = (self.results['satisfaction_metrics']['overall_satisfaction'] / 5) * 40
            response_score = min(self.results['satisfaction_metrics']['response_rate'] / 100, 1) * 20
            loyalty_score = self.results['satisfaction_metrics']['customer_loyalty_index'] * 0.2
            service_score = self.results['service_metrics']['service_quality_index'] * 0.2

            f.append(f"  满意度得分: {satisfaction_score:.1f}/40\n")
            f.append(f"  调研参与得分: {response_score:.1f}/20\n")
            f.append(f"  客户忠诚度得分: {loyalty_score:.1f}/20\n")
            f.append(f"  服务质量得分: {service_score:.1f}/20\n")
            f.append(f"  综合得分: {self.results['total_score']:.1f}/100\n")
            f.append(f"  评估等级: {self.results['grade']}\n")
            f.append(f"  综合评价: {self.results['assessment']}\n")
        f.append("\n")

        # 分析信息
        f.append("10. 分析信息\n")
        f.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.append("  数据来源: " + self.data_file + "\n")
        f.append("  分析模块: 客户满意度分析\n")
        f.append("\n")

        f.append("说明:\n")
        f.append("- 本报告基于月度客户满意度数据生成\n")
        f.append("- 满意度采用5分制，5分为最高分\n")
        f.append("- 比率和百分比数据已标注单位\n")
        f.append("- 详细分析方法请参考相关文档\n")

        return f
        

def main():
    """主函数"""
    target_month = "Jan-25"
    data = "北京中天创业园_月度数据表_补充版.csv"
    
    analyzer = CustomerSatisfactionAnalysis(data, target_month)
    analyzer.run_analysis()

    report_string = analyzer.output_results_to_file()
    print(report_string)

if __name__ == "__main__":
    main()