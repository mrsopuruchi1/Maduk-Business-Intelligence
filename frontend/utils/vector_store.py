import chromadb


client = chromadb.Client()


def store_insight(tenant_id, insight):

    collection = client.get_or_create_collection(
        name=f"tenant_{tenant_id}_insights"
    )

    collection.add(
        documents=[insight],
        ids=[str(hash(insight))]
    )
    
    
import chromadb

client = chromadb.Client()


def store_insight(tenant_id, insight):

    collection = client.get_or_create_collection(
        name=f"tenant_{tenant_id}_memory"
    )

    collection.add(
        documents=[insight],
        ids=[str(hash(insight))]
    )
    
    
import chromadb

# Initialize vector database
client = chromadb.Client()

def get_collection(name):

    return client.get_or_create_collection(name=name)


def store_vector(collection_name, document, metadata=None):

    collection = get_collection(collection_name)

    collection.add(
        documents=[document],
        metadatas=[metadata] if metadata else None,
        ids=[str(hash(document))]
    )


def search_vector(collection_name, query, limit=5):

    collection = get_collection(collection_name)

    results = collection.query(
        query_texts=[query],
        n_results=limit
    )

    return results
    
    
def remember(collection, insight):

    store_vector(collection, insight)
    
    
def recall(collection, query):

    return search_vector(collection, query)
    
    
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed(text):

    return model.encode(text).tolist()
    
    
def store_knowledge(collection, text):

    vector = embed(text)

    store_vector(collection, text, {"vector": vector})
    
    
def ai_consult(question):

    results = recall("business_memory", question)

    return results
    
    
import chromadb
from tenancy.tenant_context import TenantContext

# Initialize vector client
client = chromadb.Client()


def get_collection(tenant_id):

    return client.get_or_create_collection(
        name=f"tenant_{tenant_id}_memory"
    )


def store_vector(document, metadata=None):

    tenant_id = TenantContext.get_tenant()

    if not tenant_id:
        raise Exception("Tenant context not set")

    collection = get_collection(tenant_id)

    collection.add(
        documents=[document],
        metadatas=[metadata] if metadata else None,
        ids=[str(hash(document))]
    )


def search_vector(query, limit=5):

    tenant_id = TenantContext.get_tenant()

    if not tenant_id:
        raise Exception("Tenant context not set")

    collection = get_collection(tenant_id)

    results = collection.query(
        query_texts=[query],
        n_results=limit
    )

    return results
    
    
def remember(insight):

    store_vector(insight)
    
    
def recall(query):

    return search_vector(query)
    
    
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')


def embed(text):

    return model.encode(text).tolist()
    
    
def store_knowledge(text):

    vector = embed(text)

    store_vector(text, {"vector": vector})
    
    
def ai_consult(question):

    return recall(question)
    
    

    
    
    