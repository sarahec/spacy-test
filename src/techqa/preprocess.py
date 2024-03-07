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


def tokenize_corpus(input_path: Path, language: Language, output_path: Optional[Path], batch=1024, processes=2):
    nlp = spacy.blank("en", vocab=language.vocab)
    doc_bin = DocBin(store_user_data=True)
    with jsonlines.open(input_path) as reader:
        # json_docs = list(reader)
        docs = nlp.pipe([(eg["text"], {"id": eg["id"], "title": eg["title"], "metadata": eg["metadata"], "length": len(eg["text"])}) for eg in reader],
                        batch_size=batch, n_process=processes, as_tuples=True)
    if output_path is not None:
        doc_bin = DocBin(store_user_data=True)
        for doc, user_data in docs:
            doc.user_data = user_data
            doc_bin.add(doc)
        doc_bin.to_disk(output_path)
    else:
        lines = 0
        total_length = 0
        for doc, user_data in docs:
            doc.user_data = user_data
            lines += 1
            total_length += user_data["length"]
        print(
            f"Processed {lines} documents with an average length of {total_length / lines} characters")





def main(
    input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="Path to the .jsonl corpus file")],
    output_path: Annotated[Optional[Path],
                           typer.Argument(dir_okay=False, help="Path to the output DocBin")] = None,
    batch: Annotated[int, typer.Option(
        help="Batch size for processing")] = 1024,
    processes: Annotated[int, typer.Option(
        help="Number of processes to use for tokenization")] = 2,
):
    language = spacy.load("en_core_web_sm")
    tokenize_corpus(input_path, language, output_path, batch, processes)


if __name__ == "__main__":
    typer.run(main)
