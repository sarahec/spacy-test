"""
 Copyright 2024 Sarah Clark

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 """

import pytest
from pipeline import read_techqa_corpus, run_pipeline, post_process_docs


@pytest.mark.skip(reason="covered by the pipeline test")
def test_read_techqa_corpus():
    inpf = "data/corpus.jsonl"
    for snippet in read_techqa_corpus(inpf):
        assert "id" in snippet
        assert "title" in snippet
        assert "text" in snippet
        assert "metadata" in snippet
        assert "chunk_ind" in snippet
        assert snippet["text"] != ""


def test_run_pipeline():
    inpf = "data/corpus.jsonl"
    corpus = read_techqa_corpus(inpf)
    result = run_pipeline(corpus)
    assert result is not None
    for doc in result:
        assert doc is not None
        assert post_process_docs(doc) is not None
