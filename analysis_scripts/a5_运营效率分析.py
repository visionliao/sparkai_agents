#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运营效率分析脚本
分析运营指标、维护服务等运营效率相关指标

统计项目:
1. 运营效率指标
   - 运营GOP（毛利润）
   - 运营NOI率（净运营收入率）
   - GOP率（毛利润率）
   - 税负率
   - 管理费率
   - 运营盈利状态评估

2. 维护服务指标
   - 服务请求数
   - 房源整备数
   - 平均维修响应时间
   - 维修完成率
   - 响应效率
   - 服务质量评分

3. 成本控制指标
   - 运营费用占比
   - 人力成本效率
   - 能耗成本控制
   - 维修成本分析

4. 服务质量指标
   - 客户满意度
   - 投诉处理时效
   - 服务达标率
   - 品质检查结果

5. 资源利用指标
   - 房间使用率
   - 设施使用效率
   - 公共区域利用率
   - 资源配置合理性
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class OperationalEfficiencyAnalysis:
    def __init__(self, data_file):
        """初始化运营效率分析类"""
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
    
    def operational_metrics_analysis(self, month):
        """运营指标分析"""
        print(f"\n{'='*50}")
        print(f"运营指标分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取运营指标相关数据
        metrics_indicators = {
            '运营GOP': month_data[month_data['指标'] == '运营GOP'],
            '运营NOI率': month_data[month_data['指标'] == '运营NOI率'],
            '经营税金': month_data[month_data['指标'] == '经营税金'],
            '增值税净额': month_data[month_data['指标'] == '增值税净额'],
            '房产税': month_data[month_data['指标'] == '房产税'],
            '土地使用税': month_data[month_data['指标'] == '土地使用税'],
            '附加税': month_data[month_data['指标'] == '附加税'],
            '印花税': month_data[month_data['指标'] == '印花税'],
            '委托管理费': month_data[month_data['指标'] == '委托管理费']
        }
        
        print("运营指标数据:")
        for key, value in metrics_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '率' in key and '%' in str(val):
                    print(f"  {key}: {val}")
                else:
                    print(f"  {key}: {val:,.2f} 元")
        
        # 计算运营指标分析
        operational_results = {}
        try:
            gop = metrics_indicators['运营GOP']['数值'].iloc[0]
            noi_rate = metrics_indicators['运营NOI率']['数值'].iloc[0]
            tax = metrics_indicators['经营税金']['数值'].iloc[0]
            management_fee = metrics_indicators['委托管理费']['数值'].iloc[0]
            
            # 获取总收入和费用
            total_income = month_data[month_data['指标'] == '经营收入(含税)']['数值'].iloc[0]
            operating_expense = month_data[month_data['指标'] == '运营费用']['数值'].iloc[0]
            
            # 计算比率
            gop_rate = (gop/total_income*100) if total_income > 0 else 0
            tax_rate = (tax/total_income*100) if total_income > 0 else 0
            management_rate = (management_fee/total_income*100) if total_income > 0 else 0
            
            operational_results['total_income'] = total_income
            operational_results['operating_expense'] = operating_expense
            operational_results['gop'] = gop
            operational_results['gop_rate'] = gop_rate
            operational_results['noi_rate'] = noi_rate
            operational_results['tax'] = tax
            operational_results['tax_rate'] = tax_rate
            operational_results['management_fee'] = management_fee
            operational_results['management_rate'] = management_rate
            
            print(f"\n运营效率分析:")
            print(f"  总收入: {total_income:,.2f} 元")
            print(f"  运营费用: {operating_expense:,.2f} 元")
            print(f"  运营GOP: {gop:,.2f} 元")
            print(f"  GOP率: {gop_rate:.2f}%")
            print(f"  运营NOI率: {noi_rate:.2f}%")
            print(f"  经营税金: {tax:,.2f} 元")
            print(f"  税负率: {tax_rate:.2f}%")
            print(f"  委托管理费: {management_fee:,.2f} 元")
            print(f"  管理费率: {management_rate:.2f}%")
            
            # 运营效率评估
            if gop > 0:
                print(f"  运营盈利状态: 盈利")
                if gop_rate > 30:
                    print("  运营效率评估: 优秀 (>30%)")
                elif gop_rate > 15:
                    print("  运营效率评估: 良好 (15-30%)")
                else:
                    print("  运营效率评估: 一般 (<15%)")
            else:
                print(f"  运营盈利状态: 亏损")
                print("  运营效率评估: 需改进")
                
        except Exception as e:
            print(f"  运营指标分析错误: {e}")
        
        self.results['operational'] = operational_results
    
    def maintenance_service_analysis(self, month):
        """维护服务分析"""
        print(f"\n{'='*50}")
        print(f"维护服务分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取维护服务相关数据
        maintenance_indicators = {
            '当期处理服务请求数': month_data[month_data['指标'] == '当期处理服务请求数'],
            '当期完成待租房源整备数': month_data[month_data['指标'] == '当期完成待租房源整备数'],
            '平均维修响应时间': month_data[month_data['指标'] == '平均维修响应时间'],
            '维修完成率': month_data[month_data['指标'] == '维修完成率']
        }
        
        print("维护服务数据:")
        for key, value in maintenance_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '时间' in key:
                    print(f"  {key}: {val} 小时")
                elif '率' in key:
                    print(f"  {key}: {val}%")
                elif '数' in key:
                    print(f"  {key}: {val} 次")
                else:
                    print(f"  {key}: {val} 间")
        
        # 计算维护服务分析
        maintenance_results = {}
        try:
            service_requests = maintenance_indicators['当期处理服务请求数']['数值'].iloc[0]
            room_preparation = maintenance_indicators['当期完成待租房源整备数']['数值'].iloc[0]
            response_time = maintenance_indicators['平均维修响应时间']['数值'].iloc[0]
            completion_rate = maintenance_indicators['维修完成率']['数值'].iloc[0] / 100
            
            # 服务效率计算
            response_efficiency = 1 / response_time if response_time > 0 else 0
            service_quality_score = completion_rate * response_efficiency * 100
            
            maintenance_results['service_requests'] = service_requests
            maintenance_results['room_preparation'] = room_preparation
            maintenance_results['response_time'] = response_time
            maintenance_results['completion_rate'] = completion_rate
            maintenance_results['response_efficiency'] = response_efficiency
            maintenance_results['service_quality_score'] = service_quality_score
            
            print(f"\n维护服务分析:")
            print(f"  处理服务请求数: {service_requests} 次")
            print(f"  完成待租房源整备数: {room_preparation} 间")
            print(f"  平均维修响应时间: {response_time} 小时")
            print(f"  维修完成率: {completion_rate:.2%}")
            
            print(f"  响应效率: {response_efficiency:.3f} (次/小时)")
            print(f"  服务质量评分: {service_quality_score:.2f}")
            
            # 服务质量评估
            if completion_rate >= 0.95 and response_time <= 2:
                print("  服务质量评估: 优秀")
            elif completion_rate >= 0.90 and response_time <= 3:
                print("  服务质量评估: 良好")
            elif completion_rate >= 0.85 and response_time <= 4:
                print("  服务质量评估: 一般")
            else:
                print("  服务质量评估: 需改进")
            
            # 工作负载分析
            if room_preparation > 0:
                prep_per_request = room_preparation / service_requests
                print(f"  每个服务请求对应的房源整备数: {prep_per_request:.2f} 间/次")
                
        except Exception as e:
            print(f"  维护服务分析错误: {e}")
        
        self.results['maintenance'] = maintenance_results
    
    def analyze(self, month):
        """执行完整的运营效率分析"""
        print(f"\n开始运营效率分析 - {month}")
        print("="*60)
        
        self.operational_metrics_analysis(month)
        self.maintenance_service_analysis(month)
        
        # 输出结果到文件
        #self.output_results_to_file(month)
        
        print(f"\n{'='*60}")
        print("运营效率分析完成")
        print("="*60)

    def output_results_to_file(self, month):
        """将分析结果输出"""
        report = []

        report.append(f"北京中天创业园运营效率分析报告\n")
        report.append(f"分析月份: {month}\n")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 获取项目数据
        month_data = self.get_month_data(month)

        # 运营指标分析
        report.append("1. 运营指标分析\n")
        if month_data is not None and 'operational' in self.results:
            operational_data = self.results['operational']
            if 'total_income' in operational_data:
                report.append(f"  总收入: {operational_data['total_income']:,.2f}元\n")
                report.append(f"  运营费用: {operational_data['operating_expense']:,.2f}元\n")
                report.append(f"  运营GOP: {operational_data['gop']:,.2f}元\n")
                report.append(f"  GOP率: {operational_data['gop_rate']:.2f}%\n")
                report.append(f"  运营NOI率: {operational_data['noi_rate']:.2f}%\n")
                report.append(f"  经营税金: {operational_data['tax']:,.2f}元\n")
                report.append(f"  税负率: {operational_data['tax_rate']:.2f}%\n")
                report.append(f"  委托管理费: {operational_data['management_fee']:,.2f}元\n")
                report.append(f"  管理费率: {operational_data['management_rate']:.2f}%\n")

                # 运营盈利状态
                if operational_data['gop'] > 0:
                    report.append(f"  运营盈利状态: 盈利\n")
                    if operational_data['gop_rate'] > 30:
                        report.append(f"  运营效率评估: 优秀 (>30%)\n")
                    elif operational_data['gop_rate'] > 15:
                        report.append(f"  运营效率评估: 良好 (15-30%)\n")
                    else:
                        report.append(f"  运营效率评估: 一般 (<15%)\n")
                else:
                    report.append(f"  运营盈利状态: 亏损\n")
                    report.append(f"  运营效率评估: 需改进\n")
        report.append("\n")

        # 维护服务分析
        report.append("2. 维护服务分析\n")
        if month_data is not None and 'maintenance' in self.results:
            maintenance_data = self.results['maintenance']
            if 'service_requests' in maintenance_data:
                report.append(f"  处理服务请求数: {maintenance_data['service_requests']}次\n")
                report.append(f"  完成待租房源整备数: {maintenance_data['room_preparation']}间\n")
                report.append(f"  平均维修响应时间: {maintenance_data['response_time']}小时\n")
                report.append(f"  维修完成率: {maintenance_data['completion_rate']:.2%}\n")
                report.append(f"  响应效率: {maintenance_data['response_efficiency']:.3f}次/小时\n")
                report.append(f"  服务质量评分: {maintenance_data['service_quality_score']:.2f}\n")

                # 服务质量评估
                if maintenance_data['completion_rate'] >= 0.95 and maintenance_data['response_time'] <= 2:
                    report.append(f"  服务质量评估: 优秀\n")
                elif maintenance_data['completion_rate'] >= 0.90 and maintenance_data['response_time'] <= 3:
                    report.append(f"  服务质量评估: 良好\n")
                elif maintenance_data['completion_rate'] >= 0.85 and maintenance_data['response_time'] <= 4:
                    report.append(f"  服务质量评估: 一般\n")
                else:
                    report.append(f"  服务质量评估: 需改进\n")
        report.append("\n")

        # 综合评估
        report.append("3. 综合评估\n")
        report.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        report.append("  数据来源: " + self.data_file + "\n")
        report.append("  分析模块: 运营效率分析\n")
        report.append("\n")

        report.append("说明:\n")
        report.append("- 本报告基于月度运营数据生成\n")
        report.append("- 金额单位为元，时间单位为小时\n")
        report.append("- 比率和百分比数据已标注单位\n")
        report.append("- 详细分析方法请参考相关文档\n")
        
        return report

def main():
    """主函数"""
    data_file = "北京中天创业园_月度数据表_补充版.csv"
    
    # 创建分析实例
    analyzer = OperationalEfficiencyAnalysis(data_file)
    
    # 分析指定月份
    target_month = "Jan-25"  # 可以修改为任意月份
    analyzer.analyze(target_month)

    report_string = analyzer.output_results_to_file(target_month)
    print(report_string)

if __name__ == "__main__":
    main()