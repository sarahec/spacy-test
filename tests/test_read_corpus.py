# Fix the imports
from src.read_corpus import read_techqa_corpus


def test_read_techqa_corpus():
    inpf = "data/corpus.jsonl"
    for snippets in read_techqa_corpus(inpf):
        for snippet in snippets:
            assert "id" in snippet
            assert "title" in snippet
            assert "text" in snippet
            assert "metadata" in snippet
            assert "chunk_ind" in snippet
            assert snippet["text"] != ""
