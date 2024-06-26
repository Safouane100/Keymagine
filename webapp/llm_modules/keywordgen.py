from .imageability import CompiledImageability
from .candidates import CompiledCandidates, Candidate
from .config import LLM
from collections import Counter

class KeywordGenerator():

    def __init__(self):
        self.imageability = CompiledImageability()
        self.candidates = CompiledCandidates()

    def generate_keywords(self, language, foreign_word):
        similar_words = self.candidates.get_candidates(language, foreign_word)
        counted = self.word_counter(similar_words)
        # print("counted:", counted)
        vizzed = self.get_imageability(counted)
        # print("vizzed:", vizzed)
        ranked = self.rank_keywords(vizzed)
        # print("ranked:", ranked)
        return [r.word for r in ranked]
    
    def word_counter(self, candidates: list[str]) -> list[Candidate]:
        counter = Counter(map(str.lower, candidates))
        res = [Candidate(word=k, count=v, imageability=None, imageability_rationale=None) for k, v in counter.items()]
        res.sort(key=lambda x: x.count, reverse=True)
        return res
    
    def get_imageability(self, candidates: list[Candidate]) -> list[Candidate]:
        res = []
        for c in candidates:
            imageability = self.imageability(word=c.word)
            c.imageability = imageability.visualizable
            c.imageability_rationale = imageability.rationale
            res.append(c)
        return res
    
    def rank_keywords(self, candidates: list[Candidate]) -> list[Candidate]:
        img_scores = {"yes": 2, "somewhat": 1, "symbolized": 1, "no": 0}

        res = sorted(candidates, key=lambda x: (
            x.count * img_scores.get(x.imageability, 0),
            x.count, 
            x.imageability), reverse=True)
        return res