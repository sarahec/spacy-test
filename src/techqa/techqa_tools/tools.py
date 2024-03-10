# cython: language_level=3

from collections.abc import Callable, Generator
from pathlib import Path
from typing import Dict, Iterable, Optional
import jsonlines
import spacy
from spacy.tokens import DocBin, Doc
from spacy import Language


def load_tokenized_corpus(docbin_path: Path, language: Language) -> Iterable[Doc]:
    doc_bin = DocBin().from_disk(docbin_path)
    yield from doc_bin.get_docs(language.vocab)


def read_corpus_entries(input_path: Path) -> Iterable[tuple[str, Dict]]:
    with jsonlines.open(input_path) as reader:
        for entry in reader:
            text = entry["text"]
            yield (entry["text"], {"id": entry["id"], "title": entry["title"], "metadata": entry["metadata"], "length": len(entry["text"]), "start": 0})


def read_corpus_segments(input_path: Path, segment_size: int = 64) -> Iterable[tuple[str, Dict]]:
    with jsonlines.open(input_path) as reader:
        for entry in reader:
            text = entry["text"]
            spaces_idx = [i for i, c in enumerate(text) if c.isspace()]
            for i in range(0, len(spaces_idx), segment_size):
                first = spaces_idx[i]
                last = spaces_idx[i+segment_size] if i + \
                    segment_size < len(spaces_idx) else len(text)
                segment = text[first:last]
                yield (segment, {"id": entry["id"], "title": entry["title"], "metadata": entry["metadata"], "length": len(segment), "start": i})


def tokenize_corpus(inputs: Callable[[Path, Optional[int]], Generator[tuple[str, Dict], None, None]], language: Language, batch=1024, processes=1, segment_size=None) -> Generator[Doc, None, None]:
    nlp = spacy.blank("en", vocab=language.vocab)
    for doc, user_data in nlp.pipe(inputs, batch_size=batch, n_process=processes, as_tuples=True):
        doc.user_data = user_data
        yield doc


def save_tokenized_corpus(docs: Iterable[Doc], output_path: Path) -> None:
    doc_bin = DocBin(store_user_data=True)
    for doc in docs:
        doc_bin.add(doc)
    doc_bin.to_disk(output_path)


def label_corpus(inputs: Callable[[Path, Optional[int]], Generator[tuple[str, Dict], None, None]], language: Language, batch=1024, processes=1, segment_size=None) -> Generator[Doc, None, None]:
    for doc, user_data in language.pipe(inputs, batch_size=batch, n_process=processes, as_tuples=True):
        doc.user_data = user_data
        yield doc
