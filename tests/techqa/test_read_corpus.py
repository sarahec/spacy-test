from src.techqa.read_corpus import read_techqa_corpus


def test_read_techqa_corpus():
    inpf = "data/corpus.jsonl"
    for snippet in read_techqa_corpus(inpf):
        assert "id" in snippet
        assert "title" in snippet
        assert "text" in snippet
        assert "metadata" in snippet
        assert "chunk_ind" in snippet
        assert snippet["text"] != ""
