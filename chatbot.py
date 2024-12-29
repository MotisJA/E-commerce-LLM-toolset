import os
import gradio as gr
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain.memory.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory  # 改用基础的对话缓存
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import TextLoader
from typing import Dict, List, Any
from langchain.embeddings.base import Embeddings
from pydantic import BaseModel
from volcenginesdkarkruntime import Ark
from langchain_openai import ChatOpenAI  # ChatOpenAI模型
from sentence_transformers import SentenceTransformer
from langchain_experimental.plan_and_execute import (
    PlanAndExecute,
    load_agent_executor,
    load_chat_planner,
)
from langchain.agents import Tool
from langchain.chains import LLMMathChain

class SentenceBERTEmbeddings(Embeddings):  # 继承Embeddings基类
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

    class Config:
        arbitrary_types_allowed = True


class ChatbotWithRetrieval:
    def __init__(self, dir):

        # 加载Documents
        base_dir = dir  # 文档的存放目录
        documents = []
        for file in os.listdir(base_dir):
            file_path = os.path.join(base_dir, file)
            if file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif file.endswith(".docx") or file.endswith(".doc"):
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
            elif file.endswith(".txt"):
                loader = TextLoader(file_path)
                documents.extend(loader.load())

        # 文本的分割
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0)
        all_splits = text_splitter.split_documents(documents)

        # 向量数据库
        self.vectorstore = Qdrant.from_documents(
            documents=all_splits,  # 以分块的文档
            embedding=SentenceBERTEmbeddings(),  # 用OpenAI的Embedding Model做嵌入
            location=":memory:",  # in-memory 存储
            collection_name="my_documents",
        )  # 指定collection_name

        # 初始化LLM和向量数据库
        self.llm = ChatOpenAI(
            model=os.environ["LLM_MODELEND"],
            temperature=0,
        )
        
        # 创建工具集
        llm_math_chain = LLMMathChain.from_llm(llm=self.llm, verbose=True)
        self.tools = [
            Tool(
                name="VectorDBSearch",
                func=self._search_docs,
                description="用于搜索文档数据库获取相关信息",
            ),
            Tool(
                name="Calculator",
                func=llm_math_chain.run,
                description="用于执行数学计算",
            ),
        ]
        
        # 初始化Plan-and-Execute代理
        self.planner = load_chat_planner(self.llm)
        self.executor = load_agent_executor(self.llm, self.tools, verbose=True)
        self.agent = PlanAndExecute(
            planner=self.planner,
            executor=self.executor,
            verbose=True
        )
        
        # 修改内存初始化
        self.memory = ConversationBufferMemory(  # 使用更简单的内存模型
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # 初始化对话历史
        self.conversation_history = ""

    def _search_docs(self, query: str) -> str:
        """搜索文档数据库"""
        docs = self.vectorstore.similarity_search(query, k=3)
        return "\n".join([doc.page_content for doc in docs])

    def get_response(self, user_input: str) -> str:
        try:
            # 使用Plan-and-Execute代理处理查询
            task_prompt = f"""基于用户的问题："{user_input}"
            
请分析并回答这个问题。考虑以下几点：
1. 是否需要搜索文档获取信息
2. 是否需要进行计算
3. 如何整合多个步骤的结果
4. 如何给出清晰的解释

请制定详细的执行计划并执行。"""

            # 执行计划并获取结果
            response = self.agent.run(task_prompt)
            
            # 更新对话历史
            self.conversation_history += (
                f"你: {user_input}\nChatbot: {response}\n"
            )
            
            return self.conversation_history
            
        except Exception as e:
            print(f"处理查询时出错: {str(e)}")
            return "抱歉，我暂时无法处理您的问题，请稍后再试。"

if __name__ == "__main__":
    
    folder = "docs"
    bot = ChatbotWithRetrieval(folder)

    # 更新 Gradio 界面配置
    interface = gr.Interface(
        fn=bot.get_response,
        inputs="text",
        outputs="text",
        live=False,
        title="易速鲜花智能客服",
        description="请输入问题，然后点击提交。"
    )
    
    # 使用正确的launch参数
    interface.queue()  # 启用队列
    interface.launch(
        share=False,
        server_name="127.0.0.1"
    )  # 启动 Gradio 界面
