from typing import Dict, List
import os
from datetime import datetime
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from database.db import InventoryDB
from tools.inventory_tools import InventoryTools
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InventoryAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.environ["LLM_MODELEND"],
            temperature=0.5
        )
        self.db = InventoryDB()
        self.tools = InventoryTools()
        self.task_list = []
        
        # 初始化任务创建模板
        self.creation_prompt = PromptTemplate(
            input_variables=["product", "analysis_results", "completed_tasks"],
            template="""基于以下产品分析结果：{analysis_results}
            已完成任务：{completed_tasks}
            
            请为产品 {product} 创建库存管理子任务，需要考虑：
            1. 外部因素分析（天气、节日、社交媒体）
            2. 库存水平建议
            3. 补货时间规划
            4. 物流配送优化
            
            每个任务需要具体且可执行。
            
            请列出接下来要执行的任务："""
        )
        
        # 初始化策略生成模板
        self.strategy_prompt = PromptTemplate(
            input_variables=["product", "analysis_results"],
            template="""基于以下分析结果：{analysis_results}
            
            请为产品 {product} 制定详细的库存策略：
            1. 建议库存水平
            2. 补货时间点
            3. 安全库存量
            4. 物流配送方案
            
            制定策略时需考虑所有影响因素。
            
            详细建议："""
        )
        
        self.task_chain = LLMChain(llm=self.llm, prompt=self.creation_prompt)
        self.strategy_chain = LLMChain(llm=self.llm, prompt=self.strategy_prompt)

    def analyze_factors(self, product: str, location: str = "全国主要城市") -> Dict:
        """分析产品的影响因素"""
        try:
            # 获取当前季节
            current_season = self._get_current_season()
            logger.info(f"开始分析 {product} 的影响因素")
            
            # 使用tools进行分析
            weather_impact = self.tools.get_weather_impact(
                product=product,
                location=location,
                season=current_season
            )
            logger.info("完成天气影响分析")
            
            social_trends = self.tools.get_social_trends(product)
            logger.info("完成社交媒体趋势分析")
            
            seasonal_events = self.tools.get_seasonal_events(
                product=product,
                timeframe="3个月"
            )
            logger.info("完成节日影响分析")
            
            analysis_results = {
                "weather_impact": weather_impact,
                "social_trends": social_trends,
                "seasonal_events": seasonal_events
            }
            
            # 修改数据库记录格式
            record = {
                "product": product,
                "timestamp": datetime.now().isoformat(),
                "factors": analysis_results,
                "strategy": {},  # 添加空策略字段
                "logistics": {}  # 添加空物流字段
            }
            
            # 保存分析结果
            self.db.add_record(record)
            logger.info("保存分析结果到数据库")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"产品影响因素分析失败: {str(e)}")
            return {}

    def create_tasks(self, product: str, analysis_results: Dict) -> List[Dict]:
        """创建任务列表"""
        try:
            response = self.task_chain.invoke({
                "product": product,
                "analysis_results": str(analysis_results),
                "completed_tasks": str(self.task_list)
            })
            
            tasks = []
            for line in response["text"].split("\n"):
                if line.strip():
                    tasks.append({
                        "description": line.strip(),
                        "status": "pending",
                        "created_at": datetime.now().isoformat()
                    })
            return tasks
        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            return []

    def generate_strategy(self, product: str, analysis_results: Dict) -> Dict:
        """生成库存策略"""
        try:
            response = self.strategy_chain.invoke({
                "product": product,
                "analysis_results": str(analysis_results)
            })
            
            return self._parse_strategy(response["text"])
        except Exception as e:
            logger.error(f"生成策略失败: {str(e)}")
            return {}

    def execute_strategy(self, product: str) -> Dict:
        """执行完整的库存策略流程"""
        try:
            # 1. 分析产品影响因素
            analysis_results = self.analyze_factors(product)  # 更新这里的方法调用
            logger.info("完成产品分析")
            
            # 2. 创建任务列表
            tasks = self.create_tasks(product, analysis_results)
            logger.info(f"创建了 {len(tasks)} 个任务")
            
            # 3. 生成策略
            strategy = self.generate_strategy(product, analysis_results)
            logger.info("生成库存策略")
            
            # 4. 保存到数据库
            record = {
                "product": product,
                "analysis": analysis_results,
                "tasks": tasks,
                "strategy": strategy,
                "timestamp": datetime.now().isoformat()
            }
            self.db.add_record(record)
            
            return {
                "analysis": analysis_results,
                "strategy": strategy,
                "tasks": tasks
            }
            
        except Exception as e:
            logger.error(f"策略执行失败: {str(e)}")
            return {}

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

    def _parse_strategy(self, text: str) -> Dict:
        """解析策略文本为结构化数据"""
        try:
            lines = text.split("\n")
            strategy = {
                "inventory_level": "",
                "reorder_point": "",
                "safety_stock": "",
                "logistics_plan": ""
            }
            
            current_key = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if "库存水平" in line:
                    current_key = "inventory_level"
                    strategy[current_key] = line.split("：")[-1] if "：" in line else line
                elif "补货时间" in line:
                    current_key = "reorder_point"
                    strategy[current_key] = line.split("：")[-1] if "：" in line else line
                elif "安全库存" in line:
                    current_key = "safety_stock"
                    strategy[current_key] = line.split("：")[-1] if "：" in line else line
                elif "物流方案" in line:
                    current_key = "logistics_plan"
                    strategy[current_key] = line.split("：")[-1] if "：" in line else line
                
            return strategy
            
        except Exception as e:
            logger.error(f"解析策略失败: {str(e)}")
            return {}

    def generate_inventory_strategy(self, product: str, factors: Dict, current_stock: int) -> Dict:
        """生成库存策略"""
        try:
            response = self.strategy_chain.invoke({
                "product": product,
                "analysis_results": str(factors)  # 使用传入的factors
            })
            
            # 解析策略并添加当前库存信息
            strategy = self._parse_strategy(response["text"])
            strategy["current_stock"] = current_stock
            
            return strategy
            
        except Exception as e:
            logger.error(f"生成库存策略失败: {str(e)}")
            return {}

    def optimize_logistics(self, strategy: Dict) -> Dict:
        """优化物流配送方案"""
        try:
            # 创建物流优化提示模板
            logistics_prompt = PromptTemplate(
                input_variables=["strategy"],
                template="""基于以下库存策略：
                {strategy}
                
                请优化物流配送方案，考虑：
                1. 配送路线规划
                2. 运力资源分配
                3. 时效性保障
                4. 成本优化方案
                
                给出具体建议："""
            )
            
            logistics_chain = LLMChain(llm=self.llm, prompt=logistics_prompt)
            response = logistics_chain.invoke({"strategy": str(strategy)})
            
            # 解析物流方案
            lines = response["text"].split("\n")
            logistics = {
                "routes": "",
                "resources": "",
                "timeliness": "",
                "cost_optimization": ""
            }
            
            current_key = None
            for line in lines:
                if not line.strip():
                    continue
                    
                if "配送路线" in line:
                    current_key = "routes"
                    logistics[current_key] = line.split("：")[-1] if "：" in line else line
                elif "运力资源" in line:
                    current_key = "resources"
                    logistics[current_key] = line.split("：")[-1] if "：" in line else line
                elif "时效性" in line:
                    current_key = "timeliness"
                    logistics[current_key] = line.split("：")[-1] if "：" in line else line
                elif "成本优化" in line:
                    current_key = "cost_optimization"
                    logistics[current_key] = line.split("：")[-1] if "：" in line else line
                elif current_key:
                    logistics[current_key] += "\n" + line
            
            return logistics
            
        except Exception as e:
            logger.error(f"优化物流方案失败: {str(e)}")
            return {}

    def update_inventory_history(self, data: Dict):
        """更新库存历史记录"""
        try:
            # 确保数据结构完整
            record = {
                "product": data.get("product", ""),
                "timestamp": datetime.now().isoformat(),
                "factors": data.get("factors", {}),
                "strategy": data.get("strategy", {}),
                "logistics": data.get("logistics", {})
            }
            
            self.db.add_record(record)
            logger.info(f"已更新库存历史记录: {record['product']}")
        except Exception as e:
            logger.error(f"更新历史记录失败: {str(e)}")

