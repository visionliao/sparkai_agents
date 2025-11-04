# merge_data_v2.py

import csv
import re
import os

# --- 配置区 ---
# 定义输入文件名和输出文件名
PRICE_FILE = '房间价格.txt'
LAYOUT_FILE = '公寓详细房间分布表.txt'
AREA_ASPECT_FILE = 'SPARK_579间房间+房间对应面积朝向.txt'
GROUP_FILE = '面积分组房号表_含房型.txt'
OUTPUT_CSV = '公寓信息汇总.csv'

# 定义最终CSV文件的表头
CSV_HEADERS = [
    '房号', '楼栋', '楼层', '房型', '户型代码', '面积(平方米)', '朝向',
    '12个月租金', '6-11个月租金', '2-5个月租金', '1个月租金'
]

# --- 主数据存储结构 ---
# 创建一个字典来存储所有房间的数据，键为房号
all_room_data = {}


# --- 文件处理函数 ---

def process_prices(filename):
    """处理价格文件，并初始化主数据字典"""
    print(f"正在处理价格文件: '{filename}'...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 从第4行开始读取数据（跳过表头）
            for line in lines[3:]:
                parts = line.strip().split()
                if not parts or len(parts) < 5:
                    continue

                room_no = parts[0]
                # 为每个房间初始化一个字典
                all_room_data[room_no] = {
                    '房号': room_no,
                    '楼栋': room_no[0] if room_no else '',
                    '楼层': '',
                    '房型': '',
                    '户型代码': '',
                    '面积(平方米)': '',
                    '朝向': '',
                    '12个月租金': parts[1],
                    '6-11个月租金': parts[2],
                    '2-5个月租金': parts[3],
                    '1个月租金': parts[4]
                }
    except FileNotFoundError:
        print(f"错误: 文件 '{filename}' 未找到。")
        return False
    print(f"价格文件处理完毕。共初始化 {len(all_room_data)} 个房间的数据。")
    return True


def process_layout(filename):
    """处理房间分布表，补充楼层和房型信息"""
    print(f"正在处理房间分布文件: '{filename}'...")
    current_floor = ''
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # 使用正则表达式匹配楼层信息，如 "2F*18间"
                floor_match = re.match(r'^(\w+F)\*(\d+)间', line)
                if floor_match:
                    current_floor = floor_match.group(1)

                # 按制表符或多个空格分割，以获取房间信息块
                room_blocks = re.split(r'\t+', line)
                for block in room_blocks:
                    block = block.strip()
                    # 房号和房型通常由空格隔开，如 "A201 行政单间"
                    parts = block.split()
                    if len(parts) >= 2 and re.match(r'^[A-Z]\d+', parts[0]):
                        room_no = parts[0]
                        room_type = ' '.join(parts[1:])

                        # 如果房号已存在于我们的主数据中，则更新信息
                        if room_no in all_room_data:
                            all_room_data[room_no]['楼层'] = current_floor
                            all_room_data[room_no]['房型'] = room_type

    except FileNotFoundError:
        print(f"错误: 文件 '{filename}' 未找到。")
        return False
    print("房间分布文件处理完毕。")
    return True


def process_area_aspect(filename):
    """处理包含面积和朝向信息的文件 (已修复版)"""
    print(f"正在处理面积朝向文件: '{filename}'...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 跳过表头
            for line in lines[2:]:
                parts = line.strip().split()
                if not parts or len(parts) < 3:
                    continue

                # --- 这是修复后的关键逻辑 ---
                room_no = parts[0]  # 第一个元素总是房号
                area = parts[-1]  # 最后一个元素总是面积
                aspect = ' '.join(parts[1:-1])  # 中间的所有部分组合起来就是完整的朝向

                if room_no in all_room_data:
                    all_room_data[room_no]['面积(平方米)'] = area
                    all_room_data[room_no]['朝向'] = aspect
    except FileNotFoundError:
        print(f"错误: 文件 '{filename}' 未找到。")
        return False
    print("面积朝向文件处理完毕。")
    return True


def process_groups(filename):
    """处理面积分组文件，补充户型代码"""
    print(f"正在处理面积分组文件: '{filename}'...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 跳过表头
            for line in lines[2:]:
                parts = line.strip().split('\t')
                if not parts or len(parts) < 4:
                    continue

                model_code = parts[2]

                # 从第4列开始都是房号
                for room_part in parts[3:]:
                    # 清理房号，例如 "B208室" -> "B208"
                    room_no = room_part.replace('室', '').strip()
                    if room_no in all_room_data:
                        all_room_data[room_no]['户型代码'] = model_code
    except FileNotFoundError:
        print(f"错误: 文件 '{filename}' 未找到。")
        return False
    print("面积分组文件处理完毕。")
    return True


def write_csv_file(filename):
    """将整合后的所有数据写入最终的CSV文件"""
    print(f"正在将所有数据写入到 '{filename}'...")
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()

            # 按照房号排序后写入数据
            for room_no in sorted(all_room_data.keys()):
                writer.writerow(all_room_data[room_no])
    except IOError:
        print(f"错误: 无法写入文件 '{filename}'。请检查权限或文件是否被占用。")
        return False
    print(f"成功创建最终文件: '{filename}'")
    return True


# --- 脚本主执行区 ---
if __name__ == "__main__":
    print("--- 开始执行数据整合脚本 (修复版) ---")

    # 首先检查所有必需的输入文件是否存在
    required_files = [PRICE_FILE, LAYOUT_FILE, AREA_ASPECT_FILE, GROUP_FILE]
    if not all(os.path.exists(f) for f in required_files):
        print("错误: 一个或多个输入文件缺失。请确保所有 .txt 文件都在脚本所在的目录下。")
    else:
        # 按顺序执行所有处理步骤
        if process_prices(PRICE_FILE):
            process_layout(LAYOUT_FILE)
            process_area_aspect(AREA_ASPECT_FILE)
            process_groups(GROUP_FILE)
            write_csv_file(OUTPUT_CSV)

    print("--- 脚本执行完毕 ---")