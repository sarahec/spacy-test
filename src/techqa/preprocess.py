from statistics import fmean, pstdev
import jsonlines
import typer
from tqdm import tqdm
from typing import Annotated, Iterable, Dict, Optional
from pathlib import Path

import spacy
from spacy.tokens import DocBin, Doc
from spacy import Language


def load_corpus(docbin_path: Path, language: Language) -> Iterable[Doc]:
    doc_bin = DocBin().from_disk(docbin_path)
    for doc in doc_bin.get_docs(docbin_path, language.vocab):
        yield doc


def build_inputs(input_path: Path, language: Language, segment_size: Optional[int] = None) -> Iterable[Dict]:
    if segment_size is None:
        with jsonlines.open(input_path) as reader:
            for eg in reader:
                text = eg["text"]
                yield (eg["text"], {"id": eg["id"], "title": eg["title"], "metadata": eg["metadata"], "length": len(eg["text"]), "start": 0})
    else:
        with jsonlines.open(input_path) as reader:
            for eg in reader:
                text = eg["text"]
                spaces_idx = [i for i, c in enumerate(text) if c.isspace()]
                for i in range(0, len(spaces_idx), segment_size):
                    first = spaces_idx[i]
                    last = spaces_idx[i+segment_size] if i + \
                        segment_size < len(spaces_idx) else len(text)
                    segment = text[first:last]
                    yield (segment, {"id": eg["id"], "title": eg["title"], "metadata": eg["metadata"], "length": len(segment), "start": i})


def tokenize_corpus(input_path: Path, language: Language, output_path: Optional[Path], batch=1024, processes=1, segment_size=None):
    line_sizes = []
    nlp = spacy.blank("en", vocab=language.vocab)
    with jsonlines.open(input_path) as reader:
        # json_docs = list(reader)
        docs = nlp.pipe(build_inputs(input_path, language, segment_size),
                        batch_size=batch, n_process=processes, as_tuples=True)
    return process_docs(output_path, line_sizes, docs)


def process_docs(output_path, line_sizes, docs):
    if output_path is not None:
        doc_bin = DocBin(store_user_data=True)
        for doc, user_data in docs:
            doc.user_data = user_data
            line_sizes.append(user_data["length"])
            doc_bin.add(doc)
        doc_bin.to_disk(output_path)
    else:
        for doc, user_data in docs:
            doc.user_data = user_data
            line_sizes.append(user_data["length"])
    return line_sizes


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
    line_sizes = tokenize_corpus(
        input_path, language, output_path, batch_size, processes, segment_size)
    print(
        f"Processed {len(line_sizes)} documents.  Length median: {fmean(line_sizes)}, standard deviation: {pstdev(line_sizes)}")


if __name__ == "__main__":
    typer.run(main)
