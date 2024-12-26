from typing import Dict, List, Optional
import os
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

class MarketingAgent:
    def __init__(self):
        # 初始化 ChatOpenAI
        self.llm = ChatOpenAI(
            model=os.environ["LLM_MODELEND"],
            temperature=0.7
        )
        
        # 定义营销专家角色提示模板
        self.marketing_prompt = PromptTemplate(
            input_variables=["product", "target", "goal"],
            template="""你是一位资深的营销策划专家，擅长创意营销方案设计。
            
            目标产品: {product}
            目标受众: {target}
            营销目标: {goal}
            
            请你从以下几个方面进行头脑风暴,设计营销方案:
            1. 营销主题与核心卖点
            2. 传播渠道选择
            3. 创意活动形式
            4. 预期效果评估
            
            要求:
            - 方案要具体可执行
            - 创意要新颖独特
            - 符合目标受众特点
            - 注重投入产出比
            
            请给出你的详细营销方案建议:"""
        )
        
        # 创建营销方案生成链
        self.marketing_chain = LLMChain(
            llm=self.llm,
            prompt=self.marketing_prompt
        )
        
    def generate_marketing_plan(
        self,
        product: str,
        target: str,
        goal: str
    ) -> str:
        """
        生成营销方案
        
        Args:
            product: 目标产品/服务
            target: 目标受众群体 
            goal: 营销目标
            
        Returns:
            str: 生成的营销方案
        """
        try:
            # 调用chain生成方案
            response = self.marketing_chain.invoke({
                "product": product,
                "target": target, 
                "goal": goal
            })
            
            return response["text"]
            
        except Exception as e:
            print(f"生成营销方案时出错: {str(e)}")
            return "抱歉,生成方案时出现错误,请稍后重试。"

    def refine_plan(self, initial_plan: str, feedback: str) -> str:
        """
        根据反馈优化营销方案
        
        Args:
            initial_plan: 初始营销方案
            feedback: 优化反馈意见
            
        Returns:
            str: 优化后的营销方案
        """
        refine_prompt = PromptTemplate(
            input_variables=["plan", "feedback"],
            template="""基于以下初始营销方案和反馈意见,请对方案进行优化:
            
            初始方案:
            {plan}
            
            反馈意见:
            {feedback}
            
            请给出优化后的完整方案:"""
        )
        
        refine_chain = LLMChain(
            llm=self.llm,
            prompt=refine_prompt
        )
        
        try:
            response = refine_chain.invoke({
                "plan": initial_plan,
                "feedback": feedback
            })
            
            return response["text"]
            
        except Exception as e:
            print(f"优化营销方案时出错: {str(e)}")
            return "抱歉,优化方案时出现错误,请稍后重试。"
