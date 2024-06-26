import dspy, random
from dspy.teleprompt import LabeledFewShot

class VerbalCueSignature(dspy.Signature):
    word1 = dspy.InputField()
    word2 = dspy.InputField()
    sentence = dspy.OutputField(desc="An imaginative sentence that combines word1 and word2")

class VerbalCueModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_sentence = dspy.Predict(VerbalCueSignature)

    def forward(self, word1, word2) -> list[str]:
        temperature = 0.5 + random.uniform(-0.1, 0.1)
        return self.generate_sentence(word1=word1, word2=word2, config={"stop": "\n", "temperature": temperature}).sentence # ey

class VerbalCueGenerator:
    def __init__(self):   
        trainset = [
            dspy.Example(word1="plate", word2="fortune-teller", sentence="Imagine a fortune-teller with a pile of silver plates"),
            dspy.Example(word1="kitchen", word2="cook", sentence="Imagine your kitchen and a cook in it"),
            dspy.Example(word1="to rent", word2="meat", sentence="Imagine you rent meat to friends in your room"),
            dspy.Example(word1="to pay", word2="sailor", sentence="Imagine sailors pay for hot rum"),
            dspy.Example(word1="cliff", word2="clip", sentence="Imagine nail-clippers on a cliff"),
            dspy.Example(word1="flag", word2="fan", sentence="Imagine a flag on a fan"),
            dspy.Example(word1="to call", word2="roof", sentence="Imagine you call a friend to put a new roof on a cottage"),
            dspy.Example(word1="to dig", word2="crab", sentence="Imagine crabs dig holes in the sand"),
            dspy.Example(word1="scissors", word2="shear", sentence="Imagine shears besides a pair of scissors"),
            dspy.Example(word1="lawn", word2="raisin", sentence="Imagine your lawn covered in raisins"),
            dspy.Example(word1="to push", word2="store", sentence="Imagine you push stores in a cupboard"),
            dspy.Example(word1="to paint", word2="striking", sentence="Imagine strikers paint slogans on walls")
            ]
        # trainset = [
        #     dspy.Example(word1="four", word2="fear", sentence="Imagine you fear the number four"),
        #     dspy.Example(word1="egg", word2="eye", sentence="Imagine an eye painted on the shell of an egg"),
        #     dspy.Example(word1="cheese", word2="case", sentence="Imagine a case filled with a whole lot of different cheeses."),
        #     dspy.Example(word1="bean", word2="bone", sentence="Imagine a bone covered in beans"),
        #     dspy.Example(word1="potato", word2="cart off", sentence="")
        # ]
        vcm = VerbalCueModule()
        lfs = LabeledFewShot(k=20)
        self.lfs = lfs.compile(vcm, trainset=trainset)

    def __call__(self, word1: str, word2: str) -> str:
        # return self.lfs(word1=word1, word2=word2)
        return self.lfs(word1=word1, word2=word2)