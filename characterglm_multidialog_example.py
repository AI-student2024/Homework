import time
import os
import jwt
import requests
import zhipuai

from typing import Generator, List, Dict
from data_types import TextMsgList, MsgList,CharacterMeta

# from api import get_characterglm_response

from dotenv import load_dotenv
load_dotenv()


# 智谱开放平台API key，参考 https://open.bigmodel.cn/usercenter/apikeys
API_KEY: str = os.getenv("ZHIPUAI_API_KEY", "")

class ApiKeyNotSet(ValueError):
    pass

def verify_api_key_not_empty():
    if not API_KEY:
        raise ApiKeyNotSet

def generate_token(apikey: str, exp_seconds: int) -> str:
    # reference: https://open.bigmodel.cn/dev/api#nosdk
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)
 
    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }
 
    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


def get_characterglm_response(messages: TextMsgList, meta: CharacterMeta) -> Generator[str, None, None]:
    """ 通过http调用characterglm 这段代码的功能是实现通过HTTP调用智谱AI开放平台上的characterglm模型，用于生成基于给定消息和元数据的文本响应"""
    # Reference: https://open.bigmodel.cn/dev/api#characterglm
    verify_api_key_not_empty()
    url = "https://open.bigmodel.cn/api/paas/v3/model-api/charglm-3/sse-invoke"
    resp = requests.post(
        url,
        headers={"Authorization": generate_token(API_KEY, 1800)},
        json=dict(
            model="charglm-3",
            meta=meta,
            prompt=messages,
            incremental=True)
    )
    resp.raise_for_status()
    
    # 解析响应（非官方实现）
    sep = b':'
    last_event = None
    for line in resp.iter_lines():
        if not line or line.startswith(sep):
            continue
        field, value = line.split(sep, maxsplit=1)
        if field == b'event':
            last_event = value
        elif field == b'data' and last_event == b'add':
            yield value.decode()



def get_complete_response(messages, meta):
    generator = get_characterglm_response(messages, meta)
    full_response = ''.join(list(generator))
    return full_response

def get_chatglm_response(messages: List[Dict[str, str]]) -> str:
    """调用 chatglm 生成角色描述"""
    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY", ""))
    response = client.chat.completions.create(
        model="glm-3-turbo",
        messages=messages,
        stop=None,
        max_tokens=2000,
        stream=True,
    )
    full_response = ''.join(chunk.choices[0].delta.content for chunk in response)
    return full_response

def set_user_info():
    print("请设定您想扮演角色的名字:")
    user_role = input("名字: ")
    print(f"请输入一些关键词或者特性描述，以帮助生成{user_role}的详细信息（如年龄，职业，性别、个性等）:")
    descreption_keywords = input("角色描述关键词: ")
    messages = [{"role": "user", "content": f"生成一个角色描述，关键词：{descreption_keywords}"}]
    user_description = get_chatglm_response(messages)
    print(f"{user_role}的详细信息是：\n{user_description}")
    return user_role,user_description

def set_bot_info():
    print("请设定模型扮演角色的名字:")
    bot_role = input("名字: ")
    print(f"请输入一些关键词或者特性描述，以帮助{bot_role}的详细信息（如年龄、职业、性别、个性等）:")
    description_keywords = input("描述关键词: ")
    messages = [{"role": "user", "content": f"生成一个角色描述，关键词：{description_keywords}"}]
    bot_description = get_chatglm_response(messages)
    print(f"{bot_role}的详细信息是：\n{bot_description}")
    return bot_role, bot_description

def interactive_chat(meta):
    dialogue = []
    user_name, user_description = set_user_info()
    bot_name, bot_description = set_bot_info()

    meta['user_name'] = user_name
    meta['user_info'] = user_description
    meta['bot_name'] = bot_name
    meta['bot_info'] = bot_description

    print(f"对话已开始。{bot_name} 将与你对话。输入 '退出' 结束对话。")
    while True:
        user_input = input("你: ")
        if user_input.lower() == '退出':
            break
        messages = [{"role": "user", "content": user_input}]
        try:
            assistant_response = get_complete_response(messages, meta)
        except Exception as e:
            print(f"发生错误: {e}")
            assistant_response = "抱歉，我暂时无法回答。"
        dialogue.append(f"用户: {user_input}")
        dialogue.append(f"{bot_name}: {assistant_response}")
        print(f"{bot_name}: {assistant_response}")
    return '\n'.join(dialogue)

def save_dialogue(dialogue, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(dialogue)

def main():
    character_meta = {
        "user_info": "",
        "bot_info": "",
        "user_name": "用户",
        "bot_name": ""
    }
    dialogue = interactive_chat(character_meta)
    save_dialogue(dialogue, 'dialogue.txt')
    print("对话已保存到文件。")

if __name__ == '__main__':
    main()