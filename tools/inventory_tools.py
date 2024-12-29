from typing import Dict, List
import pandas as pd
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import logging

logger = logging.getLogger(__name__)

class InventoryTools:
    def __init__(self, llm=None):
        """允许注入LLM实例"""
        self.llm = llm or ChatOpenAI(
            model=os.environ["LLM_MODELEND"],
            temperature=0.7
        )
        self._init_tools()

    def _init_tools(self):
        # 天气分析
        weather_template = """基于{product}在{location}{season}的销售情况，分析天气影响。
        考虑：温度、降水、空气质量等因素。"""
        self.weather_chain = LLMChain(
            llm=self.llm, 
            prompt=PromptTemplate(
                template=weather_template,
                input_variables=["product", "location", "season"]
            )
        )

        # 社交趋势
        trends_template = """分析{product}的近期社交媒体趋势。
        考虑：讨论热度、消费者情绪、相关话题等。"""
        self.trends_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=trends_template,
                input_variables=["product"]
            )
        )

        # 节假日活动
        events_template = """预测未来{timeframe}内{product}的节假日销售情况。
        考虑：传统节日、促销活动、消费习惯等。"""
        self.events_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=events_template,
                input_variables=["product", "timeframe"]
            )
        )

    def get_weather_impact(self, product, location, season):
        try:
            return self.weather_chain.run(
                product=product,
                location=location,
                season=season
            )
        except Exception as e:
            logger.error(f"天气分析失败: {str(e)}")
            return "暂无天气分析数据"

    def get_social_trends(self, product):
        try:
            return self.trends_chain.run(product=product)
        except Exception as e:
            logger.error(f"社交趋势分析失败: {str(e)}")
            return "暂无社交趋势数据"

    def get_seasonal_events(self, product, timeframe):
        try:
            return self.events_chain.run(
                product=product,
                timeframe=timeframe
            )
        except Exception as e:
            logger.error(f"节假日分析失败: {str(e)}")
            return "暂无节假日活动数据"

    def _parse_weather_analysis(self, text: str) -> Dict:
        """将天气分析结果解析为结构化数据"""
        # 实现解析逻辑
        sections = text.split("\n\n")
        return {
            "impact": sections[0] if len(sections) > 0 else "",
            "behavior_changes": sections[1] if len(sections) > 1 else "",
            "demand_forecast": sections[2] if len(sections) > 2 else "",
            "recommendations": sections[3] if len(sections) > 3 else ""
        }

    def _parse_social_analysis(self, text: str) -> Dict:
        """将社交媒体分析结果解析为结构化数据"""
        # 实现解析逻辑
        sections = text.split("\n\n")
        return {
            "market_heat": sections[0] if len(sections) > 0 else "",
            "discussion_focus": sections[1] if len(sections) > 1 else "",
            "reputation_trend": sections[2] if len(sections) > 2 else "",
            "related_topics": sections[3] if len(sections) > 3 else ""
        }

    def _parse_events_analysis(self, text: str) -> List[Dict]:
        """将节日分析结果解析为结构化数据"""
        # 实现解析逻辑
        events = []
        sections = text.split("\n\n")
        for section in sections:
            if not section.strip():
                continue
            lines = section.split("\n")
            if len(lines) >= 2:
                events.append({
                    "event": lines[0],
                    "impact": lines[1:]
                })
        return events
