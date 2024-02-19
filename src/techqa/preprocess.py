import jsonlines
import typer
from tqdm import tqdm
from pathlib import Path
from spacy.tokens import DocBin
import spacy


def tokenize_corpus(input_path: Path, output_path: Path):
    spacy.prefer_gpu()
    ref_nlp = spacy.load("en_core_web_sm")
    nlp = spacy.blank("en", vocab=ref_nlp.vocab)
    doc_bin = DocBin(store_user_data=True)
    with jsonlines.open(input_path) as reader:
        json_docs = list(reader)
    docs = nlp.pipe([(eg["text"], {"id": eg["id"], "title": eg["title"], "metadata": eg["metadata"]}) for eg in json_docs],
                    batch_size=1024, n_process=2, as_tuples=True)
    for doc, user_data in docs:
        doc.user_data = user_data
        doc_bin.add(doc)

    doc_bin.to_disk(output_path)


def main(
    input_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    output_path: Path = typer.Argument(..., dir_okay=False),
):
    tokenize_corpus(input_path, output_path)


if __name__ == "__main__":
    typer.run(main)
