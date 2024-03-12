import csv
from pathlib import Path
import time

from techqa_tools import label_text, save_tokenized_corpus
from typing import Annotated, Optional
import tqdm
import typer

import spacy


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


def process(language, input_path, output_path, batch_size, processes, segment_size):
    docs = tqdm.tqdm(label_text(language, input_path, batch_size,
                                processes, segment_size))
    if output_path is not None:
        save_tokenized_corpus(docs, output_path)
    else:
        total_length = 0
        for doc in docs:
            total_length += len(doc)
        print(f"Total length of corpus: {total_length}")


benchmark_groups = ["doc", "processors", "segment", "batch"]


def run_benchmarks(language: spacy.Language, input_path: Path, benchmark_path: Path, select="all", treatment: str = 'unknown', use_gpu: bool = False):
    benchmarks = {"doc": [
        {"batch_size": 1024, "processes": 1,
            "segment_size": None, "label": "doc"},
        {"batch_size": 1024, "processes": 2,
            "segment_size": None, "label": "doc"},
        {"batch_size": 1024, "processes": 3,
            "segment_size": None, "label": "doc"},
        {"batch_size": 1024, "processes": 4,
            "segment_size": None, "label": "doc"},
        {"batch_size": 1024, "processes": 5,
            "segment_size": None, "label": "doc"},
        {"batch_size": 1024, "processes": 6,
            "segment_size": None, "label": "doc"},
    ],
        "processors": [
            {"batch_size": 1024, "processes": 1,
             "segment_size": 64, "label": "processors"},
            {"batch_size": 1024, "processes": 2,
             "segment_size": 64, "label": "processors"},
            {"batch_size": 1024, "processes": 3,
             "segment_size": 64, "label": "processors"},
            {"batch_size": 1024, "processes": 4,
             "segment_size": 64, "label": "processors"},
            {"batch_size": 1024, "processes": 5,
             "segment_size": 64, "label": "processors"},
            {"batch_size": 1024, "processes": 6,
             "segment_size": 64, "label": "processors"},
    ],
        "segment": [
        {"batch_size": 1024, "processes": 4,
            "segment_size": 128, "label": "segment"},
        {"batch_size": 1024, "processes": 4,
            "segment_size": 256, "label": "segment"},
        {"batch_size": 1024, "processes": 4,
            "segment_size": 512, "label": "segment"},
    ],
        "batch": [
        {"batch_size": 64, "processes": 4,
            "segment_size": 512, "label": "batch"},
        {"batch_size": 32, "processes": 4,
            "segment_size": 512, "label": "batch"},
        {"batch_size": 16, "processes": 4,
            "segment_size": 512, "label": "batch"},
        {"batch_size": 12, "processes": 4,
            "segment_size": 512, "label": "batch"},
        {"batch_size": 8, "processes": 4,
            "segment_size": 512, "label": "batch"},
        {"batch_size": 4, "processes": 4,
            "segment_size": 512, "label": "batch"},
    ]}

    selected = benchmarks[select] if select in benchmark_groups else benchmarks["doc"] + \
        benchmarks["processors"] + benchmarks["segment"] + benchmarks["batch"]

    print(f"Running benchmarks")
    with open(benchmark_path, 'w', newline='') as csvfile:
        fieldnames = ["group", "time", "processes",
                      "segment_size", "batch_size", "gpu", "treatment"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for setting in tqdm.tqdm(selected):
            t0 = time.perf_counter()
            process(language, input_path, None,
                    setting["batch_size"], setting["processes"], setting["segment_size"])
            t1 = time.perf_counter()
            total = t1 - t0
            writer.writerow(
                {"group": setting["label"], "time": total, "processes": setting["processes"], "segment_size": setting["segment_size"], "batch_size": setting["batch_size"], "gpu": use_gpu, "treatment": treatment})


def main(
    input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="Path to the .jsonl corpus file")],
    output_path: Annotated[Optional[Path],
                           typer.Argument(dir_okay=False, help="Path to the output DocBin")] = None,
    batch_size: Annotated[int, typer.Option(
        help="Batch size for processing")] = 1024,
    processes: Annotated[int, typer.Option(
        help="Number of processes to use for NER recognition")] = 1,
    segment_size: Annotated[int, typer.Option(
        help="Number of words per input segment")] = None,
    benchmark: Annotated[str, typer.Option(
        help="Run a benchmark: all, doc, procesors, segment, or batch")] = None,
    treatment: Annotated[Optional[str], typer.Option(
        help="Name of the treatment applied")] = "unknown",
    use_gpu: Annotated[bool, typer.Option(
        help="Use GPU for processing")] = False,

):
    if use_gpu:
        spacy.prefer_gpu()
    language = spacy.load("en_core_web_sm")
    if benchmark:
        gpu_label = "-gpu" if use_gpu else ""
        benchmark_path = f"benchmarks/label_text-{benchmark}-{treatment}{gpu_label}.csv"
        run_benchmarks(language, input_path, benchmark_path,
                       benchmark, treatment, use_gpu)
    else:
        process(language, input_path, output_path,
                batch_size, processes, segment_size)


if __name__ == "__main__":
    typer.run(main)
