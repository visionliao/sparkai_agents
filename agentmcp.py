import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, mcp, RoomInputOptions
from livekit.plugins import deepgram, openai, silero, google, elevenlabs, groq, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("mcp-agent")

load_dotenv()

class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You can retrieve data via the MCP server. The interface is voice-based: "
                "accept spoken user queries and respond with synthesized speech."
            ),
        )

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        vad=silero.VAD.load(),
        #stt=deepgram.STT(model="nova-3", language="multi"),
        #llm=openai.LLM(model="gpt-4o-mini"),
        #tts=openai.TTS(),
        #stt=openai.STT.with_groq(model="whisper-large-v3", language='zh'),
        stt=openai.STT.with_groq(model="whisper-large-v3"),
        llm=google.LLM(model="gemini-2.5-flash", ),
        tts=deepgram.TTS(),
        #tts=elevenlabs.TTS(),
        turn_detection=MultilingualModel(),
        mcp_servers=[
            mcp.MCPServerHTTP(
                url="http://localhost:8000/sse",
                timeout=5,
                client_session_timeout_seconds=5,
            ),
        ],
    )

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))