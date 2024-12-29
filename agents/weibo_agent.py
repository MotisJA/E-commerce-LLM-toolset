# 导入一个搜索UID的工具
from tools.search_tool import get_UID

# 导入所需的库
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain_openai import ChatOpenAI
import os


# 通过LangChain代理找到UID的函数
def lookup_V(category: str):
    # 初始化大模型
    llm = ChatOpenAI(
        model=os.environ["LLM_MODELEND"],
        temperature=0.7,  # 提高温度增加多样性
    )

    # 优化搜索提示模板
    template = """请帮我找到在{category}领域最有影响力的微博KOL或大V。
    
    重点关注以下特征：
    1. 粉丝量10万以上
    2. 有明确的{category}领域专业背景
    3. 有稳定的带货转化能力
    4. 内容质量高、互动活跃
    5. 有品牌合作案例
    
    从以下来源搜索：
    1. 微博热门博主
    2. {category}话题下的活跃作者
    3. 带货榜单达人
    4. 行业意见领袖
    
    仅返回找到的最佳匹配KOL的微博UID数字（从URL https://weibo.com/u/[UID] 中提取）。
    """
    # 确保所有category参数命名统一
    prompt_template = PromptTemplate(input_variables=["category"], template=template)

    # 代理的工具
    tools = [
        Tool(
            name="Crawl Google for 微博 page",
            func=get_UID,
            description="useful for when you need get the 微博 UID",
        )
    ]

    # 初始化代理
    agent = initialize_agent(
        tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
    )

    # 返回找到的UID
    ID = agent.run(prompt_template.format_prompt(category=category))

    return ID
