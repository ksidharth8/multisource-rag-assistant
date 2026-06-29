from pydantic import BaseModel, Field


class TextIngestRequest(BaseModel):
    collection_name: str
    source_name: str = "pasted_text"
    text: str


class UrlIngestRequest(BaseModel):
    collection_name: str
    url: str


class ChatMessage(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    collection_name: str
    question: str
    top_k: int = 5
    persona: str = "student"
    chat_history: list[ChatMessage] = Field(default_factory=list)


class IngestResponse(BaseModel):
    collection_name: str
    source_type: str
    source_name: str
    chunks_added: int
    characters: int


class SourceChunk(BaseModel):
    source_type: str
    source_name: str
    chunk_index: int | None = None
    text: str
    score: float | None = None
    metadata: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class HealthResponse(BaseModel):
    status: str
    database: str


class CollectionsResponse(BaseModel):
    collections: list[str]


class CollectionStatsResponse(BaseModel):
    collection_name: str
    documents: int
    chunks: int
    characters: int