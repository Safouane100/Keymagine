from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from dspy.teleprompt import LabeledFewShot, SignatureOptimizer
from typing import Optional
from .imageability import Imageability
from dataclasses import dataclass
from itertools import chain
from dspy import Example
import dspy


@dataclass
class Candidate:
    word: str
    count: Optional[int]
    imageability: Imageability
    imageability_rationale: str

class SimilarOrthography(dspy.Signature):
    """Generate an English word that looks similar to the foreign word."""

    language = dspy.InputField()
    foreign_word = dspy.InputField()
    similar_word = dspy.OutputField(desc="An English word with similar spelling to foreign_word. Don't just translate it.")

class SimilarWordModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_word = dspy.Predict(SimilarOrthography)

    def forward(self, language, foreign_word) -> list[str]:
        sim_words = self.generate_word(language=language, foreign_word=foreign_word, config=dict(n=10, stop="\n")).completions.similar_word
        return sim_words

def is_similar_metric(example, pred, trace=None):
    user_input = "" 
    while not user_input.lower() in ("yes", "y", "no", "n", "stop"):
        user_input = input(f"Similar? example: {example}. Similar word: {pred.similar_word}")
    exit(1) if user_input.lower() == "stop" else user_input.lower() in ("yes", "y")

class SimilarWord:
    def __init__(self, language, foreign_word, similar_words, translations):
        self.language = language
        self.foreign_word = foreign_word
        if isinstance(similar_words, list):
            self.similar_words = similar_words
        elif isinstance(similar_words, str):
            self.similar_words = [similar_words]
        if isinstance(translations, list):
            self.translations = translations
        elif isinstance(translations, str):
            self.translations = [translations]

    def is_translation(self, some_word):
        return some_word.lower() in self.translations

    def generate_examples(self):
        if type(self.similar_words) == str:
            return Example(language=self.language, 
                           foreign_word=self.foreign_word, 
                           similar_word=self.similar_words,
                           translations=self.translations[0])\
                            .with_inputs("language", "foreign_word")
        elif type(self.similar_words) == list:
            return [Example(language=self.language, 
                            foreign_word=self.foreign_word, 
                            translations=self.translations[0],
                            similar_word=sim_w)\
                                .with_inputs("language", "foreign_word") 
                                for sim_w in self.similar_words]

# similarword_set = [
#     SimilarWord("french", "raconter", ["raccoon", "recount"], "to tell"), 
#     SimilarWord("spanish", "caballo", ["ball", "cabal"], "horse"), 
#     SimilarWord("japanese", "arashi", "airship", "storm"), 
#     SimilarWord("german", "ecke", "echo", "corner"),
#     SimilarWord("german", "rufen", "roofing", "to call"), 
#     SimilarWord("german", "brücke", "brook", "pants"),
#     SimilarWord("spanish", "bigote", "bigot", ["moustache", "mustache"]),
#     SimilarWord("swahili", "nyanya", ["ninja", "nyan cat"], "tomato"),
#     # From now on, linkword -- https://annas-archive.org/md5/23c88d9d1ded3a3a0794da1bc65d29c0
#     SimilarWord("french", "chèvre", ["chevrolet", "chevy"], "goat"), 
#     SimilarWord("french", "cheval", "shovel", "horse"), 
#     SimilarWord("french", "chien", "shine", "dog"),
#     SimilarWord("french", "poisson", "poison", "fish"),
#     ]



class CompiledCandidates():

    def __init__(self):
        similarword_set = [
            SimilarWord("french", "raconter", ["raccoon", "recount"], "to tell"), 
            SimilarWord("spanish", "caballo", ["ball", "cabal"], "horse"), 
            SimilarWord("japanese", "arashi", "airship", "storm"), 
            SimilarWord("german", "ecke", "echo", "corner"),
            SimilarWord("german", "rufen", "roofing", "to call"), 
            SimilarWord("german", "brücke", "brook", "bridge"),
            SimilarWord("spanish", "bigote", "bigot", ["moustache", "mustache"]),
            SimilarWord("swahili", "nyanya", ["ninja", "nyan cat"], "tomato"),
            # From now on, linkword -- https://annas-archive.org/md5/23c88d9d1ded3a3a0794da1bc65d29c0
            SimilarWord("french", "chèvre", ["chevrolet", "chevy"], "goat"), 
            SimilarWord("french", "cheval", "shovel", "horse"), 
            SimilarWord("french", "chien", "shine", "dog"),
            SimilarWord("french", "poisson", "poison", "fish"),
            SimilarWord("french", "nappe", "nap", "tablecloth"),
            SimilarWord("french", "couteau", "cut you", "knife"),
            SimilarWord("french", "fourchette", "force it", "fork"),
            SimilarWord("french", "assiette", "I see it", "plate"),
            SimilarWord("french", "beurre", ["bury", "purr"], "butter"),
            SimilarWord("french", "pain", "pain", "bread"),
            SimilarWord("french", "valise", "valleys", "suitcase"),
            SimilarWord("french", "douane", ["duane", "do one"], "customs"), 
            SimilarWord("french", "sortie", "sort", "exit"),
            SimilarWord("french", "piéton", ["peyton", "payton", "peloton"], "pedestrian"),
            SimilarWord("german", "müde", "moody", "tired"),
            SimilarWord("german", "später", "spider", "later"),
            SimilarWord("german", "spät", ["spat", "spade"], "late"),
            SimilarWord("german", "gardine", "garden", "curtain"),
        ]
        lfs_optimizer = LabeledFewShot(k=60)
        similarword_trainset = [x.generate_examples() for x in similarword_set]
        similarword_trainset = list(chain.from_iterable(similarword_trainset)) # Flatten list
        # smw_module_assertions = assert_transform_module(SimilarWordModule(), backtrack_handler)
        print(similarword_trainset)
        self.similarword_lfs = lfs_optimizer.compile(SimilarWordModule(), trainset=similarword_trainset)
    
    def get_candidates(self, language, foreign_word):
        return self.similarword_lfs(language=language, foreign_word=foreign_word)