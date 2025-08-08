import os
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import AsyncIterable
from dataclasses import asdict

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
你是Spark AI，专为上海高端服务式公寓驻在星耀 (The Spark by Greystar)服务的专属AI智能中枢。你的核心使命是，基于我提供的上下文文件(context_files)，为四类用户提供极致精准、高效、且符合其身份的对话服务。

# 核心行为准则 (Core Behavioral Principles)
1.  **绝对数据驱动与溯源:** 你的所有回答都**必须**严格来源于我提供的文件内容。严禁使用任何外部知识或进行猜测。在回答时，尽可能引用你的信息来源。如果找不到信息，必须明确回答：“根据我现有的资料，无法找到关于...的信息。”
2.  **用户意图优先:** 在回答前，首先判断提问者最可能是哪类用户，并采用相应的沟通模式：
    *   **对潜在住客 (Potential Resident):** **这是你的首要对外角色。** 语气必须热情、详尽、且富有吸引力，像一个专业的虚拟租赁顾问。你的目标是清晰展示公寓价值，激发其兴趣，并引导他们进行下一步操作（如预约看房）。优先使用“营销与介绍类文件”。
    *   **对住客 (Tenant):** 语气亲切、耐心、可靠。像一个全能的生活管家。优先使用“规则问答类文件”。
    *   **对运营方 (Operator):** 语气专业、精准、高效。像一个可靠的工作助手。优先使用“运营数据类文件”。
    *   **对CEO/管理者 (Manager):** 语气简洁、数据化、有洞察力。像一个能干的数据分析师。优先使用“分析报告类文件”。
3.  **注意甄别信息的来源:**回复用户关于自身公寓信息时不要引用其他公寓的信息，即使这个信息出现在了知识库中，请注意辨别
4.  **灵活使用工具:**对于一些复杂问题，或是需要新数据的问题，请你灵活使用工具解决，解决问题时优先考虑工具都能做到什么，再在工具帮助的基础上给予知识文件解决问题
    **例如:**
    *   当用户询问出租率时，先通过查询在住的统计信息，其中会得到当前独立住客数量，再与总房间数579计算得出出租率，最后回复给客户
    *   当使用一个工具出现问题时，应主动尝试使用另一个工具
5.  **注意不要将思维过程显示出来**


# 输出格式化
*   **适应性:** 鉴于交互界面为简单文本窗口，请积极使用Markdown进行格式化，以提升信息的可读性。使用项目符号(`* `)、粗体(`**text**`)、引用(`> `)来组织回答。''')


        super().__init__(instructions=base_instructions, chat_ctx=chat_ctx)

    '''async def llm_node(
            self,
            chat_ctx: ChatContext,
            tools: list[FunctionTool],
            model_settings: ModelSettings,
    ) -> AsyncIterable[ChatChunk]:
        """
        这个方法覆盖了 Agent 的默认 LLM 节点。
        我们在这里调用底层的 LLM 插件，然后包装返回的流，
        以便在不干扰 Agent 运行的情况下打印出所有数据。
        """

        llm_plugin = self.session.llm
        if llm_plugin is None:
            async def empty_stream():
                if False:
                    yield

            return empty_stream()

        model_settings_dict = asdict(model_settings)

        # 调用 chat 方法时，使用转换后的字典
        llm_stream = llm_plugin.chat(
            chat_ctx=chat_ctx,
            tools=tools,
            **model_settings_dict,
        )

        async def stream_wrapper(original_stream: LLMStream) -> AsyncIterable[ChatChunk]:
            logging.debug("--- [LLM DEBUG] Streaming Chunks ---")
            async for chunk in original_stream:
                logging.debug(chunk)
                yield chunk
            logging.debug("--- [LLM DEBUG] Streaming Finished ---")

            if hasattr(original_stream, 'raw_response') and original_stream.raw_response:
                logging.debug("--- [LLM DEBUG] Complete Raw Response ---")
                try:
                    raw_data = original_stream.raw_response
                    if hasattr(raw_data, "to_dict"):
                        logging.debug(json.dumps(raw_data.to_dict(), indent=2, ensure_ascii=False))
                    else:
                        logging.debug(raw_data)
                except Exception:
                    logging.exception("序列化 raw_response 时出错")
                    logging.debug(original_stream.raw_response)
                logging.debug("--------------------------------------")

        return stream_wrapper(llm_stream)'''

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
        llm=google.LLM(model="gemini-2.5-flash", ),
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
                timeout=600,
                client_session_timeout_seconds=600,
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
        "SPARK_579间房型+面积朝向.txt",
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
                    f'    <source>{filename}</source>\n'
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