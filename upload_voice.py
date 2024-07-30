import os
import json
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException

# 检查并获取环境变量
ALIYUN_AK_ID = os.environ.get('ALIYUN_AK_ID')
ALIYUN_AK_SECRET = os.environ.get('ALIYUN_AK_SECRET')

if not ALIYUN_AK_ID or not ALIYUN_AK_SECRET:
    raise EnvironmentError('缺少阿里云的Access Key ID或Access Key Secret环境变量')

# 初始化AcsClient
client = AcsClient(ALIYUN_AK_ID, ALIYUN_AK_SECRET)
domain = 'nls-slp.cn-shanghai.aliyuncs.com'
version = '2019-08-19'

def build_request(api_name, method):
    request = CommonRequest()
    request.set_domain(domain)
    request.set_version(version)
    request.set_action_name(api_name)
    request.set_method(method)
    request.set_protocol_type('https')
    return request

def cosy_clone(voice_prefix, url):
    try:
        clone_request = build_request('CosyVoiceClone', 'POST')
        clone_request.add_body_params('Url', url)
        clone_request.add_body_params('VoicePrefix', voice_prefix)
        begin = int(round(time.time() * 1000))
        clone_response = client.do_action_with_exception(clone_request)
        end = int(round(time.time() * 1000))
        response_data = json.loads(clone_response)
        print(response_data)
        print('Cost: {} ms'.format(end - begin))
        return response_data
    except ServerException as e:
        print("服务端异常：", e)
    except ClientException as e:
        print("客户端异常：", e)

def cosy_list(voice_prefix, page_index=1, page_size=10):
    try:
        list_request = build_request('ListCosyVoice', 'POST')
        list_request.add_body_params('VoicePrefix', voice_prefix)
        list_request.add_body_params('PageIndex', page_index)
        list_request.add_body_params('PageSize', page_size)
        list_response = client.do_action_with_exception(list_request)
        response_data = json.loads(list_response)
        print(response_data)
        return response_data
    except ServerException as e:
        print("服务端异常：", e)
    except ClientException as e:
        print("客户端异常：", e)

if __name__ == '__main__':
    try:
        audio_url = input('请输入音频的URL：')
        if not audio_url:
            raise ValueError('音频URL不能为空')
        
        prefix = input('请输入音色前缀（英文字母或数字）：')
        if not prefix:
            raise ValueError('音色前缀不能为空')
        
        # 调用CosyVoiceClone接口复刻声音
        clone_result = cosy_clone(prefix, audio_url)
        
        # 调用ListCosyVoice接口查询状态
        list_result = cosy_list(prefix)
    except ValueError as e:
        print("输入错误：", e)
    except Exception as e:
        print("未知异常：", e)