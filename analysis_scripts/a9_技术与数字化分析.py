#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IT系统与数字化分析脚本
分析PMS系统使用、IT项目状况等IT数字化相关指标

统计项目:
1. 系统使用指标
   - PMS系统使用率
   - 活跃用户数
   - 系统工单处理数
   - 在线支付比例
   - 系统覆盖率

2. 系统性能指标
   - 系统故障次数
   - 平均故障恢复时间
   - 系统稳定性
   - 响应时间
   - 用户满意度

3. 数字化服务指标
   - 微信小程序访客数
   - 预订看房转化率
   - 签约转化率
   - 数字化服务覆盖率
   - 租户使用率

4. 技术创新指标
   - 新技术应用情况
   - 自动化程度
   - 数据分析能力
   - 技术投入回报率
   - 数字化成熟度

5. 信息安全指标
   - 数据安全性
   - 系统合规性
   - 隐私保护措施
   - 灾备能力
   - 安全培训覆盖率
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ITDigitalAnalysis:
    def __init__(self, data_file, target_month):
        """初始化IT数字化分析类"""
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
            
    def get_month_data(self, month):
        """获取指定月份的数据"""
        if month not in self.data.columns:
            print(f"错误: 月份 '{month}' 不存在于数据中")
            return None
            
        # 获取category列和指定月份的数据
        month_data = self.data[['category', month]].copy()
        month_data.columns = ['指标', '数值']
        
        # 转换数值列为数值类型
        month_data['数值'] = pd.to_numeric(month_data['数值'], errors='coerce')
        
        return month_data.dropna()
    
    def get_pms_system_data(self):
        """获取PMS系统数据"""
        pms_data = {}
        
        # 获取PMS系统相关数据
        pms_categories = [
            ('PMS系统使用率', 'usage_rate'),
            ('PMS系统活跃用户数', 'active_users'),
            ('PMS系统工单处理数', 'work_orders'),
            ('PMS系统在线支付比例', 'online_payment_rate'),
            ('IT系统故障次数', 'failures'),
            ('IT系统平均故障恢复时间', 'recovery_time'),
            ('IT系统用户满意度', 'user_satisfaction'),
            ('数字化服务覆盖率', 'digital_coverage')
        ]
        
        for category, key in pms_categories:
            row = self.target_data[self.target_data['category'] == category]
            if not row.empty:
                try:
                    pms_data[key] = float(row.iloc[0]['value'])
                except (ValueError, TypeError):
                    pms_data[key] = 0
        
        return pms_data
    
    def get_wechat_data(self):
        """获取微信小程序数据"""
        wechat_data = {}
        
        # 获取微信小程序相关数据
        wechat_categories = [
            ('微信小程序访客数', 'visitors'),
            ('微信小程序预订看房数', 'bookings'),
            ('微信小程序签约数', 'contracts'),
            ('使用小程序租户数', 'tenant_users'),
            ('运营工单数', 'operation_orders'),
            ('住户工单数', 'resident_orders')
        ]
        
        for category, key in wechat_categories:
            row = self.target_data[self.target_data['category'] == category]
            if not row.empty:
                try:
                    wechat_data[key] = float(row.iloc[0]['value'])
                except (ValueError, TypeError):
                    wechat_data[key] = 0
        
        return wechat_data
    
    def calculate_pms_metrics(self, pms_data):
        """计算PMS系统指标"""
        metrics = {}
        
        usage_rate = pms_data.get('usage_rate', 0) / 100
        active_users = pms_data.get('active_users', 0)
        work_orders = pms_data.get('work_orders', 0)
        online_payment_rate = pms_data.get('online_payment_rate', 0) / 100
        failures = pms_data.get('failures', 0)
        recovery_time = pms_data.get('recovery_time', 0)
        user_satisfaction = pms_data.get('user_satisfaction', 0)
        digital_coverage = pms_data.get('digital_coverage', 0) / 100
        
        # 效率指标计算
        if active_users > 0:
            metrics['orders_per_user'] = work_orders / active_users
        else:
            metrics['orders_per_user'] = 0
        
        metrics['system_stability'] = 1 - (failures / 30) if failures < 30 else 0
        metrics['user_satisfaction_index'] = (user_satisfaction / 5) * 100
        metrics['digital_maturity'] = digital_coverage * usage_rate
        
        # 系统使用评估
        if usage_rate >= 0.8 and user_satisfaction >= 4.0:
            metrics['system_assessment'] = '优秀'
        elif usage_rate >= 0.6 and user_satisfaction >= 3.5:
            metrics['system_assessment'] = '良好'
        elif usage_rate >= 0.4 and user_satisfaction >= 3.0:
            metrics['system_assessment'] = '一般'
        else:
            metrics['system_assessment'] = '需改进'
        
        return metrics
    
    def calculate_wechat_metrics(self, wechat_data):
        """计算微信小程序指标"""
        metrics = {}
        
        visitors = wechat_data.get('visitors', 0)
        bookings = wechat_data.get('bookings', 0)
        contracts = wechat_data.get('contracts', 0)
        tenant_users = wechat_data.get('tenant_users', 0)
        operation_orders = wechat_data.get('operation_orders', 0)
        resident_orders = wechat_data.get('resident_orders', 0)
        
        # 转化率计算
        if visitors > 0:
            metrics['visitor_to_booking_rate'] = (bookings / visitors) * 100
            metrics['overall_conversion_rate'] = (contracts / visitors) * 100
        else:
            metrics['visitor_to_booking_rate'] = 0
            metrics['overall_conversion_rate'] = 0
        
        if bookings > 0:
            metrics['booking_to_contract_rate'] = (contracts / bookings) * 100
        else:
            metrics['booking_to_contract_rate'] = 0
        
        # 工单分析
        total_orders = operation_orders + resident_orders
        metrics['total_orders'] = total_orders
        
        if tenant_users > 0:
            metrics['orders_per_tenant'] = total_orders / tenant_users
        else:
            metrics['orders_per_tenant'] = 0
        
        # 小程序效率评估
        overall_conversion_rate = metrics.get('overall_conversion_rate', 0)
        if overall_conversion_rate > 5:
            metrics['mini_program_efficiency'] = '优秀'
        elif overall_conversion_rate > 3:
            metrics['mini_program_efficiency'] = '良好'
        elif overall_conversion_rate > 1:
            metrics['mini_program_efficiency'] = '一般'
        else:
            metrics['mini_program_efficiency'] = '需改进'
        
        return metrics
    
    def generate_recommendations(self, pms_metrics, wechat_metrics):
        """生成改进建议"""
        recommendations = []
        
        # 基于PMS系统评估的建议
        if pms_metrics.get('system_assessment') == '需改进':
            recommendations.append("PMS系统使用率较低，建议加强系统培训和推广")
        
        # 基于用户满意度的建议
        user_satisfaction_index = pms_metrics.get('user_satisfaction_index', 0)
        if user_satisfaction_index < 70:
            recommendations.append("用户满意度较低，建议优化系统功能和用户体验")
        
        # 基于系统稳定性的建议
        system_stability = pms_metrics.get('system_stability', 0)
        if system_stability < 0.9:
            recommendations.append("系统稳定性有待提升，建议加强系统维护")
        
        # 基于小程序效率的建议
        if wechat_metrics.get('mini_program_efficiency') == '需改进':
            recommendations.append("微信小程序转化率较低，建议优化小程序功能")
        
        # 基于数字化成熟度的建议
        digital_maturity = pms_metrics.get('digital_maturity', 0)
        if digital_maturity < 0.5:
            recommendations.append("数字化成熟度较低，建议加大数字化投入")
        
        # 通用建议
        recommendations.append("建议建立完善的IT运维监控体系")
        recommendations.append("可考虑引入更多智能化技术提升运营效率")
        
        return recommendations
    
    def run_analysis(self):
        """运行完整分析"""
        print("=" * 60)
        print("北京中天创业园技术与数字化分析")
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
        pms_data = self.get_pms_system_data()
        wechat_data = self.get_wechat_data()
        
        print("💻 PMS系统使用分析")
        print("-" * 40)
        print(f"系统使用率: {pms_data.get('usage_rate', 0):.1f}%")
        print(f"活跃用户数: {pms_data.get('active_users', 0)} 人")
        print(f"工单处理数: {pms_data.get('work_orders', 0)} 单")
        print(f"在线支付比例: {pms_data.get('online_payment_rate', 0):.1f}%")
        print(f"系统故障次数: {pms_data.get('failures', 0)} 次")
        print(f"平均故障恢复时间: {pms_data.get('recovery_time', 0)} 小时")
        print(f"用户满意度: {pms_data.get('user_satisfaction', 0)} 分")
        print(f"数字化服务覆盖率: {pms_data.get('digital_coverage', 0):.1f}%")
        print()
        
        print("📱 微信小程序分析")
        print("-" * 40)
        print(f"访客数: {wechat_data.get('visitors', 0)} 人")
        print(f"预订看房数: {wechat_data.get('bookings', 0)} 次")
        print(f"签约数: {wechat_data.get('contracts', 0)} 间")
        print(f"使用小程序租户数: {wechat_data.get('tenant_users', 0)} 户")
        print(f"运营工单数: {wechat_data.get('operation_orders', 0)} 单")
        print(f"住户工单数: {wechat_data.get('resident_orders', 0)} 单")
        print()
        
        # 计算指标
        pms_metrics = self.calculate_pms_metrics(pms_data)
        wechat_metrics = self.calculate_wechat_metrics(wechat_data)
        
        print("📊 PMS系统指标分析")
        print("-" * 40)
        print(f"人均工单处理数: {pms_metrics['orders_per_user']:.2f} 单/人")
        print(f"系统稳定性: {pms_metrics['system_stability']:.2%}")
        print(f"用户满意度指数: {pms_metrics['user_satisfaction_index']:.1f}%")
        print(f"数字化成熟度: {pms_metrics['digital_maturity']:.2f}")
        print(f"系统使用评估: {pms_metrics['system_assessment']}")
        print()
        
        print("📈 微信小程序指标分析")
        print("-" * 40)
        print(f"访客到预订转化率: {wechat_metrics['visitor_to_booking_rate']:.2f}%")
        print(f"预订到签约转化率: {wechat_metrics['booking_to_contract_rate']:.2f}%")
        print(f"整体转化率: {wechat_metrics['overall_conversion_rate']:.2f}%")
        print(f"总工单数: {wechat_metrics['total_orders']} 单")
        print(f"每租户平均工单数: {wechat_metrics['orders_per_tenant']:.2f} 单/户")
        print(f"小程序效率评估: {wechat_metrics['mini_program_efficiency']}")
        print()
        
        # 生成建议
        recommendations = self.generate_recommendations(pms_metrics, wechat_metrics)
        
        print("💡 改进建议")
        print("-" * 40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print()
        
        # 评估结果
        print("📊 综合评估")
        print("-" * 40)
        
        # 计算综合得分
        pms_score = pms_metrics['user_satisfaction_index'] * 0.4
        stability_score = pms_metrics['system_stability'] * 100 * 0.3
        wechat_score = min(wechat_metrics['overall_conversion_rate'] * 2, 100) * 0.3
        
        total_score = pms_score + stability_score + wechat_score
        
        print(f"PMS系统得分: {pms_score:.1f}/40")
        print(f"系统稳定性得分: {stability_score:.1f}/30")
        print(f"小程序效率得分: {wechat_score:.1f}/30")
        print(f"综合得分: {total_score:.1f}/100")
        print()
        
        # 评估等级
        if total_score >= 80:
            grade = "优秀"
            assessment = "技术与数字化表现优秀，继续保持"
        elif total_score >= 60:
            grade = "良好"
            assessment = "技术与数字化表现良好，有优化空间"
        elif total_score >= 40:
            grade = "一般"
            assessment = "技术与数字化表现一般，需要改进"
        else:
            grade = "需改进"
            assessment = "技术与数字化表现不佳，急需改进"
        
        print(f"评估等级: {grade}")
        print(f"综合评价: {assessment}")
        print()
        
        # 存储结果
        self.results['pms_data'] = pms_data
        self.results['wechat_data'] = wechat_data
        self.results['pms_metrics'] = pms_metrics
        self.results['wechat_metrics'] = wechat_metrics
        self.results['recommendations'] = recommendations
        self.results['total_score'] = total_score
        self.results['grade'] = grade
        self.results['assessment'] = assessment
        
        # 输出结果到文件
        #self.output_results_to_file()
        
        print("✅ 技术与数字化分析完成")
        return True

    def output_results_to_file(self):
        """将分析结果输出"""
        f = []

        f.append(f"北京中天创业园技术与数字化分析报告\n")
        f.append(f"分析月份: {self.target_month}\n")
        f.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # PMS系统使用分析
        f.append("1. PMS系统使用分析\n")
        if 'pms_data' in self.results:
            pms_data = self.results['pms_data']
            f.append(f"  系统使用率: {pms_data.get('usage_rate', 0):.1f}%\n")
            f.append(f"  活跃用户数: {pms_data.get('active_users', 0)} 人\n")
            f.append(f"  工单处理数: {pms_data.get('work_orders', 0)} 单\n")
            f.append(f"  在线支付比例: {pms_data.get('online_payment_rate', 0):.1f}%\n")
            f.append(f"  系统故障次数: {pms_data.get('failures', 0)} 次\n")
            f.append(f"  平均故障恢复时间: {pms_data.get('recovery_time', 0)} 小时\n")
            f.append(f"  用户满意度: {pms_data.get('user_satisfaction', 0)} 分\n")
            f.append(f"  数字化服务覆盖率: {pms_data.get('digital_coverage', 0):.1f}%\n")
        f.append("\n")

        # 微信小程序分析
        f.append("2. 微信小程序分析\n")
        if 'wechat_data' in self.results:
            wechat_data = self.results['wechat_data']
            f.append(f"  访客数: {wechat_data.get('visitors', 0)} 人\n")
            f.append(f"  预订看房数: {wechat_data.get('bookings', 0)} 次\n")
            f.append(f"  签约数: {wechat_data.get('contracts', 0)} 间\n")
            f.append(f"  使用小程序租户数: {wechat_data.get('tenant_users', 0)} 户\n")
            f.append(f"  运营工单数: {wechat_data.get('operation_orders', 0)} 单\n")
            f.append(f"  住户工单数: {wechat_data.get('resident_orders', 0)} 单\n")
        f.append("\n")

        # PMS系统指标分析
        f.append("3. PMS系统指标分析\n")
        if 'pms_metrics' in self.results:
            pms_metrics = self.results['pms_metrics']
            f.append(f"  人均工单处理数: {pms_metrics['orders_per_user']:.2f} 单/人\n")
            f.append(f"  系统稳定性: {pms_metrics['system_stability']:.2%}\n")
            f.append(f"  用户满意度指数: {pms_metrics['user_satisfaction_index']:.1f}%\n")
            f.append(f"  数字化成熟度: {pms_metrics['digital_maturity']:.2f}\n")
            f.append(f"  系统使用评估: {pms_metrics['system_assessment']}\n")
        f.append("\n")

        # 微信小程序指标分析
        f.append("4. 微信小程序指标分析\n")
        if 'wechat_metrics' in self.results:
            wechat_metrics = self.results['wechat_metrics']
            f.append(f"  访客到预订转化率: {wechat_metrics['visitor_to_booking_rate']:.2f}%\n")
            f.append(f"  预订到签约转化率: {wechat_metrics['booking_to_contract_rate']:.2f}%\n")
            f.append(f"  整体转化率: {wechat_metrics['overall_conversion_rate']:.2f}%\n")
            f.append(f"  总工单数: {wechat_metrics['total_orders']} 单\n")
            f.append(f"  每租户平均工单数: {wechat_metrics['orders_per_tenant']:.2f} 单/户\n")
            f.append(f"  小程序效率评估: {wechat_metrics['mini_program_efficiency']}\n")
        f.append("\n")

        # 改进建议
        f.append("5. 改进建议\n")
        if 'recommendations' in self.results:
            for i, rec in enumerate(self.results['recommendations'], 1):
                f.append(f"  {i}. {rec}\n")
        f.append("\n")

        # 综合评估
        f.append("6. 综合评估\n")
        if 'total_score' in self.results:
            pms_score = self.results['pms_metrics']['user_satisfaction_index'] * 0.4
            stability_score = self.results['pms_metrics']['system_stability'] * 100 * 0.3
            wechat_score = min(self.results['wechat_metrics']['overall_conversion_rate'] * 2, 100) * 0.3

            f.append(f"  PMS系统得分: {pms_score:.1f}/40\n")
            f.append(f"  系统稳定性得分: {stability_score:.1f}/30\n")
            f.append(f"  小程序效率得分: {wechat_score:.1f}/30\n")
            f.append(f"  综合得分: {self.results['total_score']:.1f}/100\n")
            f.append(f"  评估等级: {self.results['grade']}\n")
            f.append(f"  综合评价: {self.results['assessment']}\n")
        f.append("\n")

        # 分析信息
        f.append("7. 分析信息\n")
        f.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.append("  数据来源: " + self.data_file + "\n")
        f.append("  分析模块: 技术与数字化分析\n")
        f.append("\n")

        f.append("说明:\n")
        f.append("- 本报告基于月度技术与数字化数据生成\n")
        f.append("- 人数单位为人，金额单位为元\n")
        f.append("- 比率和百分比数据已标注单位\n")
        f.append("- 详细分析方法请参考相关文档\n")

        return f


def main():
    """主函数"""
    target_month = "Jan-25"
    file = "北京中天创业园_月度数据表_补充版.csv"

    analyzer = ITDigitalAnalysis(file, target_month)
    analyzer.run_analysis()

    report_string = analyzer.output_results_to_file()
    print(report_string)

if __name__ == "__main__":
    main()