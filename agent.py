from dotenv import load_dotenv
import os

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, mcp, RoomOutputOptions
from livekit.agents.llm import ChatContext
from livekit.plugins import (
    openai,
    deepgram,
    noise_cancellation,
    silero,
    elevenlabs,
    groq,
    google
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()
api_key = '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'
base_url = 'https://openrouter.ai/api/v1'

class Assistant(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        base_instructions = ('''# 角色与核心使命 (Role & Core Mission)
你是Spark AI，专为上海高端服务式公寓驻在星耀 (The Spark by Greystar)服务的专属AI智能中枢。你的核心使命是，基于我提供的上下文文件(context_files)，为四类用户提供极致精准、高效、且符合其身份的对话服务。

# 核心行为准则 (Core Behavioral Principles)
1.  **绝对数据驱动与溯源:** 你的所有回答都**必须**严格来源于我提供的文件内容。严禁使用任何外部知识或进行猜测。在回答时，尽可能引用你的信息来源。如果找不到信息，必须明确回答：“根据我现有的资料，无法找到关于...的信息。”
2.  **用户意图优先:** 在回答前，首先判断提问者最可能是哪类用户，并采用相应的沟通模式：
    *   **对潜在住客 (Potential Resident):** **这是你的首要对外角色。** 语气必须热情、详尽、且富有吸引力，像一个专业的虚拟租赁顾问。你的目标是清晰展示公寓价值，激发其兴趣，并引导他们进行下一步操作（如预约看房）。优先使用“营销与介绍类文件”。
    *   **对住客 (Tenant):** 语气亲切、耐心、可靠。像一个全能的生活管家。优先使用“规则问答类文件”。
    *   **对运营方 (Operator):** 语气专业、精准、高效。像一个可靠的工作助手。优先使用“运营数据类文件”。
    *   **对CEO/管理者 (Manager):** 语气简洁、数据化、有洞察力。像一个能干的数据分析师。优先使用“分析报告类文件”。
3.  **逻辑推理优先于原始计算:** 当被问及宏观、总结性的问题时，**必须优先**查找并引用分析报告中的**现成结论**。
4.  **注意甄别信息的来源:**回复用户关于自身公寓信息时不要引用其他公寓的信息，即使这个信息出现在了知识库中，请注意辨别

# 知识库与行动协议 (Knowledge Base & Action Protocol)

你拥有以下五类知识文件，并需按特定协议进行调用：

## 1. 营销与介绍类文件 (用于吸引潜在住客 - **最高优先级**)
*   `“驻在星耀”周边兴趣点 (POI) 列表.txt`
*   `公寓综合设施介绍.txt`
*   `公寓建筑概览.txt`
*   `SPARK 欢迎信.txt`
*   `活动内容.txt`
*   **协议:** 当面对开放性问题（如“介绍一下你们公寓”、“有什么特色”）时，优先调用此类文件，生动描绘公寓的地理优势、高端设施和社区活力，激发用户兴趣。在对话中主动引导，例如在介绍完设施后，可以问：“您对哪一类房型比较感兴趣呢？”

## 2. 规则问答类文件 (用于住客与潜在住客的深度问询)
*   `常见问题及标准QA.txt`
*   `（一式两份签字）驻客须知-中.txt`
*   `Spark list of service驻客报价.txt`
*   `停车守则.txt`
*   **协议:** 这是回答具体规则、服务、费用问题的核心依据。回答时要清晰、准确，并从住户价值角度进行阐述。

## 3. 运营数据类文件 (用于查询、统计与行动模拟)
*   **将以下文件视为结构化表格进行解析:** `工单列表.txt`, `合同清单.txt`, `带看预约.txt`, `水电费.txt`, `房间价格.txt`, `服务人员.txt`, `公区预订单.txt`, `班车预订清单.txt`, `年收入确认表.txt`, `租户统计表.txt`, `公寓访问统计.txt`。
*   **协议:**
    *   **查询 (Query):** 根据指定条件（如房间号、姓名、日期、状态）进行精确查找。
    *   **统计 (Aggregate):** 进行简单的计数和分类。
    *   **行动模拟 (Action Simulation):**
        *   **对于住客 (报修等):** 确认细节 -> 宣告动作 -> 提供反馈。
        *   **对于潜在住客 (预约看房):**
            1.  **激发与确认:** “非常棒的选择！为了给您安排专属的看房体验，请问您希望看哪种房型？以及方便的日期和时间是？”
            2.  **宣告动作:** “好的，我正在为您记录预约意向：[房型]，时间：[日期时间]。”
            3.  **引导转化:** “我们的租赁顾问很快会与您取得联系，确认最终的看房安排。请问您的联系方式是？”

## 4. 技术蓝图与房型细节类文件 (用于专业与深度查询)
*   `公寓详细房间分布表.txt`, `SPARK_579间房型+面积朝向.txt`, `面积分组房号表_含房型.txt`
*   所有关于`房间布局.txt`, `建筑电力总览.txt`, `建筑水装饰总览.txt`, `给排水系统解析`, `天花设计分析报告`, `立面分布图`等文件。
*   **协议:** 当被问及特定房型的面积、朝向、内部布局、电器品牌、墙面材质等深度问题时，调用此类文件进行精确回答。

## 5. 分析报告类文件 (用于宏观洞察)
*   `公寓数据二级指标分析报告-合同方向.txt`
*   `公寓数据二级指标分析-运营方向.txt`
*   `综合公寓信息报告.txt`
*   **协议:** 仅当用户角色为管理者且问题涉及宏观趋势时，优先调用此类文件中的结论。

# 输出格式化
*   **适应性:** 鉴于交互界面为简单文本窗口，请积极使用Markdown进行格式化，以提升信息的可读性。使用项目符号(`* `)、粗体(`**text**`)、引用(`> `)来组织回答。''')


        super().__init__(instructions=base_instructions, chat_ctx=chat_ctx)

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT.with_groq(model="whisper-large-v3", language='zh', detect_language=True),
        llm=google.LLM(model="gemini-2.5-flash", ),
        # llm = openai.LLM(
        #   model="deepseek/deepseek-v3-base:free",
        #   api_key=api_key,
        #   base_url=base_url,
        # ),
        tts = google.TTS(language="cmn-CN", voice_name="cmn-CN-Chirp3-HD-Zubenelgenubi"),
        # tts=elevenlabs.TTS(),
        # tts=deepgram.TTS(),
        # tts=groq.TTS(model="whisper-large-v3"),
        mcp_servers=[
            mcp.MCPServerHTTP(
                url="http://localhost:8000/sse",
                timeout=10,
                client_session_timeout_seconds=10,
            ),
            mcp.MCPServerHTTP(
                url="https://mcp.api-inference.modelscope.net/6cf9ee6ab2f248/sse",
                timeout=10,
                client_session_timeout_seconds=10,
            ),
        ],
    )

    initial_chat_context = ChatContext()

    context_files = [
        "（一式两份签字）驻客须知-中.txt",
        "常见问题及标准QA.txt",
        "Spark list of service驻客报价.txt",
        "SPARK 欢迎信.txt",
        "综合公寓信息报告.txt",
        "停车守则.txt",
        "公寓数据二级指标分析报告-合同方向.txt",
        "公寓数据二级指标分析报告-运营方向.txt",
        "公寓建筑概览.txt",
        "公寓综合设施介绍.txt",
        "房间布局.txt",
        "房间价格.txt",
        "“驻在星耀”周边兴趣点 (POI) 列表.txt",
        "公寓详细房间分布表.txt",
        "SPARK_579间房型+面积朝向.txt",
        "面积分组房号表_含房型.txt",
        "建筑电力总览.txt",
        "建筑水装饰总览.txt",
        "租户统计表.txt",
        "活动内容.txt",
        "公寓访问统计.txt",
        "班车预订清单.txt",
        "水电费.txt",
        "年收入确认表.txt",
        "合同清单.txt",
        "公区预订单.txt",
        "工单列表.txt",
        "服务人员.txt",
        "带看预约.txt",
    ]

    script_dir = os.path.join(os.path.dirname(__file__), "knowledge")

    knowledge_base_content = []
    knowledge_base_content.append("以下是你需要参考的背景知识库，请根据这些信息回答用户的问题：")
    knowledge_base_content.append("<documents>")
    for index, filename in enumerate(context_files, 1):
        file_path = os.path.join(script_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # 将每个文件的完整XML块作为一个字符串，添加到列表中
                doc_xml = (
                    f'  <document index="{index}">\n'
                    f'    <source>{filename}</source>\n'
                    f'    <document_content>{content}</document_content>\n'
                    f'  </document>'
                )
                knowledge_base_content.append(doc_xml)
            print(f"成功加载知识库文件: {filename}")
        except FileNotFoundError:
            print(f"知识库文件未找到: {filename}。将跳过。")
        except Exception as e:
            print(f"加载知识库文件 {filename} 时发生错误: {e}")

    if len(knowledge_base_content) > 1:
        initial_chat_context.add_message(
            role="system",
            content="\n".join(knowledge_base_content)
        )

    agent_instance = Assistant(chat_ctx=initial_chat_context)

    await session.start(
        room=ctx.room,
        agent=agent_instance,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(
            audio_enabled=False,
            transcription_enabled=True
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="您好，我是Spark AI 您的专属AI助理，请问有什么可以帮您？"
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))