# server.py
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from pathlib import Path
from dotenv import load_dotenv

from datetime import datetime
import csv
from pathlib import Path

load_dotenv()
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "工单列表.csv")

mcp = FastMCP("LiveKit MCP")

@mcp.tool()
def get_current_time() -> str:
    """
    获取当前的服务器时间。

    返回:
        一个 ISO 8601 格式的字符串，表示服务器当前的日期和时间。
    """
    return datetime.now().isoformat()


@mcp.tool()
def add_ticket(
    source: str,
    ticket_id: str,
    ticket_type: str,
    project: str,
    applicant: str,
    contact: str,
    apartment: str,
    room_number: str = "",
    area: str = "",
    location: str = "",
    visit_date: str = "",
    visit_time: str = "",
    pms_id: str = ""
) -> dict:
    """
    向工单CSV文件中添加一条新的工单记录。

    Args:
        source (str): 数据来源 (例如, '小程序', 'PMS', 'AI助理').
        ticket_id (str): 工单编号 (随机生成，例如, 'GD202507160001').
        ticket_type (str): 工单类型 (例如, '维修').
        project (str): 服务项目 (例如, '空调不制冷').
        applicant (str): 申请人姓名.
        contact (str): 申请人联系方式.
        apartment (str): 公寓名称 (固定为'驻在星耀').
        room_number (str, optional): 房间号. Defaults to "".
        area (str, optional): 区域 (例如, '客房'). Defaults to "".
        location (str, optional): 具体位置 (例如, '卧室'). Defaults to "".
        visit_date (str, optional): 预计上门日期 (格式: YYYY/M/D). Defaults to "".
        visit_time (str, optional): 预计上门时间 (格式: HH:MM-HH:MM). Defaults to "".
        pms_id (str, optional): PMS单号. Defaults to "".

    Returns:
        一个包含操作结果的字典。
        成功时: {"success": True, "message": "工单已成功添加。"}
        失败时: {"success": False, "error": "错误信息..."}
    """
    try:
        # 检查CSV文件是否存在，如果不存在，则创建并写入表头
        csv_path = Path(CSV_FILE_PATH)
        if not csv_path.exists():
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                header = [
                    '数据来源', '工单编号', '工单类型', '区域', '位置', '服务项目', '公寓',
                    '房间号', '申请人', '联系方式', '预计上门日期', '预计上门时间',
                    'PMS单号', '状态', '创建人', '创建时间', '更新人', '更新时间'
                ]
                writer.writerow(header)

        # 准备要写入的新行数据
        # 注意：这里的顺序必须和CSV文件的列头完全一致
        current_time = datetime.now().strftime('%Y/%m/%d %H:%M')
        new_row = [
            source,
            ticket_id,
            ticket_type,
            area,
            location,
            project,
            apartment,
            room_number,
            applicant,
            contact,
            visit_date,
            visit_time,
            pms_id,
            '待处理',  # 状态 (Status) - 新工单默认为“待处理”
            applicant, # 创建人 (Creator) - 默认为申请人
            current_time,  # 创建时间 (Created Time)
            applicant, # 更新人 (Updater) - 初始时与创建人相同
            current_time,  # 更新时间 (Updated Time)
        ]

        # 以追加模式 ('a') 打开文件，并写入新行
        # newline='' 是为了防止在Windows下写入多余的空行
        with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(new_row)

        return {"success": True, "message": f"工单 {ticket_id} 已成功添加到 {CSV_FILE_PATH}。"}

    except Exception as e:
        print(f"Error writing to CSV: {e}")
        return {"success": False, "error": f"写入CSV文件时发生错误: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport="sse")