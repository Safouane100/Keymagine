import dspy, os

mistral = dspy.Together(model="mistralai/Mistral-7B-Instruct-v0.2")
together_openai = dspy.OpenAI(
    api_base = os.getenv("TOGETHER_API_BASE"),
    api_key= os.getenv("TOGETHER_API_KEY"),
    model="mistralai/Mistral-7B-Instruct-v0.2", 
)
dspy.configure(lm=together_openai)


class SimilarOrthography(dspy.Signature):
    """Generate a list of English words that look similar to the foreign word"""

    foreign_word = dspy.InputField()
    english_words = dspy.OutputField(desc="Newline-separated list of similar looking words")

class IsSimilar(dspy.Signature):
    """Output whether two words look similar to each other"""

    word_1 = dspy.InputField(desc="first word")
    word_2 = dspy.InputField(desc="second word")
    ouput = dspy.OutputField(desc="do the first and second words resemble each other, yes or no")


class BasicGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.Predict(SimilarOrthography)

    def forward(self, word):
        return self.generate_answer(foreign_word=word)
    




