class CognateDetectionSignature(dspy.Signature):
    """Return whether the two words are cognates of each other or very similar."""

    word_1_language = dspy.InputField()
    word_1 = dspy.InputField()
    word_2_language = dspy.InputField()
    word_2 = dspy.InputField()
    yes_no = dspy.OutputField(desc="Either yes or no.")

class CognateDetectionModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.imgg = dspy.Predict(CognateDetectionSignature)

    def forward(self, word_1_language, word_1, word_2_language, word_2):
        return self.imgg(word_1_language=word_1_language, word_1=word_1, \
                         word_2_language=word_2_language, word_2=word_2, \
                         config={"stop": "\n"})

cognate_trainset = [
    ("Italian", "mostaza", "English", "mustard", "No"),
    ("Dutch", "boter", "English", "butter", "Yes"),
    ("English", "door", "Dutch", "deur", "Yes"),
    ("French", "Pomme des terre", "Dutch", "aardappel", "No")
    ]
cognate_trainset = [Example(word_1_language=x[0], word_1=x[1], word_2_language=x[2], word_2=x[3], yes_no=x[4])
                    .with_inputs("word_1_language", "word_1", "word_2_language", "word_2") 
                    for x in cognate_trainset]