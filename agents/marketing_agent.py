import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)

class MarketingCAMELAgent:
    def __init__(self, system_message: SystemMessage, model: ChatOpenAI) -> None:
        self.system_message = system_message
        self.model = model
        self.dialog_history = []  # 添加对话历史记录
        self.init_messages()

    def init_messages(self) -> None:
        self.stored_messages = [self.system_message]
        self.dialog_history = []  # 重置对话历史

    def update_messages(self, message: BaseMessage) -> List[BaseMessage]:
        self.stored_messages.append(message)
        # 记录对话历史
        if isinstance(message, HumanMessage):
            self.dialog_history.append({
                "role": "user",
                "content": message.content
            })
        elif isinstance(message, AIMessage):
            self.dialog_history.append({
                "role": "assistant",
                "content": message.content
            })
        return self.stored_messages

    def step(self, input_message: HumanMessage) -> AIMessage:
        messages = self.update_messages(input_message)
        output_message = self.model(messages)
        self.update_messages(output_message)
        
        # 添加控制台打印
        print(f"\n{'='*50}")
        print(f"输入消息: {input_message.content}")
        print(f"输出消息: {output_message.content}")
        print(f"{'='*50}\n")
        
        return output_message

    def get_dialog_history(self) -> List[Dict]:
        return self.dialog_history

class MarketingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.environ["LLM_MODELEND"],
            temperature=0.7
        )
        
        # 设置角色提示
        self.assistant_role_name = "营销策划专家"
        self.user_role_name = "企业决策者"
        
        # 修改系统提示以更好地支持多轮对话
        self.assistant_inception_prompt = """你是一位资深的{assistant_role_name}，正在帮助{user_role_name}制定营销方案。

任务背景：{task}

作为营销专家，你需要：
1. 提供详细的市场分析
2. 制定具体的营销策略
3. 规划执行时间表
4. 设定评估指标
5. 估算预算需求

每次回应都要：
- 保持专业性
- 给出具体建议
- 提供数据支持
- 预判可能问题
- 提出优化方向

如果方案完成，请在最后添加标记：<PLAN_COMPLETE>"""

        self.user_inception_prompt = """你是一位{user_role_name}，正在与{assistant_role_name}讨论营销方案。

关于任务：{task}

作为决策者，你需要：
1. 提供明确的需求和目标
2. 说明预算限制
3. 描述目标受众
4. 提出关注重点
5. 给出具体反馈

每次互动要：
- 提出具体问题
- 分享相关信息
- 给出清晰反馈
- 要求具体细节

如果方案满意，请在最后添加标记：<FEEDBACK_COMPLETE>"""

    def _get_sys_msgs(self, task: str):
        """生成系统消息"""
        assistant_template = SystemMessagePromptTemplate.from_template(
            template=self.assistant_inception_prompt
        )
        user_template = SystemMessagePromptTemplate.from_template(
            template=self.user_inception_prompt
        )
        
        assistant_msg = assistant_template.format_messages(
            assistant_role_name=self.assistant_role_name,
            user_role_name=self.user_role_name,
            task=task,
        )[0]
        
        user_msg = user_template.format_messages(
            assistant_role_name=self.assistant_role_name,
            user_role_name=self.user_role_name,
            task=task,
        )[0]
        
        return assistant_msg, user_msg

    def generate_marketing_plan(self, product: str, target: str, goal: str) -> Dict:
        try:
            print(f"\n开始生成营销方案...")
            print(f"产品: {product}")
            print(f"目标受众: {target}")
            print(f"营销目标: {goal}\n")
            
            # 创建任务描述
            task_description = f"为产品「{product}」制定针对「{target}」的营销方案，目标是「{goal}」"

            # 初始化营销专家和决策者代理
            assistant_sys_msg = SystemMessage(content=self.assistant_inception_prompt.format(
                assistant_role_name=self.assistant_role_name,
                user_role_name=self.user_role_name,
                task=task_description
            ))
            
            assistant_agent = MarketingCAMELAgent(assistant_sys_msg, self.llm)

            # 开始多轮对话
            dialog_turns = [
                # 第一轮：提出初步方案
                f"请为{product}制定初步的营销方案框架。考虑目标受众是{target}，主要目标是{goal}。",
                
                # 第二轮：细化执行计划
                "请详细说明这个方案的具体执行步骤、时间表和预算分配。",
                
                # 第三轮：讨论风险和应对
                "这个方案可能存在哪些风险？我们应该如何预防和应对？",
                
                # 第四轮：评估和优化
                "请说明如何评估方案效果，以及根据反馈进行优化的机制。"
            ]

            conversation = []
            for i, turn in enumerate(dialog_turns, 1):
                print(f"\n=== 对话回合 {i} ===")
                print(f"问题: {turn}")
                response = assistant_agent.step(HumanMessage(content=turn))
                print(f"{'='*30}")
                
                conversation.append({
                    "round": len(conversation) // 2 + 1,
                    "question": turn,
                    "answer": response.content
                })

            print("\n营销方案生成完成！")
            # 返回结构化的对话记录
            return {
                "status": "success",
                "context": {
                    "product": product,
                    "target": target,
                    "goal": goal
                },
                "conversation": conversation
            }
            
        except Exception as e:
            print(f"\n生成营销方案时出错: {str(e)}")
            logger.error(f"生成营销方案时出错: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "conversation": []
            }

    def refine_plan(self, initial_plan: str, feedback: str) -> Dict:
        """基于反馈优化营销方案"""
        try:
            print(f"\n开始优化营销方案...")
            print(f"收到反馈: {feedback}\n")
            
            # 创建优化任务描述
            task_description = f"基于以下反馈优化营销方案：\n{feedback}"

            # 初始化代理
            assistant_sys_msg = SystemMessage(content=self.assistant_inception_prompt.format(
                assistant_role_name=self.assistant_role_name,
                user_role_name=self.user_role_name,
                task=task_description
            ))
            
            assistant_agent = MarketingCAMELAgent(assistant_sys_msg, self.llm)

            # 优化对话流程
            dialog_turns = [
                # 分析反馈
                f"请分析以下反馈的关键点：\n{feedback}",
                
                # 提出优化方案
                "基于这些反馈，请提出具体的优化建议。",
                
                # 完善细节
                "请详细说明如何落实这些优化建议。"
            ]

            conversation = []
            for i, turn in enumerate(dialog_turns, 1):
                print(f"\n=== 优化回合 {i} ===")
                print(f"问题: {turn}")
                response = assistant_agent.step(HumanMessage(content=turn))
                print(f"{'='*30}")
                
                conversation.append({
                    "round": len(conversation) // 2 + 1,
                    "question": turn,
                    "answer": response.content
                })

            print("\n营销方案优化完成！")
            return {
                "status": "success",
                "context": {
                    "original_plan": initial_plan,
                    "feedback": feedback
                },
                "conversation": conversation
            }
            
        except Exception as e:
            print(f"\n优化营销方案时出错: {str(e)}")
            logger.error(f"优化营销方案时出错: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "conversation": []
            }
