import os
import gradio as gr

# 导入相关库
from langchain.utilities import SerpAPIWrapper
from langchain.agents import Tool
from langchain.tools.file_management.write import WriteFileTool
from langchain.tools.file_management.read import ReadFileTool
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_experimental.autonomous_agents import AutoGPT
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore

import faiss

# 初始化环境变量（假设已经在环境中设置）
# os.environ["SERPAPI_API_KEY"] = os.getenv("SERPAPI_API_KEY")

# 工具初始化
search = SerpAPIWrapper()
tools = [
    Tool(
        name="search",
        func=search.run,
        description="Useful for when you need to answer questions about current events. Ask targeted questions.",
    ),
    WriteFileTool(),
    ReadFileTool(),
]

# 设置文本嵌入模型和向量存储
embeddings_model = OpenAIEmbeddings()
embedding_size = 1536
index = faiss.IndexFlatL2(embedding_size)
vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})

# 构建 AutoGPT
agent = AutoGPT.from_llm_and_tools(
    ai_name="Jarvis",
    ai_role="Assistant",
    tools=tools,
    llm=ChatOpenAI(model_name="gpt-4", temperature=0, verbose=True),
    memory=vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.8}
    ),
)
# 打印 Auto-GPT 内部的 chain 日志
agent.chain.verbose = True
def ask_jarvis(question):
    try:
        response = agent.run([question])
        return response
    except Exception as e:
        return str(e) 

# 创建 Gradio 界面
iface = gr.Interface(
    fn=ask_jarvis,
    inputs=gr.Textbox(lines=2, placeholder="Enter your question here..."),
    outputs=gr.Textbox(label="Output"),
    title="Jarvis AI Assistant",
    description="Ask any question and Jarvis will try to provide the best answer using its tools and knowledge."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)