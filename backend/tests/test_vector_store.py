import pytest
from app.services.vector.chroma_store import ChromaVectorStore


@pytest.mark.anyio
async def test_chroma_vector_store():
    # Use in-memory Chroma instance for test isolation and multi-platform compatibility
    store = ChromaVectorStore(persist_directory=":memory:")
    collection_name = "test_vendors"

    # 1. Upsert documents
    ids = ["vendor_1", "vendor_2", "vendor_3"]
    docs = [
        "Apex Industrial Hardware and Fasteners LLC",
        "Global Freight Transport and Logistics Inc",
        "Pacific Cloud Software Solutions Corp",
    ]
    metadatas = [
        {"user_id": "user_1", "category": "hardware"},
        {"user_id": "user_1", "category": "logistics"},
        {"user_id": "user_1", "category": "software"},
    ]

    await store.upsert(
        collection_name=collection_name,
        ids=ids,
        documents=docs,
        metadatas=metadatas,
    )

    # 2. Query similar
    results = await store.query_similar(
        collection_name=collection_name,
        query_text="Apex Fasteners and Hardware",
        n_results=1,
    )

    assert len(results) == 1
    assert results[0]["id"] == "vendor_1"
    assert "Apex" in results[0]["document"]
    assert results[0]["metadata"]["category"] == "hardware"

    # 3. Query with metadata filter
    filtered_results = await store.query_similar(
        collection_name=collection_name,
        query_text="Logistics cargo shipment",
        n_results=2,
        where={"category": "logistics"},
    )
    assert len(filtered_results) >= 1
    assert filtered_results[0]["id"] == "vendor_2"

    # 4. Delete document
    await store.delete(collection_name=collection_name, ids=["vendor_1"])
    after_delete = await store.query_similar(
        collection_name=collection_name,
        query_text="Apex Fasteners and Hardware",
        n_results=1,
    )
    if len(after_delete) > 0:
        assert after_delete[0]["id"] != "vendor_1"

    # 5. Clean up collection
    await store.delete_collection(collection_name=collection_name)
