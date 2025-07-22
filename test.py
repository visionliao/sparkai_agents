import os
import google.cloud.texttospeech as tts

# --- 1. 打印环境变量，用于诊断 ---
print("--- Diagnosing Environment Variables ---")
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
print("--------------------------------------\n")

try:
    # --- 2. 准备客户端和请求 ---
    # 客户端会自动使用 GOOGLE_APPLICATION_CREDENTIALS
    # 底层的 httpx 库会自动使用 HTTP_PROXY/HTTPS_PROXY
    client = tts.TextToSpeechClient()

    # 要合成的文本
    synthesis_input = tts.SynthesisInput(
        text="您好，我是Spark AI 您的专属AI助理，请问有什么可以帮您？"
    )

    # 语音配置
    voice = tts.VoiceSelectionParams(
        language_code="zh-CN", ssml_gender=tts.SsmlVoiceGender.NEUTRAL
    )

    # 音频配置
    audio_config = tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.MP3
    )
    
    # --- 3. 发起 API 请求 ---
    print("Sending request to Google Cloud TTS API...")
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    print("Successfully received response from API.")

    # --- 4. 将返回的音频内容写入文件 ---
    output_filename = "output.mp3"
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)
    
    print(f"\nSUCCESS: Audio content written to {output_filename}")

except Exception as e:
    print(f"\nERROR: An exception occurred!")
    print("--------------------------------------")
    # 打印详细的错误信息，这至关重要！
    import traceback
    traceback.print_exc()
    print("--------------------------------------")