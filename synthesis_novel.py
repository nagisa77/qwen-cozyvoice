# coding=utf-8

import os
import json
import time
import re
import nls
import pyaudio
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from aliyunsdkcore.request import CommonRequest

# 设置打开日志输出
nls.enableTrace(False)

# 从环境变量中获取 AccessKey ID 和 AccessKey Secret
ALIYUN_AK_ID = os.environ.get('ALIYUN_AK_ID')
ALIYUN_AK_SECRET = os.environ.get('ALIYUN_AK_SECRET')

if not ALIYUN_AK_ID or not ALIYUN_AK_SECRET:
    raise ValueError("Please set the environment variables ALIYUN_AK_ID and ALIYUN_AK_SECRET")

# 获取用户输入的 AppKey
app_key = input("Please enter the AppKey: ")

# 获取Token
credentials = AccessKeyCredential(ALIYUN_AK_ID, ALIYUN_AK_SECRET)
client = AcsClient(region_id='cn-shanghai', credential=credentials)
request = CommonRequest()
request.set_method('POST')
request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
request.set_version('2019-02-28')
request.set_action_name('CreateToken')

try:
    response = client.do_action_with_exception(request)
    response_data = json.loads(response)
    if 'Token' in response_data and 'Id' in response_data['Token']:
        token = response_data['Token']['Id']
        print(f"Token: {token}")
    else:
        raise ValueError("Failed to get Token.")
except Exception as e:
    raise ValueError(f"Error: {e}")

# 将音频保存进文件
SAVE_TO_FILE = True
# 将音频通过播放器实时播放，需要具有声卡。在服务器上运行请将此开关关闭
PLAY_REALTIME_RESULT = True

def read_text_file(file_path, chunk_size=100):
    with open(file_path, 'r', encoding='utf-8') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk

def filter_text(text):
    # 只保留中文字符、逗号和句号
    return re.sub(r'[^\u4e00-\u9fa5，。]', '', text)

if __name__ == "__main__":
    voice_name = input("Please enter the VoiceName: ")
    txt_file_path = input("Please enter the path to the txt file: ")

    if SAVE_TO_FILE:
        file = open("output.wav", "wb")
    if PLAY_REALTIME_RESULT:
        player = pyaudio.PyAudio()
        stream = player.open(
            format=pyaudio.paInt16, channels=1, rate=24000, output=True
        )

    # 创建SDK实例
    # 配置回调函数
    def on_data(data, *args):
        if SAVE_TO_FILE:
            file.write(data)
        if PLAY_REALTIME_RESULT:
            stream.write(data)

    def on_message(message, *args):
        print("on message=>{}".format(message))

    def on_close(*args):
        print("on_close: args=>{}".format(args))

    def on_error(message, *args):
        print("on_error message=>{} args=>{}".format(message, args))

    sdk = nls.NlsStreamInputTtsSynthesizer(
        # 由于目前阶段大模型音色只在北京地区服务可用，因此需要调整url到北京
        url="wss://nls-gateway-cn-beijing.aliyuncs.com/ws/v1",
        token=token,
        appkey=app_key,
        on_data=on_data,
        on_sentence_begin=on_message,
        on_sentence_synthesis=on_message,
        on_sentence_end=on_message,
        on_completed=on_message,
        on_error=on_error,
        on_close=on_close,
        callback_args=[],
    )

    # 发送文本消息
    sdk.startStreamInputTts(
        voice=voice_name,       # 语音合成说话人
        aformat="wav",          # 合成音频格式
        sample_rate=24000,      # 合成音频采样率
        volume=50,              # 合成音频的音量
        speech_rate=0,          # 合成音频语速
        pitch_rate=0,           # 合成音频的音调
    )

    time.sleep(1)  # 确保 startStreamInputTts 已启动

    for text_chunk in read_text_file(txt_file_path):
        filtered_text = filter_text(text_chunk)
        print(f"Sending text chunk: {filtered_text}")
        sdk.sendStreamInputTts(filtered_text)
        time.sleep(3)  # 防止请求过于频繁

    sdk.stopStreamInputTts()

    if SAVE_TO_FILE:
        file.close()
    if PLAY_REALTIME_RESULT:
        stream.stop_stream()
        stream.close()
        player.terminate()