"""Azure AI Search: create the index, ingest documents from Blob Storage, and query (keyword / vector / hybrid)."""
import re
import sys
from functools import lru_cache

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
from azure.storage.blob import BlobServiceClient

from app import config
from app.llm import embed

EMBEDDING_DIMS = 1536  # text-embedding-3-small


class SearchError(RuntimeError):
    """Azure AI Search or Blob Storage failed (message is safe to show)."""


def _cred() -> AzureKeyCredential:
    return AzureKeyCredential(config.get("AZURE_SEARCH_KEY"))


@lru_cache(maxsize=1)
def _search_client() -> SearchClient:
    return SearchClient(config.get("AZURE_SEARCH_ENDPOINT"), config.get("AZURE_SEARCH_INDEX"), _cred())


def create_index() -> None:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="owner", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="last_reviewed", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMS,
            vector_search_profile_name="hnsw-profile",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
        profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-config")],
    )
    SearchIndexClient(config.get("AZURE_SEARCH_ENDPOINT"), _cred()).create_or_update_index(
        SearchIndex(name=config.get("AZURE_SEARCH_INDEX"), fields=fields, vector_search=vector_search)
    )


def _parse(markdown: str) -> dict:
    """Split a document into front-matter fields and body."""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", markdown.replace("\r\n", "\n"), re.S)
    if not m:
        raise SearchError("A document is missing its metadata header.")
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)
    return {**meta, "body": m.group(2).strip()}


def read_blob_documents() -> list[dict]:
    """Read every .md document from the Blob container using the signed-in Azure identity (no storage key)."""
    try:
        service = BlobServiceClient(config.get("AZURE_STORAGE_ACCOUNT_URL"), credential=DefaultAzureCredential())
        container = service.get_container_client(config.get("AZURE_STORAGE_CONTAINER"))
        return [
            _parse(container.download_blob(b.name).readall().decode("utf-8"))
            for b in container.list_blobs()
            if b.name.endswith(".md")
        ]
    except config.ConfigError:
        raise
    except SearchError:
        raise
    except Exception as exc:
        raise SearchError(f"Could not read documents from Blob Storage ({type(exc).__name__}). Are you signed in with 'az login'?") from exc


def ingest() -> int:
    create_index()
    docs = []
    for d in read_blob_documents():
        text = f"{d['title']}\n{d['body']}"
        docs.append(
            {
                "id": d["id"],
                "title": d["title"],
                "content": d["body"],
                "category": d["category"],
                "doc_type": d.get("type", ""),
                "owner": d.get("owner", ""),
                "last_reviewed": d.get("last_reviewed", ""),
                "embedding": embed(text),
            }
        )
    results = _search_client().upload_documents(docs)
    failed = [r.key for r in results if not r.succeeded]
    if failed:
        raise SearchError(f"Some documents failed to upload: {failed}")
    return len(docs)


def doc_count() -> int:
    return _search_client().get_document_count()


def search(query: str, mode: str = "hybrid", k: int = 4) -> list[dict]:
    """mode: 'keyword' | 'vector' | 'hybrid'. Returns [{id,title,category,content,score}]."""
    if not query or not query.strip():
        return []
    kwargs: dict = {"top": k, "select": ["id", "title", "category", "doc_type", "last_reviewed", "content"]}
    if mode in ("vector", "hybrid"):
        kwargs["vector_queries"] = [VectorizedQuery(vector=embed(query), k_nearest_neighbors=k, fields="embedding")]
    if mode in ("keyword", "hybrid"):
        kwargs["search_text"] = query
    try:
        results = _search_client().search(**kwargs)
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "category": r["category"],
                "last_reviewed": r.get("last_reviewed", ""),
                "content": r["content"],
                "score": float(r["@search.score"]),
            }
            for r in results
        ]
    except config.ConfigError:
        raise
    except Exception as exc:
        raise SearchError(f"Azure AI Search is unavailable right now ({type(exc).__name__}).") from exc


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        n = ingest()
        print(f"Ingested {n} documents into '{config.get('AZURE_SEARCH_INDEX')}'")
