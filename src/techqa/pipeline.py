from pathlib import Path

from corpus.tools import label_corpus, read_corpus_entries, read_corpus_segments, save_tokenized_corpus, tokenize_corpus
from typing import Annotated, Optional
import tqdm
import typer

import spacy


def read_techqa_corpus(inpf):
    '''A generator that reads the TechQA corpus and yields documents'''
    extension = inpf.split(".")[-1]
    assert (extension == "jsonl")
    assert os.path.exists(inpf)

    with open(inpf, "rb") as fr:
        # incremental json, avoids loading the entire file into memory
        for passage in jsonlines(fr, '', multiple_values=is_jsonl):
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


def main(
    input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="Path to the .jsonl corpus file")],
    output_path: Annotated[Optional[Path],
                           typer.Argument(dir_okay=False, help="Path to the output DocBin")] = None,
    batch_size: Annotated[int, typer.Option(
        help="Batch size for processing")] = 1024,
    processes: Annotated[int, typer.Option(
        help="Number of processes to use for NER recognition")] = 1,
    segment_size: Annotated[int, typer.Option(
        help="Number of words per input segment")] = None
):
    language = spacy.load("en_core_web_sm")
    inputs = read_corpus_entries(
        input_path) if segment_size is None else read_corpus_segments(input_path, segment_size)
    docs = label_corpus(tqdm.tqdm(inputs), language, batch_size, processes)
    if output_path is not None:
        save_tokenized_corpus(docs, output_path)
    else:
        total_length = 0
        for doc in docs:
            total_length += len(doc)
        print(f"Total length of corpus: {total_length}")

if __name__ == "__main__":
    typer.run(main)
