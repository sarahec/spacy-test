import spacy
from src.techqa.read_corpus import read_techqa_corpus


nlp = spacy.load('en_core_web_sm')
assert (nlp is not None)


def run_pipeline(corpus, batchSize=1024, nProcesses=4):
  return nlp.pipe([d["text"] for d in corpus], batch_size=batchSize, n_process=nProcesses)

# Insert a main function to run the pipeline


def main():
    inpf = "data/corpus.jsonl"
    count = 0
    corpus = read_techqa_corpus(inpf)
    result = run_pipeline(corpus)
    for doc in result:
      if len(doc) > 0:
        count = count + 1
    print(count)


if __name__ == "__main__":
    main()
