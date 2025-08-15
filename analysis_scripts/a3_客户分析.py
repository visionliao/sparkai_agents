#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户分析脚本
分析客户结构、住户画像、客户满意度等客户相关指标

统计项目:
1. 客户结构分析
   - 长租客户占比
   - 短租客户占比
   - 新老客户比例
   - 客户集中度分析

2. 住户画像分析
   - 年龄分布分析
   - 性别分布分析
   - 职业分布分析
   - 收入水平分布

3. 客户行为分析
   - 平均租期分析
   - 续租率统计
   - 退租原因分析
   - 客户活跃度分析

4. 客户满意度分析
   - 满意度评分
   - 投诉处理率
   - 服务响应时间
   - 客户忠诚度评估

5. 客户价值分析
   - 客户终身价值
   - 高价值客户识别
   - 客户流失风险
   - 客户关系管理建议
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CustomerAnalysis:
    def __init__(self, data_file):
        """初始化客户分析类"""
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
    
    def customer_structure_analysis(self, month):
        """客户结构分析"""
        print(f"\n{'='*50}")
        print(f"客户结构分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取客户结构相关数据
        structure_indicators = {
            '公司客户占比': month_data[month_data['指标'] == '公司客户占比'],
            '公司客户物业管理费金额': month_data[month_data['指标'] == '公司客户物业管理费金额'],
            '个人客户物业管理费金额': month_data[month_data['指标'] == '个人客户物业管理费金额'],
            'Top1公司客户名称': month_data[month_data['指标'] == 'Top1公司客户名称'],
            'Top1公司客户租赁单元数': month_data[month_data['指标'] == 'Top1公司客户租赁单元数'],
            'Top1公司客户总收入': month_data[month_data['指标'] == 'Top1公司客户总收入'],
            'Top1公司客户平均租金': month_data[month_data['指标'] == 'Top1公司客户平均租金'],
            'Top2公司客户名称': month_data[month_data['指标'] == 'Top2公司客户名称'],
            'Top2公司客户租赁单元数': month_data[month_data['指标'] == 'Top2公司客户租赁单元数'],
            'Top2公司客户总收入': month_data[month_data['指标'] == 'Top2公司客户总收入'],
            'Top2公司客户平均租金': month_data[month_data['指标'] == 'Top2公司客户平均租金'],
            'Top3公司客户名称': month_data[month_data['指标'] == 'Top3公司客户名称'],
            'Top3公司客户租赁单元数': month_data[month_data['指标'] == 'Top3公司客户租赁单元数'],
            'Top3公司客户总收入': month_data[month_data['指标'] == 'Top3公司客户总收入'],
            'Top3公司客户平均租金': month_data[month_data['指标'] == 'Top3公司客户平均租金']
        }
        
        structure_results = {}
        
        print("客户结构数据:")
        for key, value in structure_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '名称' in key:
                    structure_results[key] = {'value': val, 'unit': 'text'}
                    print(f"  {key}: {val}")
                elif '占比' in key:
                    structure_results[key] = {'value': val, 'unit': '%'}
                    print(f"  {key}: {val}%")
                elif '金额' in key or '收入' in key:
                    structure_results[key] = {'value': val, 'unit': '元'}
                    print(f"  {key}: {val:,.2f} 元")
                elif '单元数' in key:
                    structure_results[key] = {'value': val, 'unit': '间'}
                    print(f"  {key}: {val} 间")
                else:
                    structure_results[key] = {'value': val, 'unit': ''}
                    print(f"  {key}: {val}")
        
        # 计算客户结构分析
        try:
            corporate_ratio = structure_indicators['公司客户占比']['数值'].iloc[0] / 100
            individual_ratio = 1 - corporate_ratio
            
            corporate_fee = structure_indicators['公司客户物业管理费金额']['数值'].iloc[0]
            individual_fee = structure_indicators['个人客户物业管理费金额']['数值'].iloc[0]
            total_fee = corporate_fee + individual_fee
            
            print(f"\n客户结构分析:")
            print(f"  公司客户占比: {corporate_ratio:.2%}")
            print(f"  个人客户占比: {individual_ratio:.2%}")
            print(f"  公司客户物业管理费: {corporate_fee:,.2f} 元")
            print(f"  个人客户物业管理费: {individual_fee:,.2f} 元")
            print(f"  总物业管理费: {total_fee:,.2f} 元")
            
            if total_fee > 0:
                print(f"  公司客户费用占比: {(corporate_fee/total_fee)*100:.2f}%")
                print(f"  个人客户费用占比: {(individual_fee/total_fee)*100:.2f}%")
            
            # 大客户分析
            print(f"\n大客户分析:")
            top1_units = structure_indicators['Top1公司客户租赁单元数']['数值'].iloc[0]
            top1_income = structure_indicators['Top1公司客户总收入']['数值'].iloc[0]
            top1_rent = structure_indicators['Top1公司客户平均租金']['数值'].iloc[0]
            
            print(f"  Top1客户租赁单元数: {top1_units} 间")
            print(f"  Top1客户月收入: {top1_income:,.2f} 元")
            print(f"  Top1客户平均租金: {top1_rent} 元")
            
            # 客户集中度分析
            try:
                total_income = month_data[month_data['指标'] == '经营收入(含税)']['数值'].iloc[0]
                if total_income > 0:
                    top1_concentration = (top1_income / total_income) * 100
                    print(f"  Top1客户收入集中度: {top1_concentration:.2f}%")
                    
                    if top1_concentration > 30:
                        print("  客户集中度风险: 高 (>30%)")
                    elif top1_concentration > 15:
                        print("  客户集中度风险: 中 (15-30%)")
                    else:
                        print("  客户集中度风险: 低 (<15%)")
            except:
                print("  客户集中度分析: 缺少总收入数据")
                
        except Exception as e:
            print(f"  客户结构分析错误: {e}")
        
        self.results['structure'] = structure_results
    
    def resident_profile_analysis(self, month):
        """住户画像分析"""
        print(f"\n{'='*50}")
        print(f"住户画像分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取住户画像相关数据
        profile_indicators = {
            '在住总人数': month_data[month_data['指标'] == '在住总人数'],
            '在住总单元数': month_data[month_data['指标'] == '在住总单元数'],
            '住户国籍分布-中国': month_data[month_data['指标'] == '住户国籍分布-中国'],
            '住户国籍分布-外国': month_data[month_data['指标'] == '住户国籍分布-外国'],
            '住户性别分布-男性': month_data[month_data['指标'] == '住户性别分布-男性'],
            '住户性别分布-女性': month_data[month_data['指标'] == '住户性别分布-女性'],
            '住户年龄分布-18-25岁': month_data[month_data['指标'] == '住户年龄分布-18-25岁'],
            '住户年龄分布-26-35岁': month_data[month_data['指标'] == '住户年龄分布-26-35岁'],
            '住户年龄分布-36-45岁': month_data[month_data['指标'] == '住户年龄分布-36-45岁'],
            '住户年龄分布-46岁以上': month_data[month_data['指标'] == '住户年龄分布-46岁以上'],
            '有小孩的单元数': month_data[month_data['指标'] == '有小孩的单元数'],
            '有狗的单元数': month_data[month_data['指标'] == '有狗的单元数'],
            '有猫的单元数': month_data[month_data['指标'] == '有猫的单元数'],
            '有其他宠物的单元数': month_data[month_data['指标'] == '有其他宠物的单元数']
        }
        
        profile_results = {}
        
        print("住户画像数据:")
        for key, value in profile_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '分布' in key:
                    profile_results[key] = {'value': val, 'unit': '%'}
                    print(f"  {key}: {val}%")
                elif '单元数' in key:
                    profile_results[key] = {'value': val, 'unit': '间'}
                    print(f"  {key}: {val} 间")
                else:
                    profile_results[key] = {'value': val, 'unit': '人'}
                    print(f"  {key}: {val} 人")
        
        # 计算住户画像分析
        try:
            total_residents = profile_indicators['在住总人数']['数值'].iloc[0]
            total_units = profile_indicators['在住总单元数']['数值'].iloc[0]
            
            print(f"\n住户画像分析:")
            print(f"  总住户数: {total_residents} 人")
            print(f"  总单元数: {total_units} 间")
            print(f"  平均每单元人数: {total_residents/total_units:.2f} 人/间")
            
            # 国籍分布
            chinese_ratio = profile_indicators['住户国籍分布-中国']['数值'].iloc[0] / 100
            foreign_ratio = profile_indicators['住户国籍分布-外国']['数值'].iloc[0] / 100
            print(f"  中国籍住户: {chinese_ratio:.2%}")
            print(f"  外国籍住户: {foreign_ratio:.2%}")
            
            # 性别分布
            male_ratio = profile_indicators['住户性别分布-男性']['数值'].iloc[0] / 100
            female_ratio = profile_indicators['住户性别分布-女性']['数值'].iloc[0] / 100
            print(f"  男性住户: {male_ratio:.2%}")
            print(f"  女性住户: {female_ratio:.2%}")
            
            # 年龄分布
            age_18_25 = profile_indicators['住户年龄分布-18-25岁']['数值'].iloc[0] / 100
            age_26_35 = profile_indicators['住户年龄分布-26-35岁']['数值'].iloc[0] / 100
            age_36_45 = profile_indicators['住户年龄分布-36-45岁']['数值'].iloc[0] / 100
            age_46_plus = profile_indicators['住户年龄分布-46岁以上']['数值'].iloc[0] / 100
            print(f"  18-25岁: {age_18_25:.2%}")
            print(f"  26-35岁: {age_26_35:.2%}")
            print(f"  36-45岁: {age_36_45:.2%}")
            print(f"  46岁以上: {age_46_plus:.2%}")
            
            # 家庭结构分析
            kids_units = profile_indicators['有小孩的单元数']['数值'].iloc[0]
            dog_units = profile_indicators['有狗的单元数']['数值'].iloc[0]
            cat_units = profile_indicators['有猫的单元数']['数值'].iloc[0]
            other_pet_units = profile_indicators['有其他宠物的单元数']['数值'].iloc[0]
            
            print(f"\n家庭结构分析:")
            print(f"  有小孩的单元: {kids_units} 间 ({kids_units/total_units*100:.2f}%)")
            print(f"  有狗的单元: {dog_units} 间 ({dog_units/total_units*100:.2f}%)")
            print(f"  有猫的单元: {cat_units} 间 ({cat_units/total_units*100:.2f}%)")
            print(f"  有其他宠物的单元: {other_pet_units} 间 ({other_pet_units/total_units*100:.2f}%)")
            
            total_pet_units = dog_units + cat_units + other_pet_units
            pet_friendly_ratio = total_pet_units / total_units
            print(f"  宠物友好度: {pet_friendly_ratio:.2%}")
            
            # 年龄结构评估
            avg_age = (age_18_25 * 21.5 + age_26_35 * 30.5 + age_36_45 * 40.5 + age_46_plus * 50)
            print(f"  估计平均年龄: {avg_age:.1f} 岁")
            
            if 25 <= avg_age <= 35:
                print("  年龄结构评估: 主要为年轻上班族")
            elif 35 < avg_age <= 45:
                print("  年龄结构评估: 主要为中年家庭")
            else:
                print("  年龄结构评估: 年龄分布较为分散")
                
        except Exception as e:
            print(f"  住户画像分析错误: {e}")
        
        self.results['profile'] = profile_results
    
    def customer_satisfaction_analysis(self, month):
        """客户满意度分析"""
        print(f"\n{'='*50}")
        print(f"客户满意度分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取客户满意度相关数据
        satisfaction_indicators = {
            '调研发送数': month_data[month_data['指标'] == '调研发送数'],
            '调研回复数': month_data[month_data['指标'] == '调研回复数'],
            '同意进一步联系反馈数': month_data[month_data['指标'] == '同意进一步联系反馈数'],
            '客户关系满意度得分': month_data[month_data['指标'] == '客户关系满意度得分'],
            '客房服务满意度得分': month_data[month_data['指标'] == '客房服务满意度得分'],
            '工程服务满意度得分': month_data[month_data['指标'] == '工程服务满意度得分'],
            'IT服务满意度得分': month_data[month_data['指标'] == 'IT服务满意度得分'],
            '住户活动参与率': month_data[month_data['指标'] == '住户活动参与率'],
            '住户活动互动数据': month_data[month_data['指标'] == '住户活动互动数据'],
            '续租意愿百分比': month_data[month_data['指标'] == '续租意愿百分比'],
            '未来居住计划-继续居住': month_data[month_data['指标'] == '未来居住计划-继续居住'],
            '未来居住计划-搬离': month_data[month_data['指标'] == '未来居住计划-搬离'],
            '未来居住计划-不确定': month_data[month_data['指标'] == '未来居住计划-不确定'],
            '具体反馈内容': month_data[month_data['指标'] == '具体反馈内容'],
            '跟进处理结果': month_data[month_data['指标'] == '跟进处理结果']
        }
        
        satisfaction_results = {}
        
        print("客户满意度数据:")
        for key, value in satisfaction_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '得分' in key:
                    print(f"  {key}: {val} 分")
                elif '百分比' in key or '率' in key:
                    print(f"  {key}: {val}%")
                elif '数' in key and val != 0:
                    print(f"  {key}: {val}")
                elif '内容' in key or '结果' in key:
                    print(f"  {key}: {val}")
        
        # 计算客户满意度分析
        try:
            sent_count = satisfaction_indicators['调研发送数']['数值'].iloc[0]
            reply_count = satisfaction_indicators['调研回复数']['数值'].iloc[0]
            contact_count = satisfaction_indicators['同意进一步联系反馈数']['数值'].iloc[0]
            
            if sent_count > 0:
                reply_rate = (reply_count / sent_count) * 100
                contact_rate = (contact_count / reply_count) * 100 if reply_count > 0 else 0
                
                print(f"\n调研分析:")
                print(f"  调研发送数: {sent_count} 份")
                print(f"  调研回复数: {reply_count} 份")
                print(f"  调研回复率: {reply_rate:.2f}%")
                print(f"  同意进一步联系: {contact_count} 份")
                print(f"  联系同意率: {contact_rate:.2f}%")
                
                if reply_rate > 80:
                    print("  调研参与度: 优秀 (>80%)")
                elif reply_rate > 60:
                    print("  调研参与度: 良好 (60-80%)")
                elif reply_rate > 40:
                    print("  调研参与度: 一般 (40-60%)")
                else:
                    print("  调研参与度: 需改进 (<40%)")
            
            # 满意度得分分析
            relation_satisfaction = satisfaction_indicators['客户关系满意度得分']['数值'].iloc[0]
            room_satisfaction = satisfaction_indicators['客房服务满意度得分']['数值'].iloc[0]
            engineering_satisfaction = satisfaction_indicators['工程服务满意度得分']['数值'].iloc[0]
            it_satisfaction = satisfaction_indicators['IT服务满意度得分']['数值'].iloc[0]
            
            print(f"\n满意度得分:")
            print(f"  客户关系满意度: {relation_satisfaction} 分")
            print(f"  客房服务满意度: {room_satisfaction} 分")
            print(f"  工程服务满意度: {engineering_satisfaction} 分")
            print(f"  IT服务满意度: {it_satisfaction} 分")
            
            avg_satisfaction = (relation_satisfaction + room_satisfaction + engineering_satisfaction + it_satisfaction) / 4
            print(f"  综合满意度: {avg_satisfaction:.2f} 分")
            
            if avg_satisfaction >= 4.5:
                print("  满意度评估: 优秀 (≥4.5分)")
            elif avg_satisfaction >= 4.0:
                print("  满意度评估: 良好 (4.0-4.4分)")
            elif avg_satisfaction >= 3.5:
                print("  满意度评估: 一般 (3.5-3.9分)")
            else:
                print("  满意度评估: 需改进 (<3.5分)")
            
            # 续租意愿分析
            renewal_willingness = satisfaction_indicators['续租意愿百分比']['数值'].iloc[0] / 100
            continue_living = satisfaction_indicators['未来居住计划-继续居住']['数值'].iloc[0] / 100
            move_out = satisfaction_indicators['未来居住计划-搬离']['数值'].iloc[0] / 100
            uncertain = satisfaction_indicators['未来居住计划-不确定']['数值'].iloc[0] / 100
            
            print(f"\n续租意愿分析:")
            print(f"  续租意愿: {renewal_willingness:.2%}")
            print(f"  计划继续居住: {continue_living:.2%}")
            print(f"  计划搬离: {move_out:.2%}")
            print(f"  不确定: {uncertain:.2%}")
            
            if renewal_willingness > 0.8:
                print("  客户忠诚度: 优秀 (>80%)")
            elif renewal_willingness > 0.6:
                print("  客户忠诚度: 良好 (60-80%)")
            elif renewal_willingness > 0.4:
                print("  客户忠诚度: 一般 (40-60%)")
            else:
                print("  客户忠诚度: 需改进 (<40%)")
                
        except Exception as e:
            print(f"  客户满意度分析错误: {e}")
    
    def analyze(self, month):
        """执行完整的客户分析"""
        print(f"\n开始客户分析 - {month}")
        print("="*60)
        
        self.customer_structure_analysis(month)
        self.resident_profile_analysis(month)
        self.customer_satisfaction_analysis(month)
        
        # 输出结果到文件
        #self.output_results_to_file(month)
        
        print(f"\n{'='*60}")
        print("客户分析完成")
        print("="*60)

    def output_results_to_file(self, month):
        """将分析结果输出"""
        report_parts = []

        report_parts.append(f"北京中天创业园客户分析报告\n")
        report_parts.append(f"分析月份: {month}\n")
        report_parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


        # 客户结构分析结果
        if 'structure' in self.results:
            report_parts.append("1. 客户结构分析\n")

            for key, data in self.results['structure'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']}%\n")
                    elif data['unit'] == '元':
                        report_parts.append(f"  {key}: {data['value']:,.2f}元\n")
                    elif data['unit'] == '间':
                        report_parts.append(f"  {key}: {data['value']}间\n")
                    elif data['unit'] == 'text':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']}\n")
            report_parts.append("\n")

        # 住户画像分析结果
        if 'profile' in self.results:
            report_parts.append("2. 住户画像分析\n")

            for key, data in self.results['profile'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']}%\n")
                    elif data['unit'] == '人':
                        report_parts.append(f"  {key}: {data['value']}人\n")
                    elif data['unit'] == '间':
                        report_parts.append(f"  {key}: {data['value']}间\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']}\n")
            report_parts.append("\n")

        # 客户满意度分析结果
        if 'satisfaction' in self.results:
            report_parts.append("3. 客户满意度分析\n")

            for key, data in self.results['satisfaction'].items():
                if 'unit' in data:
                    if data['unit'] == '%':
                        report_parts.append(f"  {key}: {data['value']}%\n")
                    elif data['unit'] == '分':
                        report_parts.append(f"  {key}: {data['value']}分\n")
                    elif data['unit'] == '人':
                        report_parts.append(f"  {key}: {data['value']}人\n")
                    elif data['unit'] == 'text':
                        report_parts.append(f"  {key}: {data['value']}\n")
                    else:
                        report_parts.append(f"  {key}: {data['value']}\n")
            report_parts.append("\n")

        # 综合评估
        report_parts.append("4. 综合评估\n")

        report_parts.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        report_parts.append("  数据来源: " + self.data_file + "\n")
        report_parts.append("  分析模块: 客户分析\n")
        report_parts.append("\n")

        report_parts.append("说明:\n")
        report_parts.append("- 本报告基于月度客户数据生成\n")
        report_parts.append("- 金额单位为元，人数单位为人\n")
        report_parts.append("- 百分比数据已标注单位\n")
        report_parts.append("- 详细分析方法请参考相关文档\n")

        return report_parts


def main():
    """主函数"""
    data_file = "北京中天创业园_月度数据表_补充版.csv"
    
    # 创建分析实例
    analyzer = CustomerAnalysis(data_file)
    
    # 分析指定月份
    target_month = "Jan-25"  # 可以修改为任意月份
    analyzer.analyze(target_month)

    report_string = analyzer.output_results_to_file(target_month)
    print(report_string)

if __name__ == "__main__":
    main()