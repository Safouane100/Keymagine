import dspy, os, time
from dspy import Example
from dspy.teleprompt import BootstrapFewShot

together = dspy.OpenAI(
    api_base = os.getenv("TOGETHER_API_BASE"),
    api_key= os.getenv("TOGETHER_API_KEY"),
    model="mistralai/Mistral-7B-Instruct-v0.2", 
)
dspy.configure(lm=together)

class SampleSignature(dspy.Signature):
    """Repeat the same exact word"""
    word = dspy.InputField()
    repeated_word = dspy.OutputField()

class SampleModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.to_return = dspy.Predict(SampleSignature)

    def forward(self, word):
        return self.to_return(word=word)

def sample_metric(word, repeated_word, trace=None):
    return word == repeated_word 

testdata = ["apple", "banana", "cherry", "dog", "elephant", "frog", "grape", "horse", "iguana"]
trainset = [Example(word=x, repeated_word=x).with_inputs("word") for x in testdata]
optimizer = BootstrapFewShot(metric=sample_metric)
compiled_module_mistral7b = optimizer.compile(SampleModule(), trainset=trainset)


while True: # Sleep to be able to inspect the phoenix page
    time.sleep(999)