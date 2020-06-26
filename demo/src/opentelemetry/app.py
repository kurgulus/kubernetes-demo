from azure_monitor import AzureMonitorSpanExporter
from azure_monitor import AzureMonitorMetricsExporter
from opentelemetry import trace
from opentelemetry import metrics
from opentelemetry.sdk.metrics import Counter, MeterProvider
from opentelemetry.sdk.metrics.export.controller import PushController
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchExportSpanProcessor
from opentelemetry.ext.flask import FlaskInstrumentor
from opentelemetry.ext.requests import RequestsInstrumentor
import time
import random
import socket
import os
import flask
import requests
# from azure_monitor.sdk.auto_collection import (
#     AutoCollection,
#     AzureMetricsSpanProcessor,
# )

# Setup distributed tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

trace_exporter = AzureMonitorSpanExporter(
    instrumentation_key = os.environ['APPINSIGHTS_INSTRUMENTATION_KEY']
)

span_processor = BatchExportSpanProcessor(trace_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

RequestsInstrumentor().instrument()

app = flask.Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Setup metrics
metrics_exporter = AzureMonitorMetricsExporter(
    instrumentation_key = os.environ['APPINSIGHTS_INSTRUMENTATION_KEY']
)
metrics.set_meter_provider(MeterProvider())
meter = metrics.get_meter(__name__)
PushController(meter, metrics_exporter, 10)

tomas_counter = meter.create_metric(
    name="mydemo_counter",
    description="mydemo namespace",
    unit="1",
    value_type=int,
    metric_type=Counter,
)

# Define cloud role
def callback_function(envelope):
    envelope.tags['ai.cloud.role'] = os.getenv('APP_NAME')
    return True

trace_exporter.add_telemetry_processor(callback_function)
metrics_exporter.add_telemetry_processor(callback_function)

# Flask routing
@app.route('/')
def init():
    time.sleep(random.random())
    response = requests.get(os.getenv('REMOTE_ENDPOINT'))
    return 'OK'

@app.route('/data')
def data():
    time.sleep(random.random())
    with tracer.start_as_current_span(name='ProcessDataFunction'):
        time.sleep(random.random())
    return 'OK'

@app.route('/counter')
def test():
    tomas_counter.add(1, {"environment": "testing"})
    return 'OK'

# Run Flask app
app.run(host='0.0.0.0', port=8080, threaded=True)
