from typing import Optional, List, Dict
from fastapi import FastAPI
from fastapi import File, UploadFile
import shutil
from pydantic import BaseModel
from datetime import date
import json, os
import uvicorn
from langchain_community.llms import Ollama
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains.retrieval import create_retrieval_chain
from pathlib import Path


app = FastAPI()

folder_path = os.path.join(os.path.dirname(__file__), "db")
pdf_dir = os.path.join(os.path.dirname(__file__), "pdf_drive")

Path(folder_path).mkdir(parents=True, exist_ok=True)
Path(pdf_dir).mkdir(parents=True, exist_ok=True)

cached_llm = Ollama(model="llama3")

embedding = FastEmbedEmbeddings()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=80, length_function=len, is_separator_regex=False
)
prompt = PromptTemplate.from_template(
    """ 
    <s>[INST] You are a technical assistant good at searching docuemnts. If you do not have an answer from the provided information say so. [/INST] </s>
    [INST] Generate response in markdown format [/INST]
    [INST] {input}
           Context: {context}
           Answer:
    [/INST]
"""
)

class Query(BaseModel):
    text: str

class PDFFiles(BaseModel):
    file_names: List[str]

@app.post("/ai")
def ai_post(query: Query):

    print("query is ", query)
    response = cached_llm.invoke(query.text)
    print (response)
    return {"llm_response": response}


@app.post("/pdf_post")
def pdf_post(pdf_file: UploadFile = File(...)):
    save_file = os.path.join(pdf_dir, pdf_file.filename)
    with open(save_file, 'wb') as f:
        shutil.copyfileobj(pdf_file.file, f)

    pdf_loader = PDFPlumberLoader(save_file)
    docs = pdf_loader.load_and_split()

    print (f"docs length = {len(docs)}")

    chunks = text_splitter.split_documents(docs)
    print (f"chunks len={len(chunks)}")

    vector_store = Chroma.from_documents(
        documents=chunks, embedding=embedding, persist_directory=folder_path
    )

    vector_store.persist()

    return {
        "status" : "Successfully Uploaded",
        "filename": pdf_file.filename,
        "content_type": pdf_file.content_type,
        "doc_len":len(docs),
        "chunks": len(chunks)
    }

@app.post("/query_pdf")
def query_pdf(query: Query):
    query = query.text
    vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)

    print ("creating chain...")
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 20,
            "score_threshold": 0.1,
        }
    )

    document_chain = create_stuff_documents_chain(cached_llm, prompt)
    chain = create_retrieval_chain(retriever, document_chain)
    result = chain.invoke({"input": query})
    print(result)

    sources = []
    for doc in result["context"]:
        sources.append(
            {"source": doc.metadata["source"], "page_content": doc.page_content}
        )

    response_answer = {"answer": result["answer"], "sources": sources}
    # with open('output2.md', 'w+') as f:
    #     f.write(response_answer["answer"])
    return response_answer

def serve_chain_api():
    uvicorn.run(app, host='0.0.0.0', port=5000 )

if __name__ == "__main__":
    # Serve the app with uvicorn
    serve_chain_api()