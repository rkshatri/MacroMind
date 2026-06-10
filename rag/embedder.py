from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import os

def load_documents(knowledge_base_path):
    # Loop through all .txt files in knowledge_base. For each file use TextLoader to load it
    # as a LangChain document -> source content, metadata (filename). Return list of documents.
    docs = []
    for filename in os.listdir(knowledge_base_path):
        if filename.endswith('.txt'):
            print(f"Processing {filename}")
            filepath = os.path.join(knowledge_base_path, filename)
            loader = TextLoader(filepath)
            file_data = loader.load()
            docs.extend(file_data)

    print(f"Loaded {len(docs)} documents")
    return docs

def chunk_documents(docs):

    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " "],
        chunk_size=500,
        chunk_overlap=50,
        )
    chunks = splitter.split_documents(docs)

    print(f"Created {len(chunks)} chunks")
    return chunks

def build_vector_store(chunks, persist_path):
    print("Building vector store... (Ollama must be running)")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(persist_path)
    print(f"Vector store saved at {persist_path}")

def load_vector_store(persist_path):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return FAISS.load_local(persist_path, embeddings, allow_dangerous_deserialization=True)

if __name__ == "__main__":
    KB_PATH = "rag/knowledge_base"
    VS_PATH = "rag/vector_store"

    docs = load_documents(KB_PATH)
    chunks = chunk_documents(docs)
    build_vector_store(chunks, VS_PATH)

    # Check
    store = load_vector_store(VS_PATH)
    results = store.similarity_search("post workout protein", k=2)
    for r in results:
        print(r.metadata["source"])
        print(r.page_content)
        print()