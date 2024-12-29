# 导入所需要的库
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from tools.parsing_tool import TextParsing
import os

# 生成文案的函数
def generate_letter(information):
    # 设置输出解析器
    parser = PydanticOutputParser(pydantic_object=TextParsing)
    
    letter_template = """
    分析以下电商KOL的信息: {information}
    
    请你作为商务拓展专家：
    1. 基本情况分析
       - 总结其专业背景和影响力
       - 分析粉丝规模和质量
       - 评估商业信誉
       - 总结过往合作案例
    
    2. 特色亮点提炼
       - 专业领域优势
       - 粉丝群体特点
       - 内容创作特色
       - 带货能力分析
       
    3. 潜在合作机会
       - 可以对接的业务方向
       - 共同的市场机会
       - 可以深度合作的领域
       - 双方的协同优势
       
    4. 商务合作邮件
       - 突出合作诚意
       - 强调共同价值
       - 提供明确合作方案
       - 凸显双赢前景
    
    要求：
    - 内容具体详实
    - 数据客观准确
    - 表达专业得体
    - 重点突出价值
    
    \n{format_instructions}"""

    prompt = PromptTemplate(
        input_variables=["information"],
        template=letter_template,
        partial_variables={
            "format_instructions": parser.get_format_instructions()
        },
    )

    # llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    llm = ChatOpenAI(model=os.environ.get("LLM_MODELEND"))

    # 构建并执行chain
    chain = prompt | llm | parser
    
    try:
        result = chain.invoke({"information": information})
        return result.json()
    except Exception as e:
        print(f"Error generating letter: {str(e)}")
        return None
