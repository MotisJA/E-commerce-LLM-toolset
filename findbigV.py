# 导入所取的库
import re
from agents.weibo_agent import lookup_V
from tools.general_tool import remove_non_chinese_fields
from tools.scraping_tool import get_data
from tools.textgen_tool import generate_letter
from dotenv import load_dotenv
import os
import json

load_dotenv()

os.environ["SERPAPI_API_KEY"] = os.getenv('SERPAPI_API_KEY')
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_BASE_URL'] = os.getenv('OPENAI_BASE_URL')
os.environ['LLM_MODELEND'] = os.getenv('LLM_MODELEND')

def find_bigV(flower: str):
    try:
        # 拿到UID
        response_UID = lookup_V(flower_type=flower)
        
        # 检查是否包含数字的UID
        uid_matches = re.findall(r"\d+", response_UID)
        if not uid_matches:
            return generate_default_response(flower)
            
        # 抽取UID里面的数字
        UID = uid_matches[0]
        print("这位鲜花大V的微博ID是", UID)

        # 根据UID爬取大V信息
        person_info = get_data(UID)
        if not person_info:
            return generate_default_response(flower)

        # 移除无用的信息
        remove_non_chinese_fields(person_info)

        # 调用函数根据大V信息生成文本
        result = generate_letter(information=person_info)
        if not result:
            return generate_default_response(flower)
            
        return result
        
    except Exception as e:
        print(f"Error in find_bigV: {str(e)}")
        return generate_default_response(flower)

def generate_default_response(keyword):
    """生成默认的返回数据"""
    return json.dumps({
        "summary": f"抱歉，我们暂时无法找到与"{keyword}"相关的专家信息。",
        "facts": [
            "暂无相关信息",
            "您可以尝试使用其他相关关键词"
        ],
        "interest": [
            "建议您可以换个关键词试试",
            "或者稍后再来尝试"
        ],
        "letter": [
            f"很抱歉，我们当前未能找到与"{keyword}"相关的专家信息。建议您可以：\n1. 使用更具体的关键词\n2. 尝试相关领域的其他关键词\n3. 稍后再来尝试"
        ]
    })

if __name__ == "__main__":

    # 拿到UID
    response_UID = lookup_V(flower_type="牡丹")

    # 抽取UID里面的数字
    UID = re.findall(r"\d+", response_UID)[0]
    print("这位鲜花大V的微博ID是", UID)

    # 根据UID爬取大V信息
    person_info = get_data(UID)
    print(person_info)

    # 移除无用的信息
    remove_non_chinese_fields(person_info)
    print(person_info)

    result = generate_letter(information=person_info)
    print(result)

    from flask import jsonify

    # 使用json.loads将字符串解析为字典
    result = json.loads(result)
    abc = jsonify(
        {
            "summary": result["summary"],
            "facts": result["facts"],
            "interest": result["interest"],
            "letter": result["letter"],
        }
    )
