import dspy, os, time
from dspy import Example
from dspy.teleprompt import BootstrapFewShot

############################################################
######### INFERENCE MONITORING
import phoenix as px
from openinference.instrumentation.dspy import DSPyInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

endpoint = "http://127.0.0.1:6006/v1/traces"
resource = Resource(attributes={})
tracer_provider = trace_sdk.TracerProvider(resource=resource)
span_otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter=span_otlp_exporter))

trace_api.set_tracer_provider(tracer_provider=tracer_provider)
DSPyInstrumentor().instrument()

phoenix_session = px.launch_app()
#############################################################


together = dspy.OpenAI(
    api_base = os.getenv("TOGETHER_API_BASE"),
    api_key= os.getenv("TOGETHER_API_KEY"),
    model="mistralai/Mistral-7B-Instruct-v0.2", 
)
dspy.configure(lm=together)

class SampleSignature(dspy.Signature):
    """Repeat the same exact word."""
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