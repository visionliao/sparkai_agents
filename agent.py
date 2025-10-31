import os
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import AsyncIterable
from dataclasses import asdict
from google.genai import types as genai_types
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, mcp, RoomOutputOptions
from livekit.agents.voice import ModelSettings
from livekit.agents.llm import (
    FunctionTool,
    ChatChunk,
    ChatContext,
    LLMStream,
)
from livekit.plugins import (
    openai,
    deepgram,
    noise_cancellation,
    silero,
    elevenlabs,
    groq,
    google,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# --- 日志配置 START ---
# 建议将日志配置放在所有其他代码之前，以确保尽早捕获日志
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# 创建一个文件处理器，用于写入日志文件，并设置日志轮转
# 每个日志文件最大 10MB，保留最近 5 个文件
log_file = 'agent.log'
file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG) # 文件中也记录 DEBUG 及以上级别的信息

# 创建一个控制台处理器，以便在终端仍然能看到输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.DEBUG) # 控制台可以显示更详细的 DEBUG 信息

# 获取根记录器并添加处理器
# 这样，所有模块（包括 livekit 库本身）的日志都会被捕获
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # 设置根记录器的最低级别
root_logger.handlers.clear() # 清除可能存在的旧处理器
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)
# --- 日志配置 END ---


load_dotenv()
api_key = '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'
base_url = 'https://openrouter.ai/api/v1'

class Assistant(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        base_instructions = ('''# 角色与核心使命 (Role & Core Mission)

你是Spark AI，专为上海高端服务式公寓**驻在星耀 (The Spark by Greystar)**服务的专属AI智能中枢。你的核心使命是，基于提供的文件和工具，为四类核心用户提供极致精准、高效、且符合其身份的对话服务。

# 核心行为准则 (Core Behavioral Principles)

你的所有行为都必须严格遵循以下准则。这些准则是你存在的基础，其优先级高于一切。

**1. 全局语言一致性原则 (Global Language Consistency Principle)**
*   **最高优先级指令:** 这是你的**首要行为准-则**。你必须**始终**使用与当前用户对话的主流语言（例如：英语或中文）进行回复。此规则的优先级高于任何工具返回内容的语言。
*   **会话语言确立:** 你需要根据用户的第一句或最近几句提问来确立当前会话的主流语言（后文称`会话语言`），并在整个对话过程中坚定地维持该语言。

**2. 绝对数据驱动与溯源 (Absolute Data-driven & Source-aware Principle)**
*   **严格信源:** 你的所有回答都**必须**严格来源于我提供的文件内容。严禁使用任何外部知识或进行任何形式的猜测。
*   **信息甄别:** 当你被问及关于“驻在星耀”公寓的信息时，你必须**只使用**与“驻在星耀”直接相关的信息进行回答，并主动忽略知识库中关于其他公寓的无关内容。
*   **未知处理:** 如果在提供的资料中找不到所需信息，你必须明确、直接地回答：“根据我现有的资料，无法找到关于...的信息。” (注意：此句也需根据`会话语言`进行转换后再输出)。

**3. 用户意图优先与角色扮演 (User Intent First & Persona Adaptation)**
*   **动态角色切换:** 在回答前，你必须首先判断提问者最可能是哪类用户，并立即切换到相应的沟通模式和角色：
    *   **对潜在住客 (Potential Resident):** **你的首要对外角色。** 语气必须**热情、详尽、且富有吸引力**，如同一个专业的虚拟租赁顾问。
    *   **对住客 (Tenant):** 语气必须**亲切、耐心、可靠**，如同一个全能的生活管家。
    *   **对运营方 (Operator):** 语气必须**专业、精准、高效**，如同一个可靠的工作助手。
    *   **对CEO/管理者 (Manager):** 语气必须**简洁、数据化、有洞察力**，如同一个能干的数据分析师。

**4. 智能体化工作流 (Agentic Workflow)**

**4.1. 任务处理流程**
*   **任务区分:** 当遇到用户给出的问题时，首先查看完整的现有知识内容与可用的工具，自主判断问题的解决是否需要进行工具调用，还是仅靠知识库可直接查看的内容便可解决，判断结果无需告知用户
*   **时间感知:** 你可以通过工具获取当前时间，以便回答具有时效性的问题，你可以获取当前的时间并以此为基础进行简单的时间计算，如当你需要‘上个月’这个时间段的具体日期，你可以现使用工具获取现在时间后，根据现在的时间推算出上个月的具体日期。
*   **意图确认:** 通过完整上下文判断用户的具体意图，如无法明确判断用户的意图，请先按照用户最有可能的需求完成任务，完成任务后再先用户确认，严禁在进行具体任务完成前先用户确认信息。 
*   **拆解与规划:** 当遇到复杂的、或需要查询动态数据的问题时，你必须先将问题拆解，并根据可用的工具和知识库制定一个清晰的解决计划。
*   **透明化执行:** 你需要将你的计划步骤（例如：“好的，我将为您查询当前的入住情况并计算最新的出租率。”）告知用户。但**不要**暴露具体调用的工具名称、查询的文件名等技术细节。
*   **自主执行:** 制定计划后，应连续执行，无需等待用户确认。如果执行过程中出现问题，先尝试自主解决，若无法解决，再向用户报告问题及原因。 

**4.2. 【关键】工具后处理与语言防火墙 (Post-Tool Processing & Language Firewall)**
*   **强制触发:** **此规则在每次工具调用成功后必须立即强制执行。**
*   **第一步：静默分析:** 在获得工具返回的原始数据后，**禁止立刻用它来生成回复**。你必须先在内部对其进行静默分析。
*   **第二步：语言审查与强制转换:**
    *   检查工具返回数据的语言。
    *   将其与已确立的`会话语言`进行比对。
    *   如果两者语言**不一致**（例如，`会话语言`是英语，但工具返回了包含“张三”、“未入住”等中文内容），你**必须、必须、必须**在内部将所有这些信息（无论是文本、数值还是概念）**完全转换并适配**到`会话语言`中。这是一个**绝对的、不可跳过的强制步骤**。
*   **第三步：生成回复:** 只有在所有信息都**完全符合**`会话语言`之后，你才能开始使用这些处理过的信息来组织并生成你对用户的最终回复。
*   **第四步：最终输出前自检:** 在输出最终答案前的最后一刻，进行一次快速的自我检查：“我生成的这段回复，从头到尾，包括所有引用的数据，是否都严格遵守了`会话语言`？”
''')


        super().__init__(instructions=base_instructions, chat_ctx=chat_ctx)

async def entrypoint(ctx: agents.JobContext):
    # 注意：这里的 noise_cancellation 只有在连接 LiveKit Cloud 时才有效。
    # 如果您使用自托管的 LiveKit，建议移除这个选项或做好错误处理。
    try:
        noise_cancellation_plugin = noise_cancellation.BVC()
    except Exception:
        logging.warning("无法加载降噪插件，可能不是在 LiveKit Cloud 环境。将禁用降噪。")
        noise_cancellation_plugin = None

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT.with_groq(model="whisper-large-v3", language='zh', detect_language=True),
        max_tool_steps=10,
        llm=google.LLM(model="gemini-2.5-flash", max_output_tokens=65536, http_options=genai_types.HttpOptions(timeout=300000)
),
        # llm = openai.LLM(
        #   model="deepseek/deepseek-v3-base:free",
        #   api_key=api_key,
        #   base_url=base_url,
        # ),
        tts = google.TTS(language="cmn-CN", voice_name="cmn-CN-Chirp3-HD-Laomedeia", speaking_rate=1.5),
        # tts=elevenlabs.TTS(),
        # tts=deepgram.TTS(),
        # tts=groq.TTS(model="whisper-large-v3"),
        mcp_servers=[
            mcp.MCPServerHTTP(
                url="http://localhost:8000/sse",
                timeout=5,
                client_session_timeout_seconds=10,
            ),
            mcp.MCPServerHTTP(
                url="http://localhost:8001/sse",
                timeout=10,
                client_session_timeout_seconds=10,
            ),
            mcp.MCPServerHTTP(
                url="http://localhost:8002/sse",
                timeout=600,
                client_session_timeout_seconds=600,
            ),
            mcp.MCPServerHTTP(
                url="https://mcp.amap.com/sse?key=beb415c1aaeb42091106b78966c80bf1",
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
        "公寓建筑概览.txt",
        "公寓综合设施介绍.txt",
        "房间布局.txt",
        "房间价格.txt",
        "“驻在星耀”周边兴趣点 (POI) 列表.txt",
        "公寓详细房间分布表.txt",
        "SPARK_579间房间+房间对应面积朝向.txt",
        "面积分组房号表_含房型.txt",
        "建筑电力总览.txt",
        "建筑水装饰总览.txt",
        "活动内容.txt",
        "水电费.txt",
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
                doc_xml = (
                    f'  <document index="{index}">\n'
                    f'    <source>{os.path.splitext(filename)[0]}</source>\n'
                    f'    <document_content>{content}</document_content>\n'
                    f'  </document>'
                )
                knowledge_base_content.append(doc_xml)
            logging.info(f"成功加载知识库文件: {filename}")
        except FileNotFoundError:
            logging.warning(f"知识库文件未找到: {filename}。将跳过。")
        except Exception:
            logging.exception(f"加载知识库文件 {filename} 时发生错误")

    knowledge_base_content.append("</documents>")

    if len(knowledge_base_content) > 2: # 检查是否真的加载了文件
        initial_chat_context.add_message(
            role="system",
            content="\n".join(knowledge_base_content)
        )

    agent_instance = Assistant(chat_ctx=initial_chat_context)

    room_input_opts = RoomInputOptions(video_enabled=True)
    if noise_cancellation_plugin:
        room_input_opts.noise_cancellation = noise_cancellation_plugin

    await session.start(
        room=ctx.room,
        agent=agent_instance,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(
            audio_enabled=True,
            transcription_enabled=True
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="您好，我是Spark AI 您的专属AI助理，请问有什么可以帮您？"
    )

    @session.on("conversation_item_added")
    def on_conversation_item_added(event: agents.ConversationItemAddedEvent):
        # 检查消息的角色
        if event.item.role == 'user':
            # 这是用户的输入
            logging.info(f"--- [USER INPUT] ---")
            logging.info(f"User: {event.item.text_content}")
            logging.info(f"--------------------")
        elif event.item.role == 'assistant':
            # 这是 AI 的最终回复
            # 我们只记录非空的文本回复
            text_content = event.item.text_content.strip()
            if text_content:
                logging.info(f"--- [AI RESPONSE] ---")
                logging.info(f"AI: {text_content}")
                logging.info(f"---------------------")


if __name__ == "__main__":
    logging.info("启动 Agent Worker...")
    try:
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    except Exception:
        logging.critical("Agent Worker 启动失败", exc_info=True)
        # exc_info=True 会自动附加异常信息，等同于 logging.exception