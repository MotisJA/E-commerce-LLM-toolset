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
         下面是这个人的微博信息 {information}
         请你帮我:
         1. 写一个简单的总结
         2. 挑两件有趣的特点说一说
         3. 找一些他比较感兴趣的事情
         4. 写一篇热情洋溢的介绍信
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
