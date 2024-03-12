import csv
from pathlib import Path
import time

from typing import Annotated, Optional
import tqdm
import typer

import spacy
from spacy import Language

from techqa_tools import tokenize, save_tokenized_corpus


def process(language, input_path, output_path, batch_size, processes, segment_size):
    docs = tqdm.tqdm(tokenize(language, input_path,
                batch_size, processes, segment_size))
    if output_path is not None:
        save_tokenized_corpus(docs, output_path)
    else:
        total_length = 0
        for doc in docs:
            total_length += len(doc)
        print(f"Total length of corpus: {total_length}")


def run_benchmarks(language, input_path, benchmark_path):
    settings = [
        {"batch_size": 1024, "processes": 1,
            "segment_size": None, "label": "whole doc"},
        {"batch_size": 1024, "processes": 1, "segment_size": 64, "label": "default"},
        {"batch_size": 1024, "processes": 2, "segment_size": 64, "label": "default"},
        {"batch_size": 1024, "processes": 4, "segment_size": 64, "label": "default"},
        {"batch_size": 1024, "processes": 1,
            "segment_size": 64, "label": "segmented"},
        {"batch_size": 1024, "processes": 1,
            "segment_size": 128, "label": "segmented"},
        {"batch_size": 1024, "processes": 1,
            "segment_size": 256, "label": "segmented"},
        {"batch_size": 1024, "processes": 1,
            "segment_size": 512, "label": "segmented"},
    ]
    print(f"Running benchmarks")
    with open(benchmark_path, 'w', newline='') as csvfile:
        fieldnames = ['label', 'time', 'processes',
                      'segment_size', 'batch_size']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for setting in tqdm.tqdm(settings):
            t0 = time.time()
            process(language, input_path, None,
                    setting["batch_size"], setting["processes"], setting["segment_size"])
            t1 = time.time()
            total = t1 - t0
            writer.writerow(
                {'label': setting["label"], 'time': total, 'processes': setting["processes"], 'segment_size': setting["segment_size"], 'batch_size': setting["batch_size"]})


def main(
    input_path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="Path to the .jsonl corpus file")],
    output_path: Annotated[Optional[Path],
                           typer.Argument(dir_okay=False, help="Path to the output DocBin")] = None,
    batch_size: Annotated[int, typer.Option(
        help="Batch size for processing")] = 1024,
    processes: Annotated[int, typer.Option(
        help="Number of processes to use for tokenization")] = 1,
    segment_size: Annotated[int, typer.Option(
        help="Number of words per input segment")] = None,
    benchmark: Annotated[bool, typer.Option(
        help="Run a benchmark for different settings")] = False,
    benchmark_path: Annotated[Optional[Path], typer.Option(
        help="Path to the benchmark output file")] = "benchmarks/tokenize.csv",
    use_gpu: Annotated[bool, typer.Option(
        help="Use GPU for processing")] = False,

):
    if use_gpu:
        spacy.prefer_gpu()
    language = spacy.load("en_core_web_sm")
    if benchmark:
        run_benchmarks(language, input_path, benchmark_path)
    else:
        process(language, input_path, output_path,
                batch_size, processes, segment_size, language)


if __name__ == "__main__":
    typer.run(main)
