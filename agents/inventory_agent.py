from typing import Dict, List, Optional, Any, Deque
from collections import deque
from datetime import datetime
import os
import logging
from langchain.chains import LLMChain
from langchain.chains.base import Chain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.vectorstores.base import VectorStore
from langchain_community.vectorstores import FAISS
from langchain.pydantic_v1 import BaseModel, Field
from tools.inventory_tools import InventoryTools
from langchain_community.docstore.in_memory import InMemoryDocstore
import faiss
from chatbot import SentenceBERTEmbeddings  # 导入统一的嵌入模型

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskCreationChain(LLMChain):
    @classmethod
    def from_llm(cls, llm, verbose=True):
        template = """基于目标：{objective}
        创建2-3个关键任务，考虑:
        1. 外部环境分析(天气、节日、社交媒体)
        2. 库存策略制定(水平、补货、物流)
        
        已完成：{task_description}
        待完成：{incomplete_tasks}
        上次结果：{result}
        """
        prompt = PromptTemplate(
            template=template,
            input_variables=["objective", "result", "task_description", "incomplete_tasks"]
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

class TaskPrioritizationChain(LLMChain):
    @classmethod 
    def from_llm(cls, llm, verbose=True):
        template = """对以下库存管理任务进行优先级排序：{task_names}
        考虑团队的最终目标：{objective}
        从{next_task_id}开始，将结果作为编号列表返回，例如：
        1. 第一个任务
        2. 第二个任务
        """
        prompt = PromptTemplate(
            template=template,
            input_variables=["task_names", "objective", "next_task_id"]
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

class ExecutionChain(LLMChain):
    @classmethod
    def from_llm(cls, llm, verbose=True):
        template = """任务：{task}
        目标：{objective}
        上下文：{context}
        
        请简明扼要地给出执行结果。
        """
        prompt = PromptTemplate(
            template=template, 
            input_variables=["objective", "task", "context"]
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

class InventoryAGI(Chain):
    """基于BabyAGI的库存管理智能代理"""
    
    task_creation_chain: TaskCreationChain = Field(...)
    task_prioritization_chain: TaskPrioritizationChain = Field(...) 
    execution_chain: ExecutionChain = Field(...)
    vectorstore: VectorStore = Field(...)
    max_iterations: Optional[int] = Field(default=None)
    tools: InventoryTools = Field(...)
    task_list: Deque = Field(default_factory=deque)
    task_id_counter: int = Field(default=1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def input_keys(self) -> List[str]:
        return ["objective"]

    @property
    def output_keys(self) -> List[str]:
        return []

    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行主循环"""
        objective = inputs["objective"]
        first_task = inputs.get("first_task", "评估产品库存需求")
        all_results = []
        
        # 设定固定任务列表
        fixed_tasks = [
            {"task_id": 1, "task_name": "分析天气和节假日影响"},
            {"task_id": 2, "task_name": "评估社交媒体趋势"},
            {"task_id": 3, "task_name": "制定库存策略建议"}
        ]
        
        # 执行固定任务列表
        for task in fixed_tasks:
            self._print_next_task(task)
            
            # 执行任务
            result = self._execute_task(
                objective=objective,
                task=task["task_name"]
            )
            self._print_task_result(result)
            
            # 存储结果
            if result and not result.startswith("任务执行出错"):
                all_results.append(result)
                self.vectorstore.add_texts(
                    texts=[result],
                    metadatas=[{"task": task["task_name"]}],
                    ids=[f"result_{task['task_id']}"]
                )
                
        return {"results": all_results}

    def _execute_task(self, objective: str, task: str) -> str:
        """执行单个任务"""
        try:
            # 初始化上下文
            context = []
            product_name = objective.split()[0]
            task_result = ""
            
            # 如果向量存储中有数据，尝试获取相关任务
            if self.vectorstore.index.ntotal > 0:
                try:
                    context = self._get_top_tasks(query=objective)
                except Exception as e:
                    logger.warning(f"获取历史任务失败: {str(e)}")
            
            # 使用工具执行具体分析
            if "天气分析" in task.lower():
                weather_impact = self.tools.get_weather_impact(
                    product=product_name,
                    location="全国主要城市",
                    season=self._get_current_season()
                )
                task_result = f"天气分析结果：{weather_impact}"
                
            elif "社交趋势" in task.lower():
                social_trends = self.tools.get_social_trends(
                    product=product_name
                )
                task_result = f"社交趋势分析：{social_trends}"
                
            elif "节日影响" in task.lower():
                events = self.tools.get_seasonal_events(
                    product=product_name,
                    timeframe="3个月"
                )
                task_result = f"节日影响分析：{events}"
            
            # 使用执行链处理任务
            if not task_result:  # 如果没有使用特定工具
                chain_response = self.execution_chain.run(
                    objective=objective,
                    task=task,
                    context="\n".join(context) if context else "暂无相关上下文"
                )
                task_result = str(chain_response)

            if not task_result:
                task_result = "任务执行完成，但未产生具体结果"
                
            return task_result
                
        except Exception as e:
            logger.error(f"任务执行失败: {str(e)}", exc_info=True)
            return f"任务执行出错: {str(e)}"

    def _get_next_tasks(self, result: str, task_description: str, objective: str) -> List[Dict]:
        """生成新任务"""
        try:
            response = self.task_creation_chain.run(
                result=result,
                task_description=task_description,
                incomplete_tasks=", ".join(t["task_name"] for t in self.task_list),
                objective=objective
            )
            
            if not isinstance(response, str):
                response = str(response)
                
            new_tasks = []
            for task in response.split("\n"):
                if task.strip():
                    new_tasks.append({"task_name": task.strip()})
                    
            if not new_tasks:
                # 如果没有新任务，添加一个总结任务
                new_tasks.append({"task_name": "总结库存管理策略建议"})
                
            return new_tasks
            
        except Exception as e:
            logger.error(f"生成新任务失败: {str(e)}", exc_info=True)
            return [{"task_name": "总结已完成的分析结果"}]

    def _prioritize_tasks(self, this_task_id: int, task_list: List[Dict], objective: str) -> List[Dict]:
        """对任务进行优先级排序"""
        task_names = [t["task_name"] for t in task_list]
        response = self.task_prioritization_chain.run(
            task_names=task_names,
            next_task_id=this_task_id + 1,
            objective=objective
        )
        
        prioritized_tasks = []
        for line in response.split("\n"):
            if not line.strip():
                continue
            # 解析任务ID和名称
            parts = line.strip().split(".", 1)
            if len(parts) == 2:
                task_id = int(parts[0].strip())
                task_name = parts[1].strip()
                prioritized_tasks.append({
                    "task_id": task_id,
                    "task_name": task_name
                })
        return prioritized_tasks

    def _get_top_tasks(self, query: str, k: int = 5) -> List[str]:
        """获取相关任务历史"""
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [str(item.metadata["task"]) for item, _ in results]

    def _get_current_season(self) -> str:
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "春季"
        elif month in [6, 7, 8]:
            return "夏季"
        elif month in [9, 10, 11]:
            return "秋季"
        else:
            return "冬季"

    def _print_task_list(self):
        """打印任务列表"""
        print("\n=== 当前任务列表 ===")
        for t in self.task_list:
            print(f"{t['task_id']}: {t['task_name']}")

    def _print_next_task(self, task: Dict):
        """打印下一个任务"""
        print(f"\n=== 执行任务 ===\n{task['task_id']}: {task['task_name']}")

    def _print_task_result(self, result: str):
        """打印任务结果"""
        print(f"\n=== 执行结果 ===\n{result}")

    def add_task(self, task: Dict):
        """添加任务到任务列表"""
        if not hasattr(self, 'task_list'):
            self.task_list = deque()
        self.task_list.append(task)

    def execute_strategy(self, product: str, city: str = "全国") -> Dict:
        """执行完整的库存管理策略"""
        try:
            print(f"\n{'='*50}")
            print(f"开始分析 {city} 地区的 {product} 库存策略")
            print(f"{'='*50}\n")
            
            # 执行分析
            result = self.invoke(
                input={
                    "objective": f"为{city}地区的{product}制定库存策略"
                }
            )
            
            # 整理结果
            analysis_results = []
            strategy_results = []
            logistics_results = []
            weather_impact = {}
            social_trends = {}
            seasonal_events = []
            
            if isinstance(result.get("results"), list):
                for r in result["results"]:
                    r_str = str(r)
                    print(f"\n分析结果:")
                    print(f"{'-'*30}")
                    print(r_str)
                    print(f"{'-'*30}")
                    
                    if "天气分析" in r_str:
                        weather_impact = self._parse_weather_result(r_str)
                    elif "社交趋势" in r_str:
                        social_trends = self._parse_social_result(r_str)
                    elif "节日" in r_str:
                        seasonal_events = self._parse_events_result(r_str)
                    elif "策略" in r_str:
                        strategy_results.append(r_str)
                    elif "物流" in r_str:
                        logistics_results.append(r_str)
                    else:
                        analysis_results.append(r_str)

            print(f"\n{'='*50}")
            print("库存策略分析完成")
            print(f"{'='*50}\n")
            
            # 返回结构化数据
            return {
                "weather_impact": weather_impact or {
                    "impact": "暂无天气影响分析",
                    "behavior_changes": "",
                    "demand_forecast": "",
                    "recommendations": ""
                },
                "social_trends": social_trends or {
                    "market_heat": "暂无社交趋势分析",
                    "discussion_focus": "",
                    "reputation_trend": "",
                    "related_topics": ""
                },
                "seasonal_events": seasonal_events or [],
                "strategy": self._format_strategy_result(strategy_results, city),
                "logistics": self._format_logistics_result(logistics_results, city),
                "status": "success"
            }
            
        except Exception as e:
            print(f"\n策略执行失败: {str(e)}")
            logger.error(f"策略执行失败: {str(e)}", exc_info=True)
            return {
                "weather_impact": {},
                "social_trends": {},
                "seasonal_events": [],
                "strategy": {},
                "logistics": {},
                "status": "error"
            }

    def _parse_weather_result(self, text: str) -> Dict:
        """解析天气分析结果"""
        parts = text.split("\n")
        return {
            "impact": next((p.split("：")[-1] for p in parts if "影响" in p), ""),
            "behavior_changes": next((p.split("：")[-1] for p in parts if "行为" in p), ""),
            "demand_forecast": next((p.split("：")[-1] for p in parts if "预测" in p), ""),
            "recommendations": next((p.split("：")[-1] for p in parts if "建议" in p), "")
        }

    def _parse_social_result(self, text: str) -> Dict:
        """解析社交趋势结果"""
        parts = text.split("\n")
        return {
            "market_heat": next((p.split("：")[-1] for p in parts if "热度" in p), ""),
            "discussion_focus": next((p.split("：")[-1] for p in parts if "焦点" in p), ""),
            "reputation_trend": next((p.split("：")[-1] for p in parts if "趋势" in p), ""),
            "related_topics": next((p.split("：")[-1] for p in parts if "话题" in p), "")
        }

    def _parse_events_result(self, text: str) -> List[Dict]:
        """解析节日活动结果"""
        events = []
        current_event = None
        
        for line in text.split("\n"):
            if "：" in line:
                if current_event:
                    events.append(current_event)
                event_name = line.split("：")[0]
                current_event = {"event": event_name, "impact": [line.split("：")[1]]}
            elif line.strip() and current_event:
                current_event["impact"].append(line.strip())
                
        if current_event:
            events.append(current_event)
            
        return events

    def _format_strategy_result(self, results: List[str], city: str) -> Dict:
        """格式化策略建议"""
        return {
            "suggested_level": f"建议{city}地区维持适度库存水平",
            "reorder_time": "根据销售周期动态调整",
            "safety_stock": "建议设置安全库存以应对需求波动",
            "recommendations": "\n".join(results)[:200] if results else "暂无具体建议"
        }

    def _format_logistics_result(self, results: List[str], city: str) -> Dict:
        """格式化物流方案"""
        return {
            "routes": f"优化{city}地区配送路线",
            "resources": "合理分配运力资源",
            "timeliness": "确保准时配送",
            "cost_optimization": "\n".join(results)[:200] if results else "采用标准配送方案"
        }

    @classmethod
    def from_llm(cls, llm, vectorstore, tools, **kwargs):
        """初始化库存AGI代理"""
        task_creation_chain = TaskCreationChain.from_llm(llm)
        task_prioritization_chain = TaskPrioritizationChain.from_llm(llm)
        execution_chain = ExecutionChain.from_llm(llm)
        
        return cls(
            task_creation_chain=task_creation_chain,
            task_prioritization_chain=task_prioritization_chain,
            execution_chain=execution_chain,
            vectorstore=vectorstore,
            tools=tools,
            **kwargs
        )
    
    @staticmethod
    def create_default_agent():
        """创建默认配置的库存AGI代理"""
        embeddings = SentenceBERTEmbeddings()
        
        # 初始化向量存储
        vectorstore = FAISS.from_texts(
            texts=["初始化文本"],
            embedding=embeddings,
            metadatas=[{"task": "init"}]
        )
        
        llm = ChatOpenAI(
            model=os.environ["LLM_MODELEND"],
            temperature=0.3  # 降低随机性
        )
        
        return InventoryAGI.from_llm(
            llm=llm,
            vectorstore=vectorstore,
            tools=InventoryTools(llm=llm),
            max_iterations=3  # 减少迭代次数
        )

