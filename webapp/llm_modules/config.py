import dspy, os
import phoenix as px
from openinference.instrumentation.dspy import DSPyInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


class LLM():

    def __init__(self, model_name="meta-llama/Meta-Llama-3-70B"):
        self.llm = dspy.OpenAI(
            api_base = os.getenv("TOGETHER_API_BASE"),
            api_key= os.getenv("TOGETHER_API_KEY"),
            model= os.getenv("LLM_MODEL_NAME", model_name))
        dspy.configure(lm=self.llm, trace=[])
        print("LLM is loaded")
        # self.monitoring()
        # print("Monitoring is loaded")

    def monitoring(self):
        endpoint = "http://127.0.0.1:6006/v1/traces"
        resource = Resource(attributes={})
        tracer_provider = trace_sdk.TracerProvider(resource=resource)
        span_otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
        tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter=span_otlp_exporter))

        trace_api.set_tracer_provider(tracer_provider=tracer_provider)
        DSPyInstrumentor().instrument()

        phoenix_session = px.launch_app()

    def get_llm(self):
        return self.llm