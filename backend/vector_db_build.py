import chromadb
import os
from modelscope import snapshot_download
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

model_dir = snapshot_download(
    "AI-ModelScope/bge-base-zh-v1.5"
)

model = SentenceTransformer(model_dir)

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="minority_spot")


folder_str = "./docs"
folder = Path(folder_str)

json_files = list(folder.glob("*.json"))
for file in json_files:
    with open(Path(file),"r",encoding="utf-8") as f:#读取原文件，以json格式存储
        json_dict = json.load(f)
        metadata = [{"city": json_dict["city"],"name":spot["name"],"address":spot["address"]} for spot in json_dict["spot"]]#设置值
        print(f'{json_dict["city"]}小众景点数为{len(metadata)}')
        documents = [spot["description"] for spot in json_dict["spot"]]#设置键，用于编码
        start_idx = collection.count()
        ids = [f"chunk_{start_idx+i}" for i in range(len(metadata))]#设置id，必填
        embeddings = model.encode(
            documents,
            normalize_embeddings=True
        )
        collection.add(ids=ids,embeddings=embeddings,metadatas=metadata,documents=documents)#写入存储。document是键，metadata是值，也就是根据描述来搜索景点

query = "南京户外适合拍照的小众景点"
embedding_query = model.encode(query,normalize_embeddings=True)
query_results = collection.query(embedding_query,where={"city":"南京"},n_results=3)

for result in query_results["metadatas"]:
    print(result)


