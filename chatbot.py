import os
import gradio as gr
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain.memory import ConversationSummaryMemory
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

        # 初始化LLM
        self.llm = ChatOpenAI(
            model=os.environ["LLM_MODELEND"],
            temperature=0,
        )

        # 修正Memory初始化方式
        self.memory = ConversationSummaryMemory(
            llm=self.llm,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # 初始化对话历史
        self.conversation_history = ""

        # 设置Retrieval Chain
        retriever = self.vectorstore.as_retriever()
        self.qa = ConversationalRetrievalChain.from_llm(
            self.llm, retriever=retriever, memory=self.memory
        )

    def get_response(self, user_input):  # 这是为 Gradio 创建的新函数
        response = self.qa.invoke({"question": user_input})
        # 更新对话历史
        self.conversation_history += (
            f"你: {user_input}\nChatbot: {response['answer']}\n"
        )
        return self.conversation_history


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
