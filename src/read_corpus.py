import jsonlines
import ijson
import math


def read_techqa_corpus(inpf):
    '''A generator that reads the TechQA corpus and yields documents'''
    extension = inpf.split(".")[-1]
    assert (extension in ["jsonl", "json"])
    if (extension == "jsonl"):
        with jsonlines.open(inpf, "r") as reader:
            for passage in reader:          # iteration avoids loading the entire file into memory
                yield preprocess_single_doc(passage)
    else:
        with open(inpf, "r") as fr:
            # incremental json, avoids loading the entire file into memory
            for passage in ijson.items(fr):
                yield preprocess_single_doc(passage)


def preprocess_single_doc(passage):
    snippets = []

    passage_tokens = passage["text"].split()
    passage_size = 64
    n_passages = math.ceil(1.0 * len(passage_tokens)/passage_size)
    for pind in range(n_passages):
        s = passage_size * pind
        e = min(passage_size * (pind + 1), len(passage_tokens))
        chunked_passage = " ".join(passage_tokens[s:e])
        snippets.append({
            "id": passage["id"],
            "title": passage["title"],
            "text": chunked_passage,
            "metadata": passage["metadata"],
            "chunk_ind": pind,
        })
    return snippets
