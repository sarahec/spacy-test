import jsonlines
import typer
from tqdm import tqdm
from pathlib import Path
from spacy.tokens import DocBin
import spacy


def analyze_corpus(source_path: Path, output_path: Path):
    nlp = spacy.load("en_core_web_sm")
    source_bin = DocBin().from_disk(source_path)
    tokenized_docs = list(source_bin.get_docs(nlp.vocab))
    docs = nlp.pipe(tokenized_docs, batch_size=64, n_process=12)
    output_bin = DocBin(attrs=["ENT_IOB", "ENT_TYPE"], store_user_data=True)
    for doc in docs:
        output_bin.add(doc)
    output_bin.to_disk(output_path)


def main(
    input_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    output_path: Path = typer.Argument(..., dir_okay=False),
):
    analyze_corpus(input_path, output_path)


if __name__ == "__main__":
    typer.run(main)
