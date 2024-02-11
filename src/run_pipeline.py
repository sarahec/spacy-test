import spacy


nlp = spacy.load('en_core_web_sm')
assert (nlp is not None)


def run_pipeline(corpus, batchSize=1024, nProcesses=12):
  return nlp.pipe([d["text"] for d in corpus], batch_size=batchSize, n_process=nProcesses)
