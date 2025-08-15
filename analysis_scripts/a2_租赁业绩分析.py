#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
租赁业绩分析脚本
分析出租率、租金、租赁漏斗等租赁业绩指标

统计项目:
1. 出租率分析
   - 整体出租率
   - 长租出租率
   - 短租出租率
   - 出租率趋势分析

2. 租金水平分析
   - 平均租金
   - 长租平均租金
   - 短租平均租金
   - 租金效率计算

3. 租赁漏斗分析
   - 咨询量统计
   - 看房量统计
   - 成交量统计
   - 各环节转化率

4. 租金回收分析
   - 租金回收率
   - 欠租金额统计
   - 收租及时率
   - 坏账风险评估

5. 租赁业绩评估
   - 租赁收入分析
   - 综合业绩评分
   - 市场竞争力分析
   - 改进建议生成
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class LeasingPerformanceAnalysis:
    def __init__(self, data_file):
        """初始化租赁业绩分析类"""
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
    
    def occupancy_analysis(self, month):
        """出租率分析"""
        print(f"\n{'='*50}")
        print(f"出租率分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取出租率相关数据
        occupancy_indicators = {
            '项目房间总间数': month_data[month_data['指标'] == '项目房间总间数'],
            '长租间数': month_data[month_data['指标'] == '长租间数'],
            '间天出租率-长租': month_data[month_data['指标'] == '间天出租率-长租'],
            '项目整体出租率': month_data[month_data['指标'] == '项目整体出租率'],
            '各户型入住率-一居室': month_data[month_data['指标'] == '各户型入住率-一居室'],
            '各户型入住率-二居室': month_data[month_data['指标'] == '各户型入住率-二居室'],
            '各户型入住率-三居室': month_data[month_data['指标'] == '各户型入住率-三居室']
        }
        
        occupancy_results = {}
        
        print("基础出租数据:")
        for key, value in occupancy_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '%' in str(val):
                    occupancy_results[key] = {'value': val, 'unit': '%'}
                    print(f"  {key}: {val}")
                else:
                    unit = '间' if '间数' in key else ''
                    occupancy_results[key] = {'value': val, 'unit': unit}
                    print(f"  {key}: {val}{unit}")
        
        # 计算出租率分析
        try:
            total_rooms = occupancy_indicators['项目房间总间数']['数值'].iloc[0]
            leased_rooms = occupancy_indicators['长租间数']['数值'].iloc[0]
            occupancy_rate = occupancy_indicators['项目整体出租率']['数值'].iloc[0]
            
            print(f"\n出租率分析:")
            print(f"  总房间数: {total_rooms} 间")
            print(f"  已出租房间: {leased_rooms} 间")
            print(f"  空置房间: {total_rooms - leased_rooms} 间")
            print(f"  整体出租率: {occupancy_rate:.2%}")
            print(f"  空置率: {(1 - occupancy_rate):.2%}")
            
            # 户型出租率分析
            one_bedroom_rate = occupancy_indicators['各户型入住率-一居室']['数值'].iloc[0] / 100
            two_bedroom_rate = occupancy_indicators['各户型入住率-二居室']['数值'].iloc[0] / 100
            three_bedroom_rate = occupancy_indicators['各户型入住率-三居室']['数值'].iloc[0] / 100
            
            print(f"  一居室出租率: {one_bedroom_rate:.2%}")
            print(f"  二居室出租率: {two_bedroom_rate:.2%}")
            print(f"  三居室出租率: {three_bedroom_rate:.2%}")
            
            # 出租率效率评估
            avg_occupancy = (one_bedroom_rate + two_bedroom_rate + three_bedroom_rate) / 3
            occupancy_results['户型平均出租率'] = {'value': avg_occupancy, 'unit': 'ratio'}
            print(f"  户型平均出租率: {avg_occupancy:.2%}")
            
            if avg_occupancy > 0.8:
                evaluation = "优秀 (>80%)"
            elif avg_occupancy > 0.6:
                evaluation = "良好 (60-80%)"
            elif avg_occupancy > 0.4:
                evaluation = "一般 (40-60%)"
            else:
                evaluation = "需改进 (<40%)"
            
            occupancy_results['出租率评估'] = {'value': evaluation, 'unit': 'text'}
            print(f"  出租率评估: {evaluation}")
            
            # 添加计算得出的指标
            occupancy_results['空置房间数'] = {'value': total_rooms - leased_rooms, 'unit': '间'}
            occupancy_results['空置率'] = {'value': (1 - occupancy_rate), 'unit': 'ratio'}
                
        except Exception as e:
            print(f"  出租率计算错误: {e}")
        
        self.results['occupancy'] = occupancy_results
    
    def rent_analysis(self, month):
        """租金分析"""
        print(f"\n{'='*50}")
        print(f"租金分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取租金相关数据
        rent_indicators = {
            '含管理费均价-长租': month_data[month_data['指标'] == '含管理费均价-长租'],
            '项目整体均价': month_data[month_data['指标'] == '项目整体均价'],
            '各户型平均租金-一居室': month_data[month_data['指标'] == '各户型平均租金-一居室'],
            '各户型平均租金-二居室': month_data[month_data['指标'] == '各户型平均租金-二居室'],
            '各户型平均租金-三居室': month_data[month_data['指标'] == '各户型平均租金-三居室'],
            '各户型租金效率-一居室': month_data[month_data['指标'] == '各户型租金效率-一居室'],
            '各户型租金效率-二居室': month_data[month_data['指标'] == '各户型租金效率-二居室'],
            '各户型租金效率-三居室': month_data[month_data['指标'] == '各户型租金效率-三居室'],
            '面价租金': month_data[month_data['指标'] == '面价租金'],
            '优惠后租金': month_data[month_data['指标'] == '优惠后租金'],
            '净租金': month_data[month_data['指标'] == '净租金']
        }
        
        rent_results = {}
        
        print("租金数据:")
        for key, value in rent_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '效率' in key:
                    rent_results[key] = {'value': val, 'unit': '元/㎡'}
                    print(f"  {key}: {val} 元/㎡")
                else:
                    rent_results[key] = {'value': val, 'unit': '元'}
                    print(f"  {key}: {val} 元")
        
        # 计算租金分析
        try:
            avg_rent = rent_indicators['项目整体均价']['数值'].iloc[0]
            one_bedroom_rent = rent_indicators['各户型平均租金-一居室']['数值'].iloc[0]
            two_bedroom_rent = rent_indicators['各户型平均租金-二居室']['数值'].iloc[0]
            three_bedroom_rent = rent_indicators['各户型平均租金-三居室']['数值'].iloc[0]
            
            face_rent = rent_indicators['面价租金']['数值'].iloc[0]
            discount_rent = rent_indicators['优惠后租金']['数值'].iloc[0]
            
            print(f"\n租金分析:")
            print(f"  项目平均租金: {avg_rent} 元")
            print(f"  一居室平均租金: {one_bedroom_rent} 元")
            print(f"  二居室平均租金: {two_bedroom_rent} 元")
            print(f"  三居室平均租金: {three_bedroom_rent} 元")
            
            # 租金梯度分析
            rent_gradient_1_2 = two_bedroom_rent / one_bedroom_rent
            rent_gradient_2_3 = three_bedroom_rent / two_bedroom_rent
            print(f"  一居室到二居室租金梯度: {rent_gradient_1_2:.2f}x")
            print(f"  二居室到三居室租金梯度: {rent_gradient_2_3:.2f}x")
            
            # 优惠幅度分析
            discount_amount = face_rent - discount_rent
            discount_rate = (discount_amount / face_rent) * 100
            print(f"  面价租金: {face_rent} 元")
            print(f"  优惠后租金: {discount_rent} 元")
            print(f"  优惠金额: {discount_amount} 元")
            print(f"  优惠幅度: {discount_rate:.2f}%")
            
            # 租金效率分析
            one_efficiency = rent_indicators['各户型租金效率-一居室']['数值'].iloc[0]
            two_efficiency = rent_indicators['各户型租金效率-二居室']['数值'].iloc[0]
            three_efficiency = rent_indicators['各户型租金效率-三居室']['数值'].iloc[0]
            
            print(f"  一居室租金效率: {one_efficiency} 元/㎡")
            print(f"  二居室租金效率: {two_efficiency} 元/㎡")
            print(f"  三居室租金效率: {three_efficiency} 元/㎡")
            
            avg_efficiency = (one_efficiency + two_efficiency + three_efficiency) / 3
            rent_results['平均租金效率'] = {'value': avg_efficiency, 'unit': '元/㎡'}
            print(f"  平均租金效率: {avg_efficiency:.2f} 元/㎡")
            
            # 添加计算得出的指标
            rent_results['一居室到二居室租金梯度'] = {'value': rent_gradient_1_2, 'unit': 'ratio'}
            rent_results['二居室到三居室租金梯度'] = {'value': rent_gradient_2_3, 'unit': 'ratio'}
            rent_results['优惠金额'] = {'value': discount_amount, 'unit': '元'}
            rent_results['优惠幅度'] = {'value': discount_rate, 'unit': '%'}
            
        except Exception as e:
            print(f"  租金分析错误: {e}")
        
        self.results['rent'] = rent_results
    
    def leasing_funnel_analysis(self, month):
        """租赁漏斗分析"""
        print(f"\n{'='*50}")
        print(f"租赁漏斗分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取租赁漏斗相关数据
        funnel_indicators = {
            '当期申请数量': month_data[month_data['指标'] == '当期申请数量'],
            '当期带看量': month_data[month_data['指标'] == '当期带看量'],
            '当期转化率': month_data[month_data['指标'] == '当期转化率'],
            '经纪人成交租赁百分比': month_data[month_data['指标'] == '经纪人成交租赁百分比'],
            '续租率': month_data[month_data['指标'] == '续租率'],
            '按租期划分申请占比-6个月以下': month_data[month_data['指标'] == '按租期划分申请占比-6个月以下'],
            '按租期划分申请占比-6-12个月': month_data[month_data['指标'] == '按租期划分申请占比-6-12个月'],
            '按租期划分申请占比-12个月以上': month_data[month_data['指标'] == '按租期划分申请占比-12个月以上']
        }
        
        funnel_results = {}
        
        print("租赁漏斗数据:")
        for key, value in funnel_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '%' in str(val):
                    funnel_results[key] = {'value': val, 'unit': '%'}
                    print(f"  {key}: {val}")
                else:
                    unit = '人' if '数量' in key else '人次' if '带看量' in key else ''
                    funnel_results[key] = {'value': val, 'unit': unit}
                    print(f"  {key}: {val}{unit}")
        
        # 计算租赁漏斗分析
        try:
            applications = funnel_indicators['当期申请数量']['数值'].iloc[0]
            viewings = funnel_indicators['当期带看量']['数值'].iloc[0]
            conversion_rate = funnel_indicators['当期转化率']['数值'].iloc[0] / 100
            broker_percentage = funnel_indicators['经纪人成交租赁百分比']['数值'].iloc[0] / 100
            
            print(f"\n租赁漏斗分析:")
            print(f"  申请数量: {applications} 人")
            print(f"  带看量: {viewings} 人次")
            print(f"  申请到带看转化率: {(viewings/applications)*100:.2f}%")
            print(f"  带看到签约转化率: {conversion_rate:.2%}")
            print(f"  整体转化率: {(viewings/applications)*conversion_rate:.2%}")
            
            # 成交分析
            estimated_deals = applications * (viewings/applications) * conversion_rate
            print(f"  预估成交数: {estimated_deals:.0f} 单")
            
            # 经纪人成交分析
            print(f"  经纪人成交占比: {broker_percentage:.2%}")
            print(f"  经纪人成交数: {estimated_deals * broker_percentage:.0f} 单")
            print(f"  非经纪人成交数: {estimated_deals * (1-broker_percentage):.0f} 单")
            
            # 租期结构分析
            short_term = funnel_indicators['按租期划分申请占比-6个月以下']['数值'].iloc[0] / 100
            medium_term = funnel_indicators['按租期划分申请占比-6-12个月']['数值'].iloc[0] / 100
            long_term = funnel_indicators['按租期划分申请占比-12个月以上']['数值'].iloc[0] / 100
            
            print(f"\n租期结构分析:")
            print(f"  短期租期(<6个月): {short_term:.2%}")
            print(f"  中期租期(6-12个月): {medium_term:.2%}")
            print(f"  长期租期(>12个月): {long_term:.2%}")
            
            # 租期稳定性评估
            stability_score = short_term * 0.2 + medium_term * 0.6 + long_term * 1.0
            funnel_results['租期稳定性评分'] = {'value': stability_score, 'unit': 'score'}
            print(f"  租期稳定性评分: {stability_score:.2f} (满分1.0)")
            
            if stability_score > 0.7:
                stability_eval = "优秀"
            elif stability_score > 0.5:
                stability_eval = "良好"
            elif stability_score > 0.3:
                stability_eval = "一般"
            else:
                stability_eval = "较差"
            
            funnel_results['租期稳定性评估'] = {'value': stability_eval, 'unit': 'text'}
            print(f"  租期稳定性: {stability_eval}")
            
            # 添加计算得出的指标
            funnel_results['申请到带看转化率'] = {'value': (viewings/applications)*100, 'unit': '%'}
            funnel_results['整体转化率'] = {'value': (viewings/applications)*conversion_rate, 'unit': 'ratio'}
            funnel_results['预估成交数'] = {'value': estimated_deals, 'unit': '单'}
            funnel_results['经纪人成交数'] = {'value': estimated_deals * broker_percentage, 'unit': '单'}
            funnel_results['非经纪人成交数'] = {'value': estimated_deals * (1-broker_percentage), 'unit': '单'}
                
        except Exception as e:
            print(f"  租赁漏斗分析错误: {e}")
        
        self.results['funnel'] = funnel_results
    
    def rental_collection_analysis(self, month):
        """租金回收分析"""
        print(f"\n{'='*50}")
        print(f"租金回收分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取租金回收相关数据
        collection_indicators = {
            '当期已收租金总额': month_data[month_data['指标'] == '当期已收租金总额'],
            '未收租金单元数': month_data[month_data['指标'] == '未收租金单元数'],
            '月度至今租金回收率': month_data[month_data['指标'] == '月度至今租金回收率'],
            '年初至今租金回收率': month_data[month_data['指标'] == '年初至今租金回收率'],
            '31-90天未收租金AR金额': month_data[month_data['指标'] == '31-90天未收租金AR金额'],
            'AR中预计可回收比例': month_data[month_data['指标'] == 'AR中预计可回收比例']
        }
        
        collection_results = {}
        
        print("租金回收数据:")
        for key, value in collection_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '%' in str(val):
                    collection_results[key] = {'value': val, 'unit': '%'}
                    print(f"  {key}: {val}")
                elif 'AR金额' in key:
                    collection_results[key] = {'value': val, 'unit': '元'}
                    print(f"  {key}: {val:,.2f} 元")
                else:
                    unit = '间' if '单元数' in key else '元'
                    collection_results[key] = {'value': val, 'unit': unit}
                    print(f"  {key}: {val}{unit}")
        
        # 计算租金回收分析
        try:
            collected_rent = collection_indicators['当期已收租金总额']['数值'].iloc[0]
            uncollected_units = collection_indicators['未收租金单元数']['数值'].iloc[0]
            monthly_collection_rate = collection_indicators['月度至今租金回收率']['数值'].iloc[0] / 100
            ytd_collection_rate = collection_indicators['年初至今租金回收率']['数值'].iloc[0] / 100
            ar_amount = collection_indicators['31-90天未收租金AR金额']['数值'].iloc[0]
            ar_recovery_rate = collection_indicators['AR中预计可回收比例']['数值'].iloc[0] / 100
            
            print(f"\n租金回收分析:")
            print(f"  已收租金总额: {collected_rent:,.2f} 元")
            print(f"  未收租金单元数: {uncollected_units} 间")
            print(f"  月度租金回收率: {monthly_collection_rate:.2%}")
            print(f"  年初至今租金回收率: {ytd_collection_rate:.2%}")
            print(f"  31-90天未收租金: {ar_amount:,.2f} 元")
            print(f"  AR预计可回收比例: {ar_recovery_rate:.2%}")
            print(f"  预计坏账金额: {ar_amount * (1-ar_recovery_rate):,.2f} 元")
            
            # 回收质量评估
            if monthly_collection_rate > 0.95:
                quality_eval = "优秀 (>95%)"
            elif monthly_collection_rate > 0.90:
                quality_eval = "良好 (90-95%)"
            elif monthly_collection_rate > 0.80:
                quality_eval = "一般 (80-90%)"
            else:
                quality_eval = "需改进 (<80%)"
            
            collection_results['回收质量评估'] = {'value': quality_eval, 'unit': 'text'}
            print(f"  回收质量评估: {quality_eval}")
            
            # 添加计算得出的指标
            collection_results['月度租金回收率_数值'] = {'value': monthly_collection_rate, 'unit': 'ratio'}
            collection_results['年初至今租金回收率_数值'] = {'value': ytd_collection_rate, 'unit': 'ratio'}
            collection_results['AR预计可回收比例_数值'] = {'value': ar_recovery_rate, 'unit': 'ratio'}
            collection_results['预计坏账金额'] = {'value': ar_amount * (1-ar_recovery_rate), 'unit': '元'}
                
        except Exception as e:
            print(f"  租金回收分析错误: {e}")
        
        self.results['collection'] = collection_results
    
    def analyze(self, month):
        """执行完整的租赁业绩分析"""
        print(f"\n开始租赁业绩分析 - {month}")
        print("="*60)
        
        self.occupancy_analysis(month)
        self.rent_analysis(month)
        self.leasing_funnel_analysis(month)
        self.rental_collection_analysis(month)
        
        # 输出结果到文件
        #self.output_results_to_file(month)
        
        print(f"\n{'='*60}")
        print("租赁业绩分析完成")
        print("="*60)

    def output_results_to_file(self, month):
        """将分析结果输出"""
        report_parts = []

        report_parts.append(f"北京中天创业园租赁业绩分析报告\n")
        report_parts.append(f"分析月份: {month}\n")
        report_parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 出租率分析结果
        if 'occupancy' in self.results:
            report_parts.append("1. 出租率分析\n")
            for key, data in self.results['occupancy'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    elif data['unit'] == 'ratio':
                        report_parts.append(f"  {key}: {data['value']:.2%}\n")
                    elif data['unit'] == 'text':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']}{data['unit']}\n")
            report_parts.append("\n")

        # 租金分析结果
        if 'rent' in self.results:
            report_parts.append("2. 租金水平分析\n")
            for key, data in self.results['rent'].items():
                if 'unit' in data:
                    if data['unit'] == '元/㎡':
                        report_parts.append(f"  {key}: {data['value']:.2f}元/㎡\n")
                    elif data['unit'] == 'ratio':
                        report_parts.append(f"  {key}: {data['value']:.2f}x\n")
                    elif data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']:.2f}%\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']:.2f}元\n")
            report_parts.append("\n")

        # 租赁漏斗分析结果
        if 'funnel' in self.results:
            report_parts.append("3. 租赁漏斗分析\n")
            for key, data in self.results['funnel'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    elif data['unit'] == 'ratio':
                        report_parts.append(f"  {key}: {data['value']:.2%}\n")
                    elif data['unit'] == 'score':
                        report_parts.append(f"  {key}: {data['value']:.2f} (满分1.0)\n")
                    elif data['unit'] == 'text':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']}{data['unit']}\n")
            report_parts.append("\n")

        # 租金回收分析结果
        if 'collection' in self.results:
            report_parts.append("4. 租金回收分析\n")
            for key, data in self.results['collection'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    elif data['unit'] == 'ratio':
                        report_parts.append(f"  {key}: {data['value']:.2%}\n")
                    elif data['unit'] == 'text':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']}{data['unit']}\n")
            report_parts.append("\n")

        # 综合评估
        report_parts.append("5. 综合评估\n")
        report_parts.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        report_parts.append("  数据来源: " + self.data_file + "\n")
        report_parts.append("  分析模块: 租赁业绩分析\n")
        report_parts.append("\n")

        report_parts.append("说明:\n")
        report_parts.append("- 本报告基于月度租赁数据生成\n")
        report_parts.append("- 金额单位为元，租金效率单位为元/㎡\n")
        report_parts.append("- 百分比数据已标注单位\n")
        report_parts.append("- 详细分析方法请参考相关文档\n")

        return report_parts


def main():
    """主函数"""
    data_file = "北京中天创业园_月度数据表_补充版.csv"
    
    # 创建分析实例
    analyzer = LeasingPerformanceAnalysis(data_file)
    
    # 获取所有月份列
    months = [col for col in analyzer.df.columns if col != 'category' and col != '单位及备注']
    print(f"可分析的月份: {months}")
    
    # 分析指定月份
    target_month = "Jan-25"  # 可以修改为任意月份
    analyzer.analyze(target_month)
    report_string = analyzer.output_results_to_file(target_month)
    print(report_string)

if __name__ == "__main__":
    main()