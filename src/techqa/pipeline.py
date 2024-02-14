import ijson
import jsonlines
import math
import os
import spacy

nlp = spacy.load('en_core_web_sm')
assert (nlp is not None)

def read_techqa_corpus(inpf):
    '''A generator that reads the TechQA corpus and yields documents'''
    extension = inpf.split(".")[-1]
    assert (extension in ["jsonl", "json"])
    assert os.path.exists(inpf)

    is_jsonl = True if extension == "jsonl" else False

    with open(inpf, "rb") as fr:
        # incremental json, avoids loading the entire file into memory
        for passage in ijson.items(fr, '', multiple_values=is_jsonl):
            for snippet in preprocess_single_doc(passage):
                yield snippet


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


def run_pipeline(corpus, batchSize=1024, nProcesses=4):
  return nlp.pipe([d["text"] for d in corpus], batch_size=batchSize, n_process=nProcesses)


def post_process_docs(doc):
    tokens = []
    mentions = []
    for token in doc:
        if token.ent_iob_ == "B":
            mentions.append(len(tokens))
            tokens.append(token.text)
            continue
        if token.ent_iob_ == "I":
            tokens[-1] = "{} {}".format(tokens[-1], token.text)
            continue
        if token.ent_iob_ == "O":
            tokens.append(token.text)
    yield (tokens, mentions)


def main():
    inpf = "data/corpus.jsonl"
    count = 0
    corpus = read_techqa_corpus(inpf)
    assert corpus is not None
    result = run_pipeline(corpus, batchSize=1024, nProcesses=4)
    for doc in result:
      if post_process_docs(doc) is not None:
        count = count + 1
    print(count)


if __name__ == "__main__":
    main()
