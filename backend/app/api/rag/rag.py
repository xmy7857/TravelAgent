import chromadb
from sentence_transformers import SentenceTransformer
from modelscope import snapshot_download
from langchain.tools import tool, ToolRuntime

model_dir = snapshot_download("AI-ModelScope/bge-base-zh-v1.5")
model = SentenceTransformer(model_dir)
client = chromadb.PersistentClient(
    path="./chroma_db"
)

@tool
def rag(query: str, city: str):
    """
    用于查询小众景点
    Args: 
    query为查询语句，例如'上海有哪些适合拍照的小众景点？'
    city为计划旅游的城市，例如'上海'
    """
    print("正在查询小众景点")
    collection = client.get_collection(
        name="minority_spot"
    )

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )#将查询向量化

    results = collection.query(
        query_embeddings=[
            query_embedding.tolist()#把向量转化成列表
        ],
        n_results=5,
        where={"city": city}
    )#查询结果
    return results["metadatas"]


