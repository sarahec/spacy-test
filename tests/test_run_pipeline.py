from src.read_corpus import read_techqa_corpus
from src.run_pipeline import run_pipeline


def test_run_pipeline():
    inpf = "data/corpus.jsonl"
    corpus = read_techqa_corpus(inpf)
    result = run_pipeline(corpus)
    assert result is not None
    for doc in result:
        assert doc is not None
        assert len(doc) > 0
