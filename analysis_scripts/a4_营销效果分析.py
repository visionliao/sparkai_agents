#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
营销效果分析脚本
分析营销投入产出、自有渠道效果等营销相关指标

统计项目:
1. 营销投入分析
   - 总营销投入
   - 各渠道投入占比
   - 营销投入趋势
   - 营销预算执行率

2. 获客效果分析
   - 获客数量统计
   - 获客成本计算
   - 获客渠道分析
   - 获客转化率

3. 渠道效果分析
   - 自有渠道效果
   - 第三方渠道效果
   - 线上渠道效果
   - 线下渠道效果

4. 营销ROI分析
   - 各渠道ROI计算
   - 营销投资回报率
   - 营销效率评估
   - 成本效益分析

5. 营销策略评估
   - 营销活动效果
   - 品牌影响力分析
   - 市场渗透率分析
   - 营销优化建议
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MarketingEffectivenessAnalysis:
    def __init__(self, data_file):
        """初始化营销效果分析类"""
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
    
    def marketing_roi_analysis(self, month):
        """营销投入产出分析"""
        print(f"\n{'='*50}")
        print(f"营销投入产出分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取营销投入产出相关数据
        roi_indicators = {
            '线上营销渠道花费': month_data[month_data['指标'] == '线上营销渠道花费'],
            '线下营销渠道花费': month_data[month_data['指标'] == '线下营销渠道花费'],
            '中介渠道花费': month_data[month_data['指标'] == '中介渠道花费'],
            '自有渠道花费': month_data[month_data['指标'] == '自有渠道花费'],
            '线上营销渠道产生收入': month_data[month_data['指标'] == '线上营销渠道产生收入'],
            '线下营销渠道产生收入': month_data[month_data['指标'] == '线下营销渠道产生收入'],
            '中介渠道产生收入': month_data[month_data['指标'] == '中介渠道产生收入'],
            '自有渠道产生收入': month_data[month_data['指标'] == '自有渠道产生收入'],
            '租赁和市场总费用': month_data[month_data['指标'] == '租赁和市场总费用']
        }
        
        print("营销投入产出数据:")
        for key, value in roi_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '花费' in key:
                    print(f"  {key}: {val:,.2f} 元")
                elif '收入' in key:
                    print(f"  {key}: {val:,.2f} 元")
                elif '费用' in key:
                    print(f"  {key}: {val:,.2f} 元")
        
        # 计算营销ROI分析
        roi_results = {}
        try:
            online_cost = roi_indicators['线上营销渠道花费']['数值'].iloc[0]
            offline_cost = roi_indicators['线下营销渠道花费']['数值'].iloc[0]
            agent_cost = roi_indicators['中介渠道花费']['数值'].iloc[0]
            own_cost = roi_indicators['自有渠道花费']['数值'].iloc[0]
            total_cost = online_cost + offline_cost + agent_cost + own_cost
            
            online_income = roi_indicators['线上营销渠道产生收入']['数值'].iloc[0]
            offline_income = roi_indicators['线下营销渠道产生收入']['数值'].iloc[0]
            agent_income = roi_indicators['中介渠道产生收入']['数值'].iloc[0]
            own_income = roi_indicators['自有渠道产生收入']['数值'].iloc[0]
            total_income = online_income + offline_income + agent_income + own_income
            
            roi_results['total_cost'] = total_cost
            roi_results['total_income'] = total_income
            roi_results['online_roi'] = (online_income - online_cost) / online_cost * 100 if online_cost > 0 else 0
            roi_results['offline_roi'] = (offline_income - offline_cost) / offline_cost * 100 if offline_cost > 0 else 0
            roi_results['agent_roi'] = (agent_income - agent_cost) / agent_cost * 100 if agent_cost > 0 else 0
            roi_results['own_roi'] = (own_income - own_cost) / own_cost * 100 if own_cost > 0 else 0
            roi_results['total_roi'] = (total_income - total_cost) / total_cost * 100
            
            print(f"\n营销投入分析:")
            print(f"  线上营销花费: {online_cost:,.2f} 元 ({online_cost/total_cost*100:.2f}%)")
            print(f"  线下营销花费: {offline_cost:,.2f} 元 ({offline_cost/total_cost*100:.2f}%)")
            print(f"  中介渠道花费: {agent_cost:,.2f} 元 ({agent_cost/total_cost*100:.2f}%)")
            print(f"  自有渠道花费: {own_cost:,.2f} 元 ({own_cost/total_cost*100:.2f}%)")
            print(f"  总营销花费: {total_cost:,.2f} 元")
            
            print(f"\n营销产出分析:")
            print(f"  线上营销收入: {online_income:,.2f} 元 ({online_income/total_income*100:.2f}%)")
            print(f"  线下营销收入: {offline_income:,.2f} 元 ({offline_income/total_income*100:.2f}%)")
            print(f"  中介渠道收入: {agent_income:,.2f} 元 ({agent_income/total_income*100:.2f}%)")
            print(f"  自有渠道收入: {own_income:,.2f} 元 ({own_income/total_income*100:.2f}%)")
            print(f"  总营销收入: {total_income:,.2f} 元")
            
            print(f"\nROI分析:")
            if online_cost > 0:
                online_roi = (online_income - online_cost) / online_cost * 100
                print(f"  线上营销ROI: {online_roi:.2f}%")
            if offline_cost > 0:
                offline_roi = (offline_income - offline_cost) / offline_cost * 100
                print(f"  线下营销ROI: {offline_roi:.2f}%")
            if agent_cost > 0:
                agent_roi = (agent_income - agent_cost) / agent_cost * 100
                print(f"  中介渠道ROI: {agent_roi:.2f}%")
            if own_cost > 0:
                own_roi = (own_income - own_cost) / own_cost * 100
                print(f"  自有渠道ROI: {own_roi:.2f}%")
            
            total_roi = (total_income - total_cost) / total_cost * 100
            print(f"  总体营销ROI: {total_roi:.2f}%")
            
            # 渠道效率评估
            print(f"\n渠道效率评估:")
            channels = [
                ('线上营销', online_cost, online_income),
                ('线下营销', offline_cost, offline_income),
                ('中介渠道', agent_cost, agent_income),
                ('自有渠道', own_cost, own_income)
            ]
            
            for channel_name, cost, income in channels:
                if cost > 0:
                    roi = (income - cost) / cost * 100
                    if roi > 200:
                        efficiency = "优秀"
                    elif roi > 100:
                        efficiency = "良好"
                    elif roi > 0:
                        efficiency = "一般"
                    else:
                        efficiency = "亏损"
                    print(f"  {channel_name}: {efficiency} (ROI: {roi:.2f}%)")
            
        except Exception as e:
            print(f"  营销ROI分析错误: {e}")
        
        self.results['roi'] = roi_results
    
    def owned_channel_analysis(self, month):
        """自有渠道效果分析"""
        print(f"\n{'='*50}")
        print(f"自有渠道效果分析 - {month}")
        print(f"{'='*50}")
        
        month_data = self.get_month_data(month)
        if month_data is None:
            return
            
        # 提取自有渠道相关数据
        channel_indicators = {
            '微信阅读量': month_data[month_data['指标'] == '微信阅读量'],
            '微信新增粉丝': month_data[month_data['指标'] == '微信新增粉丝'],
            '小红书点击量': month_data[month_data['指标'] == '小红书点击量'],
            '小红书新增粉丝': month_data[month_data['指标'] == '小红书新增粉丝'],
            '小红书点赞': month_data[month_data['指标'] == '小红书点赞'],
            '小红书潜在客户线索': month_data[month_data['指标'] == '小红书潜在客户线索'],
            'Instagram总粉丝数': month_data[month_data['指标'] == 'Instagram总粉丝数'],
            'Instagram页面触达增长百分比': month_data[month_data['指标'] == 'Instagram页面触达增长百分比'],
            'Instagram目标账户触达数': month_data[month_data['指标'] == 'Instagram目标账户触达数'],
            'Instagram非粉丝互动数': month_data[month_data['指标'] == 'Instagram非粉丝互动数'],
            'Instagram重要帖子点赞数': month_data[month_data['指标'] == 'Instagram重要帖子点赞数'],
            'Instagram页面浏览量': month_data[month_data['指标'] == 'Instagram页面浏览量'],
            'Facebook总粉丝数': month_data[month_data['指标'] == 'Facebook总粉丝数'],
            'Facebook页面触达增长百分比': month_data[month_data['指标'] == 'Facebook页面触达增长百分比'],
            'Facebook内容触达账户数': month_data[month_data['指标'] == 'Facebook内容触达账户数'],
            'Facebook平均每帖展示数': month_data[month_data['指标'] == 'Facebook平均每帖展示数'],
            'Facebook页面浏览量': month_data[month_data['指标'] == 'Facebook页面浏览量'],
            'Facebook新增粉丝数': month_data[month_data['指标'] == 'Facebook新增粉丝数'],
            '微博发帖数': month_data[month_data['指标'] == '微博发帖数'],
            '微博总浏览量': month_data[month_data['指标'] == '微博总浏览量'],
            '直接成交数量': month_data[month_data['指标'] == '直接成交数量'],
            '直接成交租金收入': month_data[month_data['指标'] == '直接成交租金收入']
        }
        
        print("自有渠道数据:")
        for key, value in channel_indicators.items():
            if not value.empty:
                val = value['数值'].iloc[0]
                if '百分比' in key:
                    print(f"  {key}: {val}%")
                elif '浏览量' in key and '万次' in str(val):
                    print(f"  {key}: {val} 万次")
                elif '粉丝' in key or '数' in key:
                    print(f"  {key}: {val} 人")
                elif '量' in key or '次' in key:
                    print(f"  {key}: {val} 次")
                elif '数量' in key:
                    print(f"  {key}: {val} 间")
                elif '收入' in key:
                    print(f"  {key}: {val:,.2f} 元")
                else:
                    print(f"  {key}: {val}")
        
        # 计算自有渠道效果分析
        channel_results = {}
        try:
            # 微信分析
            wechat_reads = channel_indicators['微信阅读量']['数值'].iloc[0]
            wechat_new_followers = channel_indicators['微信新增粉丝']['数值'].iloc[0]
            wechat_engagement_rate = (wechat_new_followers / wechat_reads * 100) if wechat_reads > 0 else 0
            
            print(f"\n微信渠道分析:")
            print(f"  阅读量: {wechat_reads:,} 次")
            print(f"  新增粉丝: {wechat_new_followers} 人")
            print(f"  粉丝转化率: {wechat_engagement_rate:.2f}%")
            
            # 小红书分析
            xiaohongshu_clicks = channel_indicators['小红书点击量']['数值'].iloc[0]
            xiaohongshu_likes = channel_indicators['小红书点赞']['数值'].iloc[0]
            xiaohongshu_leads = channel_indicators['小红书潜在客户线索']['数值'].iloc[0]
            xiaohongshu_new_followers = channel_indicators['小红书新增粉丝']['数值'].iloc[0]
            
            print(f"\n小红书渠道分析:")
            print(f"  点击量: {xiaohongshu_clicks:,} 次")
            print(f"  点赞数: {xiaohongshu_likes:,} 个")
            print(f"  潜在客户线索: {xiaohongshu_leads:,} 条")
            print(f"  新增粉丝: {xiaohongshu_new_followers} 人")
            print(f"  线索转化率: {(xiaohongshu_leads/xiaohongshu_clicks*100):.2f}%")
            
            # Instagram分析
            instagram_followers = channel_indicators['Instagram总粉丝数']['数值'].iloc[0]
            instagram_growth = channel_indicators['Instagram页面触达增长百分比']['数值'].iloc[0]
            instagram_reach = channel_indicators['Instagram目标账户触达数']['数值'].iloc[0]
            instagram_engagement = channel_indicators['Instagram非粉丝互动数']['数值'].iloc[0]
            
            print(f"\nInstagram渠道分析:")
            print(f"  总粉丝数: {instagram_followers:,} 人")
            print(f"  页面触达增长: {instagram_growth}%")
            print(f"  目标账户触达: {instagram_reach:,} 人")
            print(f"  非粉丝互动: {instagram_engagement:,} 次")
            print(f"  互动率: {(instagram_engagement/instagram_reach*100):.2f}%")
            
            # Facebook分析
            facebook_followers = channel_indicators['Facebook总粉丝数']['数值'].iloc[0]
            facebook_growth = channel_indicators['Facebook页面触达增长百分比']['数值'].iloc[0]
            facebook_new_followers = channel_indicators['Facebook新增粉丝数']['数值'].iloc[0]
            facebook_views = channel_indicators['Facebook页面浏览量']['数值'].iloc[0]
            
            print(f"\nFacebook渠道分析:")
            print(f"  总粉丝数: {facebook_followers:,} 人")
            print(f"  页面触达增长: {facebook_growth}%")
            print(f"  新增粉丝: {facebook_new_followers} 人")
            print(f"  页面浏览量: {facebook_views:,} 次")
            print(f"  粉丝增长率: {(facebook_new_followers/facebook_followers*100):.2f}%")
            
            # 微博分析
            weibo_posts = channel_indicators['微博发帖数']['数值'].iloc[0]
            weibo_views = channel_indicators['微博总浏览量']['数值'].iloc[0]
            
            print(f"\n微博渠道分析:")
            print(f"  发帖数: {weibo_posts} 条")
            print(f"  总浏览量: {weibo_views} 万次")
            print(f"  平均每帖浏览量: {(weibo_views*10000/weibo_posts):,.0f} 次")
            
            # 直接成交分析
            direct_deals = channel_indicators['直接成交数量']['数值'].iloc[0]
            direct_income = channel_indicators['直接成交租金收入']['数值'].iloc[0]
            
            print(f"\n直接成交分析:")
            print(f"  直接成交数量: {direct_deals} 间")
            print(f"  直接成交收入: {direct_income:,.2f} 元")
            if direct_deals > 0:
                print(f"  平均每单收入: {direct_income/direct_deals:,.2f} 元")
            
            # 整体效果评估
            total_followers = instagram_followers + facebook_followers
            total_new_followers = wechat_new_followers + xiaohongshu_new_followers + facebook_new_followers
            total_leads = xiaohongshu_leads
            
            print(f"\n自有渠道整体效果:")
            print(f"  总粉丝数: {total_followers:,} 人")
            print(f"  本月新增粉丝: {total_new_followers} 人")
            print(f"  潜在客户线索: {total_leads} 条")
            print(f"  直接成交: {direct_deals} 间")
            
            lead_conversion_rate = (direct_deals / total_leads) * 100 if total_leads > 0 else 0
            if total_leads > 0:
                print(f"  线索转化率: {lead_conversion_rate:.2f}%")
            
            # 存储结果
            channel_results['total_followers'] = total_followers
            channel_results['total_new_followers'] = total_new_followers
            channel_results['total_leads'] = total_leads
            channel_results['direct_deals'] = direct_deals
            channel_results['direct_income'] = direct_income
            channel_results['lead_conversion_rate'] = lead_conversion_rate
            
        except Exception as e:
            print(f"  自有渠道分析错误: {e}")
        
        self.results['channels'] = channel_results
    
    def analyze(self, month):
        """执行完整的营销效果分析"""
        print(f"\n开始营销效果分析 - {month}")
        print("="*60)
        
        self.marketing_roi_analysis(month)
        self.owned_channel_analysis(month)
        
        # 输出结果到文件
        #self.output_results_to_file(month)
        
        print(f"\n{'='*60}")
        print("营销效果分析完成")
        print("="*60)

    def output_results_to_file(self, month):
        """将分析结果输出"""
        report = []

        report.append(f"北京中天创业园营销效果分析报告\n")
        report.append(f"分析月份: {month}\n")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 获取项目数据
        month_data = self.get_month_data(month)

        # 营销ROI分析
        report.append("1. 营销ROI分析\n")
        if month_data is not None and 'roi' in self.results:
            roi_data = self.results['roi']
            if 'total_cost' in roi_data:
                report.append(f"  总营销花费: {roi_data['total_cost']:,.2f}元\n")
                report.append(f"  总营销收入: {roi_data['total_income']:,.2f}元\n")
                report.append(f"  总体营销ROI: {roi_data['total_roi']:.2f}%\n")

                if 'online_roi' in roi_data:
                    report.append(f"  线上营销ROI: {roi_data['online_roi']:.2f}%\n")
                if 'offline_roi' in roi_data:
                    report.append(f"  线下营销ROI: {roi_data['offline_roi']:.2f}%\n")
                if 'agent_roi' in roi_data:
                    report.append(f"  中介渠道ROI: {roi_data['agent_roi']:.2f}%\n")
                if 'own_roi' in roi_data:
                    report.append(f"  自有渠道ROI: {roi_data['own_roi']:.2f}%\n")
        report.append("\n")

        # 自有渠道效果分析
        report.append("2. 自有渠道效果分析\n")
        if month_data is not None and 'channels' in self.results:
            channel_data = self.results['channels']
            if 'total_followers' in channel_data:
                report.append(f"  总粉丝数: {channel_data['total_followers']:,}人\n")
                report.append(f"  本月新增粉丝: {channel_data['total_new_followers']}人\n")
                report.append(f"  潜在客户线索: {channel_data['total_leads']}条\n")
                report.append(f"  直接成交数量: {channel_data['direct_deals']}间\n")
                report.append(f"  直接成交收入: {channel_data['direct_income']:,.2f}元\n")
                report.append(f"  线索转化率: {channel_data['lead_conversion_rate']:.2f}%\n")
        report.append("\n")

        # 综合评估
        report.append("3. 综合评估\n")
        report.append("  分析完成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        report.append("  数据来源: " + self.data_file + "\n")
        report.append("  分析模块: 营销效果分析\n")
        report.append("\n")

        report.append("说明:\n")
        report.append("- 本报告基于月度营销数据生成\n")
        report.append("- 金额单位为元，数量单位为相应单位\n")
        report.append("- ROI和百分比数据已标注单位\n")
        report.append("- 详细分析方法请参考相关文档\n")

        return report


def main():
    """主函数"""
    data_file = "北京中天创业园_月度数据表_补充版.csv"
    
    # 创建分析实例
    analyzer = MarketingEffectivenessAnalysis(data_file)
    
    # 获取所有月份列
    months = [col for col in analyzer.df.columns if col != 'category' and col != '单位及备注']
    print(f"可分析的月份: {months}")
    
    # 分析指定月份
    target_month = "Aug-25"  # 可以修改为任意月份
    analyzer.analyze(target_month)

    report_string = analyzer.output_results_to_file(target_month)
    print(report_string)


if __name__ == "__main__":
    main()