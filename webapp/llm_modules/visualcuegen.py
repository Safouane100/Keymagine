import dspy
from dspy import Example
from dspy.teleprompt import LabeledFewShot

class VisualCueSignature(dspy.Signature):
    """
    Generate a text-to-image prompt from the given sentence.
    Replace slang terms with more formal terms.
    If a word has synonyms, choose the most visually descriptive one.
    """
    sentence = dspy.InputField()
    text2img_prompt = dspy.OutputField(desc="A prompt for generating an image from a sentence")

class VisualCueModule(dspy.Module):
    def __init__(self):
        super().__init__()
        # self.generate_prompt = dspy.Predict("sentence -> text2img_prompt")
        self.generate_prompt = dspy.Predict(VisualCueSignature)

    def forward(self, verbal_cue: str) -> str:
        res = self.generate_prompt(sentence=verbal_cue, config={"stop": "\n"}).text2img_prompt
        print("Visual cue:", res)
        return res 

class VisualCueGenerator:

    def __init__(self):   
        trainset = [
            Example(sentence="Imagine a fortune-teller with a pile of silver plates", text2img_prompt="fortune-teller with pile of silver plates"),
            Example(sentence="Imagine your kitchen and a cook in it", text2img_prompt="cook in kitchen"),
            Example(sentence="Imagine you rent meat to friends in your room", text2img_prompt="renting meat to friends in room"),
            Example(sentence="Imagine sailors pay for hot rum", text2img_prompt="sailors paying for rum"),
            Example(sentence="Imagine nail-clippers on a cliff", text2img_prompt="nail-clippers on a cliff"),
            Example(sentence="Imagine a flag on a fan", text2img_prompt="flag on a fan"),
            Example(sentence="Imagine you call a friend to put a new roof on a cottage", text2img_prompt="calling friend on top of a cottage roof"),
            Example(sentence="Imagine crabs dig holes in the sand", text2img_prompt="crab digging hole in sand"),
            Example(sentence="Imagine shears besides a pair of scissors", text2img_prompt="shears besides scissors"),
            Example(sentence="Imagine your lawn covered in raisins", text2img_prompt="lawn covered in raisins"),
            Example(sentence="Imagine you push stores in a cupboard", text2img_prompt="push stores in a cupboard"),
            Example(sentence="Imagine strikers paint slogans on walls", text2img_prompt="strikers painting slogans on wall")]

        self.lfs = LabeledFewShot(k=20).compile(VisualCueModule(), trainset=trainset)

    def __call__(self, verbal_cue: str) -> str:
        res = self.lfs(verbal_cue=verbal_cue)
        print("Visual cue prompt:", res)
        return res