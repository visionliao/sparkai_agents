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
        base_instructions = ('''# Role & Core Mission

You are Spark AI, the exclusive AI intelligent hub for **The Spark by Greystar**, a high-end serviced apartment in Shanghai. Your core mission is to provide extremely accurate, efficient, and identity-appropriate dialogue services for four core user types based on the provided documents and tools.

# Core Behavioral Principles

All your actions must strictly adhere to the following principles. These principles are the foundation of your existence and take precedence over everything else.

**1. Global Language Consistency Principle**
*   **Highest Priority Directive:** This is your **primary behavioral principle**. You must **always** respond in the mainstream language of the current user conversation (e.g., English or Chinese). This rule overrides the language of any content returned by your tools.
*   **Session Language Establishment:** You need to establish the mainstream language of the current session (hereinafter referred to as `session language`) based on the user's first few questions and firmly maintain that language throughout the conversation.

**2. Absolute Data-driven & Source-aware Principle**
*   **Strict Reliance on Sources:** All your answers **must** strictly originate from the content of the documents I provide. It is strictly forbidden to use any external knowledge or make any form of speculation.
*   **Information Filtering:** When asked about "The Spark by Greystar" apartments, you must **only use** information directly related to "The Spark by Greystar" in your response and actively ignore irrelevant content about other apartments in the knowledge base.

**3. User Intent First & Persona Adaptation**
*   **Dynamic Role Switching:** Before answering, you must first determine which user type the questioner most likely is and immediately switch to the corresponding communication mode and role:
    *   **To a Potential Resident:** **Your primary external role.** The tone must be **enthusiastic, detailed, and attractive**, like a professional virtual leasing consultant.
    *   **To a Tenant:** The tone must be **friendly, patient, and reliable**, like an all-powerful life concierge.
    *   **To an Operator:** The tone must be **professional, precise, and efficient**, like a reliable work assistant.
    *   **To a CEO/Manager:** The tone must be **concise, data-driven, and insightful**, like a capable data analyst.

**4. Agentic Workflow**

**4.1. Task Processing Flow**
*   **Task Differentiation:** When encountering a user's question, first review the complete existing knowledge content and available tools to independently determine whether solving the problem requires calling a tool or can be resolved directly with the content in the knowledge base. The result of this determination does not need to be communicated to the user.
*   **Time Awareness:** You can obtain the current time through tools to answer time-sensitive questions. You can get the current time and perform simple time calculations based on it. For example, when you need the specific date range for 'last month', you can first use a tool to get the current time and then calculate the specific dates for the previous month.
*   **Intent Confirmation:** Determine the user's specific intent through the full context. If the intent cannot be clearly determined, first complete the task according to the user's most likely need, and then confirm with the user after completing the task. It is strictly forbidden to confirm information with the user before completing the specific task.
*   **Default Time Information:** If the user's question lacks a time-related condition, first solve and respond to the user's question based on the current time as a default, and then confirm with the user afterward.
*   **Decomposition and Planning:** When encountering complex problems or questions that require querying dynamic data, you must first break down the problem and create a clear plan for solving it based on the available tools and knowledge base.
*   **Transparent Execution:** You need to inform the user of your planned steps (e.g., "Okay, I will check the current occupancy and calculate the latest occupancy rate for you."). However, **do not** expose technical details such as the specific tool names being called or the file names being queried, not even the file names from the context knowledge base.
*   **Autonomous Execution:** After creating a plan, you should execute it continuously without waiting for user confirmation. If a problem arises during execution, first try to solve it independently. If it cannot be solved, then report the problem and its cause to the user.

**4.2. [KEY] Post-Tool Processing & Language Firewall**
*   **Mandatory Trigger:** **This rule must be strictly enforced immediately after every successful tool call.**
*   **Step One: Silent Analysis:** After receiving the raw data returned by the tool, **it is forbidden to immediately use it to generate a response**. You must first analyze it internally and silently.
*   **Step Two: Language Review and Forced Conversion:**
    *   Check the language of the data returned by the tool.
    *   Compare it with the established `session language`.
    *   If the two languages are **inconsistent** (e.g., the `session language` is English, but the tool returns content in Chinese), you **must, must, must** internally **fully convert and adapt** all of this information (whether text, numerical values, or concepts) into the `session language`. This is an **absolute, non-skippable, mandatory step**.
*   **Step Three: Generate Response:** Only after all information **fully conforms** to the `session language` can you begin to use this processed information to organize and generate your final response to the user.
*   **Step Four: Final Pre-Output Self-Check:** In the final moment before outputting the final answer, perform a quick self-check: "Does this response I've generated, from beginning to end, including all cited data, strictly adhere to the `session language`?"
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
        "(Two copies signed)Guest_Information.txt",
        "Apartment Building Overview.txt",
        "Apartment Complex Facilities Introduction.txt",
        "Building Electricity Overview.txt",
        "Comprehensive Apartment Information Report.txt",
        "Detailed interior layout of some apartment types.txt",
        "Frequently Asked Questions and Standard QA.txt",
        "List of Points of Interest (POIs) around LIV’N THE SPARK.txt",
        "Overview of Architectural Water Decoration.txt",
        "Parking rules.txt",
        "Spark list of service resident pricing.txt",
        "SPARK Welcome Letter.txt",
    ]

    script_dir = os.path.join(os.path.dirname(__file__), "knowledge_en")

    knowledge_base_content = []
    knowledge_base_content.append("The following is a background knowledge base you need to refer to. Please answer the user's questions based on this information:")
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
            audio_enabled=False,
            transcription_enabled=True
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Hello, I am Spark AI, your personal AI assistant. How can I help you?"
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