from dotenv import load_dotenv
import os

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, mcp, RoomOutputOptions
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
    elevenlabs,
    groq,
    hume,
    google
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from openai import models

load_dotenv()
api_key = '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'
#api_key = 'sk-zqgtbwsousqqgogdextjisowumwtkkyvgqhxbuzqqlcxzxem'
base_url = 'https://openrouter.ai/api/v1'
#base_url = "https://api.siliconflow.cn/v1"

class Assistant(Agent):
    def __init__(self) -> None:
        context_files = [
            "（一式两份签字）驻客须知-中.txt",
            "常见问题及标准QA.txt",
            "Spark list of service驻客报价.txt",
            "SPARK欢迎信.txt",
            "综合公寓信息报告.txt",
            "公寓建筑概览.txt",
            "公寓综合设施介绍（包含1层与7层公共区域以及地下停车场的详细介绍）.txt",
            "房间布局整合.txt",
            #"房间布局整合优化.txt",
            "公寓详细房间分布表.txt",
            "房型数量面积及楼层分布情况.txt",
            "面积分组房号表_含房型.txt",
            #"QA简化.txt",
            #"房型面积数据.txt",
            # 如果有其他文件，可以在这里添加
            # "another_context.txt",
        ]
        # 用于存储所有文件内容的字符串
        combined_context = []
        script_dir = os.path.join(os.path.dirname(__file__), "knowledge")

        for filename in context_files:
            file_path = os.path.join(script_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 将文件名和内容格式化，方便 LLM 理解
                    combined_context.append(f"\n--- 文件名: {filename} ---\n{content}")
                print(f"成功加载上下文文件: {filename}")
            except FileNotFoundError:
                print(f"上下文文件未找到: {filename}。将跳过此文件。")
            except Exception as e:
                print(f"加载上下文文件 {filename} 时发生错误: {e}")

        base_instructions = ('''# 驻在星耀人工智能客服专员“Spark AI”系统提示词

## C - Context (背景信息)
作为“驻在星耀 (The Spark by Greystar)”上海高端服务式长租公寓的AI客服专员“Spark AI”，你将致力于通过高效、专业的沟通，解决客户的所有疑问。你的存在旨在提升客户体验，确保每位客户都能获得量身定制的服务。

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

通过遵循以上系统提示词，“Spark AI”将能够为客户提供卓越的服务体验，进一步提升“驻在星耀”的品牌形象。'''
            "你应该使用简短且简洁的回答。"
            "你可能会收到用户摄像头或屏幕的实时画面，请根据画面内容回答用户的问题。")
        # 将所有文件内容添加到指令中
        full_instructions = base_instructions
        if combined_context:
            full_instructions += "\n\n以下是一些额外的背景信息和知识，请参考这些信息进行回答：\n"
            full_instructions += "\n".join(combined_context)
        super().__init__(instructions=full_instructions)


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        #turn_detection=MultilingualModel(),
        #stt=deepgram.STT(model="nova-3", language="multi"),
        stt=openai.STT.with_groq(model="whisper-large-v3", language='zh'),
        #llm = openai.LLM(
        #   model="deepseek/deepseek-v3-base:free",
        #   api_key=api_key,
        #   base_url=base_url,
        #),
        llm=google.LLM(model="gemini-2.5-flash", ),
        #tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        #tts=elevenlabs.TTS(),
        #tts=deepgram.TTS(),
        #tts=groq.TTS(model="whisper-large-v3"),
        #tts=hume.TTS(),
        #tts=google.TTS(),
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

    await session.start(
        room=ctx.room,
        agent=Assistant(),
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