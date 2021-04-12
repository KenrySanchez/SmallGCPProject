import argparse
import json
import logging

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import storage
from smart_open import open

class ReadFile(beam.DoFn):

    def __init__(self, input_path):
        self.input_path = input_path

    def start_bundle(self):
        self.client = storage.Client()

    def process(self, something):
        clear_data = []
        with open(self.input_path) as fin:
            for line in fin:
                data = json.loads(line)
                
                for elems in data['annotation_results']:
                  for item in elems['object_annotations']:

                    clear_data.append({
                      'description': item['entity']['description'],
                      'time' : 0
                    })

        yield clear_data

class DataflowOptions(PipelineOptions):

    def run(self, argv=None):
        parser = argparse.ArgumentParser()
        known_args, pipeline_args = parser.parse_known_args(argv)

        pipeline_options = PipelineOptions(pipeline_args)
        dataflow_options = pipeline_options.view_as(DataflowOptions)

        with beam.Pipeline(options=pipeline_options) as pipeline:
            (pipeline
                | 'Start' >> beam.Create([None])
                | 'Read JSON' >> beam.ParDo(ReadFile(dataflow_options.input_path))
                | 'Write to BigQuery' >> beam.io.Write(beam.io.BigQuerySink(pipeline_options['output']))
            )


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()