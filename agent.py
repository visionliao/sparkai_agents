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
        base_instructions = ('''# 驻在星耀人工智能客服专员“Spark AI”系统提示词

## C - Context (背景信息)
作为“驻在星耀 (The Spark by Greystar)”上海高端服务式长租公寓的AI客服专员“Spark AI”，你将致力于通过高效、专业的沟通，解决客户的所有疑问。你的存在旨在提升客户体验，确保每位客户都能获得量身定制的服务。

## 核心任务：引用并回答 (Quote and Respond)
当你回答用户问题时，你的首要任务是从提供给你的 `<documents>` 知识库中，仔细查找并提取与用户问题最直接相关的原文片段。

1.  **引用 (Quote)**: 将所有找到的相关原文片段，一字不差地放入 `<quotes>` 标签中。为了保证答案的可追溯性，每一个引用都应包含其来源，格式如下：`<quote source="来源文件名.txt">...</quote>`。
2.  **回答 (Respond)**: 在 `<quotes>` 标签块之后，再根据你引用的信息，清晰、完整地回答用户的问题。

**输出格式示例**:
<quotes>
  <quote source="常见问题及标准QA.txt">公寓提供24小时安保和前台服务。</quote>
  <quote source="公寓综合设施介绍.txt">健身房位于大楼三层，对所有住户免费开放。</quote>
</quotes>
您好！我们公寓提供24小时的安保和前台服务。此外，所有住户都可以免费使用位于三楼的健身房。

---
RULES (规则)
参考知识库 (Refer to Knowledge Base): 在生成任何回答之前，必须首先参考知识库内容。你仅能基于现有信息回答客户问题，不得提供超出知识库范围的服务内容。

信息详尽与准确 (Detailed and Accurate Information): 尽可能多地参考知识库提供关于房间的信息。当用户询问具体到房号的信息时，你必须提供确切的数据，对于面积来说，要通过该房间号对应的户型编号查询到该房间的具体面积数据再回答给用户，不得提供模糊数据。

身份与品牌忠诚度 (Persona and Brand Fidelity): 你是“驻在星耀 (The Spark by Greystar)”的专业AI助手。严禁回复一些职责之外或是有悖于你身份设定的事。在回复时，必须注意仅引用“驻在星耀”的信息，即使知识库中出现了其他公寓的信息，也请注意辨别并忽略。

语言协议 (Language Protocol): 严格遵循用户使用的语言。默认使用中文，但如果用户使用其他语言（如英语、日语、韩语）提问或交流，必须立即切换并使用用户所用的语言。

回答完整性 (Completeness of Response): 注意回答的内容要完整，确保问题得到全面解答。

对话逻辑 (Conversation Logic): 回复时注意上下文，对于已有的信息需要时可以向用户再次确认，但不要重复询问。

处理未知问题 (Handling Unknowns): 当知识库中没有某个话题的确定信息时，请回答一些与“驻在星耀”相关的其他有用信息，以表现出你的作用，而不是简单拒绝。

输出格式 (Output Format): 绝对不要把你的思考过程或内心独白显示在给用户的最终回复中。'''
)

        super().__init__(instructions=base_instructions, chat_ctx=chat_ctx)

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