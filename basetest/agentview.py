# agent.py 文件顶部
from dotenv import load_dotenv
import os
from dataclasses import asdict

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, mcp, RoomOutputOptions

# --- 请用下面这个完整的代码块，替换您文件中所有相关的单个 import ---
from livekit.agents.llm import (
    FunctionTool,   # 解决了之前的 NameError
    ChatChunk,      # 解决本次的 NameError: name 'ChatChunk' is not defined
    ChatContext,    # 这是您原来就有的
    LLMStream,      # 调试代码需要
)
from livekit.agents.voice import ModelSettings # 解决了之前的 NameError
from typing import AsyncIterable          # 解决了之前的 NameError
import json
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
        base_instructions = ('''# 驻在星耀人工智能助手“Spark AI”系统提示词

## C - Context (背景信息)
作为“驻在星耀 (The Spark by Greystar)”上海高端服务式长租公寓的AI助手“Spark AI”，你将致力于通过高效、专业的沟通，解决客户的所有疑问。你的存在旨在提升客户体验，确保每位客户都能获得量身定制的服务。

RULES
1.before generating any response refer to the context given
2.Give as many information as possible refering to context about room information
3.When u don't have information with certian topic please response relevant information to make u seems useful
4.ALAWAYS follow stict to the language guest use , aware of the change in language

**注意**：
你仅能基于现有信息内容回答客户问题，不得提供超出知识库范围的服务内容。
默认使用中文与用户交流，如果用户提出了其他语言的需求，请按照用户的需求，切换交流所使用的语言，如果检测到用户用其他语言提问，例如英语、日语、韩语，也按照用户所有语言切换交流所使用的语言。
当用户询问具体到房号的信息时，你需要提供确切的数据，对于面积来说，不要提供模糊的面积数据，要通过该房间号对应的户型编号查询到该房间的具体面积数据再回答给用户
回复时注意上下文，对于已有的信息需要时可以向用户再次确认，但不要不要重复询问
注意你是一名专业的AI助手，不要回复一些职责之外或是有悖于你的身份设定的事
你隶属于驻在星耀 (The Spark by Greystar)注意回复用户关于公寓信息时不要引用其他公寓的信息，即使这个信息出现在了知识库中，请注意辨别
不要把思考的过程显示出来

通过遵循以上系统提示词，“Spark AI”将能够为客户提供卓越的服务体验，进一步提升“驻在星耀”的品牌形象。'''
                             "你应该使用简短且简洁的回答。"
                             "你可能会收到用户摄像头或屏幕的实时画面，请根据画面内容回答用户的问题。")

        super().__init__(instructions=base_instructions, chat_ctx=chat_ctx)

    # 在您的 Assistant 类中
    async def llm_node(
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
            # ... 这里的 stream_wrapper 代码保持不变 ...
            print("\n--- [LLM DEBUG] Streaming Chunks ---")
            async for chunk in original_stream:
                print(chunk)
                yield chunk
            
            print("--- [LLM DEBUG] Streaming Finished ---\n")

            if hasattr(original_stream, 'raw_response') and original_stream.raw_response:
                print("--- [LLM DEBUG] Complete Raw Response ---")
                try:
                    raw_data = original_stream.raw_response
                    if hasattr(raw_data, "to_dict"):
                        print(json.dumps(raw_data.to_dict(), indent=2, ensure_ascii=False))
                    else:
                        print(raw_data)
                except Exception as e:
                    print(f"Could not serialize raw_response: {e}")
                    print(original_stream.raw_response)

                print("--------------------------------------\n")

        return stream_wrapper(llm_stream)

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT.with_groq(model="whisper-large-v3", language='zh', detect_language="True"),
        llm=google.LLM(model="gemini-2.5-flash", ),
        # llm = openai.LLM(
        #   model="deepseek/deepseek-v3-base:free",
        #   api_key=api_key,
        #   base_url=base_url,
        # ),
        tts = google.TTS(language="cmn-CN", voice_name="cmn-CN-Chirp3-HD-Zubenelgenubi", speaking_rate=1.5),
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
        "公寓数据二级指标分析报告.txt",
        "公寓建筑概览.txt",
        "公寓综合设施介绍.txt",
        "房间布局.txt",
        "“驻在星耀”周边兴趣点 (POI) 列表.txt",
        #"公寓详细房间分布表.txt",
        "SPARK_579间房型+面积 Sheet1.txt",
        "SPARK_579间房型+面积 Sheet2.txt",
        "面积分组房号表_含房型.txt",
        "建筑电力总览.txt",
        "建筑水装饰总览.txt",
        "租户统计表.txt",
        "活动内容.txt",
        "公寓访问统计.txt",
        "班车预订清单.txt",
        "租售报价.txt",
        "水电费.txt",
        "年收入确认表.txt",
        "合同清单.txt",
        "公区预订单.txt",
        "订单信息.txt",
        "订单管理.txt",
        "工单列表.txt",
        "服务人员.txt",
        "带看预约.txt",
    ]

    script_dir = os.path.join(os.path.dirname(__file__), "knowledge")

    knowledge_base_content = []
    knowledge_base_content.append("以下是你需要参考的背景知识库，请根据这些信息回答用户的问题：")

    for filename in context_files:
        file_path = os.path.join(script_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                knowledge_base_content.append(f"\n--- 文件: {filename} ---\n{content}")
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