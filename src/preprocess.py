from pathlib import Path

from techqa_tools import read_corpus_entries, read_corpus_segments, save_tokenized_corpus, tokenize_corpus
from typing import Annotated, Optional
import tqdm
import typer

import spacy

def main(
    input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="Path to the .jsonl corpus file")],
    output_path: Annotated[Optional[Path],
                           typer.Argument(dir_okay=False, help="Path to the output DocBin")] = None,
    batch_size: Annotated[int, typer.Option(
        help="Batch size for processing")] = 1024,
    processes: Annotated[int, typer.Option(
        help="Number of processes to use for tokenization")] = 1,
    segment_size: Annotated[int, typer.Option(
        help="Number of words per input segment")] = None
):
    language = spacy.load("en_core_web_sm")
    inputs = read_corpus_entries(
        input_path) if segment_size is None else read_corpus_segments(input_path, segment_size)
    docs = tokenize_corpus(tqdm.tqdm(inputs), language, batch_size, processes)
    if output_path is not None:
        save_tokenized_corpus(docs, output_path)
    else:
        total_length = 0
        for doc in docs:
            total_length += len(doc)
        print(f"Total length of corpus: {total_length}")
if __name__ == "__main__":
    typer.run(main)