from typing import Optional, Union
from pydantic import BaseModel
from bunnet import Document, Indexed

class WordPair(BaseModel):
    native_word: str
    foreign_word: str

    def __repr__(self):
        return f"WordPair(native_word = {self.native_word}, foreign_word = {self.foreign_word})"

class WordList(Document):
    list_name: Indexed(str, unique=True)
    foreign_lang: str
    native_lang: str
    words: dict[int, WordPair] = {}

    def get(self, id):
        return self.words.get(id)

class Keyword(BaseModel):
    wordpair: WordPair
    keyword: str
    generated_by: str # user, transphoner, expert, myLLM
    meaning: Optional[str] = None
    verbal_cue: Optional[str] = None
    visual_cue: Optional[str] = None
    
    def __repr__(self):
        return f"Keyword(wordpair = {self.wordpair}, keyword = {self.keyword}, generated_by = {self.generated_by}, verbal_cue = {self.verbal_cue}, visual_cue = {self.visual_cue})"

    def get_myLLM_rank(self) -> Optional[int]:
        if self.generated_by.startswith("myLLM"):
            # Filter out digits from generated_by
            return int("".join(filter(str.isdigit, self.generated_by)))
        return None


class User(Document):
    user_id: Indexed(str, unique=True) 
    consented: bool = False
    keywords: list[Keyword] = []
    test_answers: dict[str, str] = {}
    final_answers: dict[str, str] = {}
    review_answers: dict[str, str] = {}
    grading: dict[str, str] = {}

    def get_user(user_id):
        u = User.find_one(User.user_id == user_id).run()
        if not u:
            u = User(user_id=user_id).insert()
            u.save()
        return u
        # return u
        # return User.find_one(User.user_id == user_id).run() or User(user_id=user_id).insert()

    def get_keyword(self, arg) -> Optional[Keyword]:
        if isinstance(arg, WordPair):
            return next((k for k in self.keywords if k.wordpair.foreign_word == arg.foreign_word), None)
        if isinstance(arg, Keyword):
            return next((k for k in self.keywords if k.wordpair.foreign_word == arg.wordpair.foreign_word), None)
        if isinstance(arg, int):
            from webapp.app import wordlist
            wp = wordlist.get(arg)
            return self.get_keyword(wp)

    def add_keyword(self, kw: Keyword) -> None:
        if not any(k.wordpair.foreign_word == kw.wordpair.foreign_word for k in self.keywords):
            print("Adding keyword", kw)
            self.keywords.append(kw)
            self.save()

    def get_verbal_cue(self, wp: WordPair) -> str:
        kw = self.get_keyword(wp)
        if kw:
            return kw.verbal_cue
        raise Exception("Keyword not found")

    def get_visual_cue(self, wp: WordPair) -> str:
        kw = self.get_keyword(wp)
        if kw:
            return kw.visual_cue
        raise Exception("Keyword not found")

    def add_verbal_cue(self, wp_or_kw: Union[WordPair, Keyword], verbal_cue: str) -> None:
        kw = self.get_keyword(wp_or_kw)
        if kw:
            kw.verbal_cue = verbal_cue
            self.save()
        else:
            raise Exception("Keyword not found")

    def add_visual_cue(self, wp_or_kw, visual_cue: str) -> None:
        kw = self.get_keyword(wp_or_kw)
        if kw:
            kw.visual_cue = visual_cue
            self.save()
        else:
            raise Exception("Keyword not found")

    def set_test_answers(self, answers: dict[str, str]) -> None:
        self.test_answers.update(answers)
        self.save()
    
    def set_final_answers(self, answers: dict[str, str]) -> None:
        self.final_answers.update(answers)
        self.save()
    
    def set_review_answers(self, answers: dict[str, str]) -> None:
        self.review_answers.update(answers)
        self.save()

    def set_grade(self, nr: str, grade: str) -> None:
        if grade not in ("correct", "incorrect", "partial", "keyword"):
            raise ValueError("Invalid grade")
        if int(nr) not in range(1, 37):
            raise ValueError("Invalid question number")
        self.grading[nr] = grade
        self.save()

    def get_grade(self, nr: str) -> str:
        return self.grading.get(nr, "")

    def get_helpfulness(self, nr: int) -> str:
        nr = str(nr)
        return self.review_answers.get(f"helpfulness{nr}", "")

    def is_correct(self, nr) -> bool:
        if isinstance(nr, int):
            nr = str(nr)
        return self.get_grade(nr) in ("correct", "partial")

    def is_transphoner_value(self, n: int) -> bool:
        """
        1-indexed!
        """
        return (n % 2 == 1 and self.user_id.startswith("T")) \
            or (n % 2 == 0 and self.user_id.startswith("L"))

    def get_split_results(self) -> dict[str, list[str]]:
        # filter_digits = lambda s : int("".join(filter(str.isdigit, s)))
        generated_by = set(kw.generated_by for kw in self.keywords) | {"myLLM", "personalized"}
        def is_gen_by(kw, g):
            if isinstance(kw, int): kw = self.get_keyword(kw)
            if not kw: return False
            gb = kw.generated_by
            if g == "personalized": return gb == "user" or gb.startswith("myLLM")
            return kw.generated_by.startswith(g)

        return dict(

            # "transphoner_grades": [self.get_grade(str(i)) for i in range(1, 37) if self.is_transphoner_value(i)],
            transphoner_grades = [self.get_grade(str(i)) for i in range(1, 37) if is_gen_by(i, "transphoner")],
            # personalized_grades = [self.get_grade(str(i)) for i in range(1, 37) if not self.is_transphoner_value(i)],
            personalized_grades = [self.get_grade(str(i)) for i in range(1, 37) if is_gen_by(i, "personalized")],
            myllm_grades = [self.get_grade(str(i)) for i in range(1, 37) if is_gen_by(i, "myLLM")],
            # user_grades = [self.get_grade(str(i)) for i in range(1, 37) if self.get_keyword(i) and self.get_keyword(i).generated_by == "user"],
            user_grades = [self.get_grade(str(i)) for i in range(1, 37) if is_gen_by(i, "user")],
            other_grades = [self.get_grade(str(i)) for i in range(1, 37) if not is_gen_by(i, "transphoner") and not is_gen_by(i, "personalized")],
            transphoner_helpfulness = [self.review_answers.get("helpfulness" + str(i)) for i in range(1, 37) if self.is_transphoner_value(i)],
            personalized_helpfulness = [self.review_answers.get("helpfulness" + str(i)) for i in range(1, 37) if not self.is_transphoner_value(i)]
        )

            

    def __repr__(self):
        return f"User(user_id = {self.user_id}, consented = {self.consented})"

