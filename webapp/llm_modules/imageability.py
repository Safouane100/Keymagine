import dspy
from dspy.teleprompt import LabeledFewShot
from dspy import Example
from typing import Literal

Imageability = Literal["yes", "no", "somewhat", "symbolized"]

class ImageabilityJudge(dspy.Signature):
    """Judge whether the given word can be represented as an image"""
    word = dspy.InputField()
    rationale = dspy.OutputField()
    visualizable: Imageability = dspy.OutputField(desc="Either yes, no, somewhat, or symbolized")

class ImgModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.imgg = dspy.Predict(ImageabilityJudge)

    def forward(self, word):
        return self.imgg(word=word, config={"stop": "\n"})



class CompiledImageability():

    def __init__(self):
        # imageability_trainset = [
        #     ("love", "symbolized", "Love is most commonly represented as a heart."),
        #     ("tree", "yes", "A tree is a visualizable noun"),
        #     ("idolatry", "somewhat", "This can be approximated as a man bowing before a statue"), 
        #     ("televangelist", "somewhat", "A televangelist can be represented as a man in a slick suit, standing on a stage with a cross behind him"),
        #     ("cat", "yes", "A cat is a visualizable noun"),
        #     ("archimandrite", "no", "Archimandrite is a noun, but is too unknown to be represented in an image"),
        #     ("contumacious", "no", "This is an adjective, but too unknown to be represented in an image"),
        #     ("arrival", "somewhat", "This can be approximated by a man standing in front of a door"),
        #     ("justice", "symbolized", "This can be symbolized as a scale, or as Lady Justice"),
        #     ("democracy", "symbolized", "This can be symbolized as a voting box with the American flag on it."),
        #     ("to be about to", "no", "This is too abstract to represent as an image."),
        #     ("horror", "symbolized", "Horror can be represented as a scared face or a monster"),
        #     ("criminal", "yes", "A criminal can be represented as a man in a striped jumpsuit"),
        #     ("peace", "symbolized", "Peace is most commonly represented as a dove or a handshake")
        #     ]
        imageability_trainset = [
            ("therefore", "no", "This is a function word, and cannot be represented as an image."),
            ("whether", "no", "This is a function word, and cannot be represented as an image."),
            ("logical", "no", "This is too abstract to be represented as an image."),
            ("fallacy", "no", "This is too abstract to be represented as an image."),
            ("acumen", "no", "This is too abstract to be represented as an image."),
            ("industry", "somewhat", "This can be represented as a factory."),
            ("lesson", "somewhat", "This can be represented as a teacher in front of a blackboard."),
            ("thief", "somewhat", "This can be represented as a man in a mask, holding a bag of money."),
            ("hero", "somewhat", "This can be represented as superman."),
            ("shout", "somewhat", "This can be represented as a person shouting with their mouth open."),
            ("love", "symbolized", "Love is most commonly symbolized as a heart."),
            ("alligator", "yes", "An alligator is a visualizable noun"),
            ("window", "yes", "A window is a visualizable noun"),
            ("telephone", "yes", "A telephone is a visualizable noun"),
            ("cat", "yes", "A cat is a visualizable noun"),
            ("cake", "yes", "A cake is a visualizable noun"),
            ("horror", "symbolized", "Horror can be symbolized as a scared face or a monster"),
            ("peace", "symbolized", "Peace is most commonly symbolized as a dove or a handshake"),
            ("justice", "symbolized", "This can be symbolized as a scale or as Lady Justice"),
            ("democracy", "symbolized", "This can be symbolized as a voting box with the American flag on it."),
        ]
        imageability_trainset = [Example(word=x[0], rationale=x[2], visualizable=x[1]).with_inputs("word") for x in imageability_trainset]
        lfs_optimizer = LabeledFewShot(k=8)
        self.img_compiled = lfs_optimizer.compile(student=ImgModule(), trainset=imageability_trainset)
        
    def __call__(self, word):
        return self.img_compiled(word=word)