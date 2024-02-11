from src.techqa.pipeline import read_techqa_corpus, run_pipeline, post_process_docs


def test_read_techqa_corpus():
    inpf = "data/corpus.jsonl"
    for snippet in read_techqa_corpus(inpf):
        assert "id" in snippet
        assert "title" in snippet
        assert "text" in snippet
        assert "metadata" in snippet
        assert "chunk_ind" in snippet
        assert snippet["text"] != ""


def test_run_pipeline():
    inpf = "data/corpus.jsonl"
    corpus = read_techqa_corpus(inpf)
    result = run_pipeline(corpus)
    assert result is not None
    for doc in result:
        assert doc is not None
        assert post_process_docs(doc) is not None
