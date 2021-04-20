import argparse
import json
import logging

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.value_provider import StaticValueProvider
from google.cloud import storage
from smart_open import open


class ReadFile(beam.DoFn):

    def __init__(self, input_path):
        self.input_path = input_path

    def start_bundle(self):
        self.client = storage.Client()

    def calculate_time_values(self, segment):

        time = 0
        start_time = 0
        end_time = 0
  
        start_time_seconds = segment["start_time_offset"][
            "seconds"] if "seconds" in segment["start_time_offset"] else 0
            
        start_time_nanos = segment["start_time_offset"][
            "nanos"] if "nanos" in segment["start_time_offset"] else 0

        end_time_seconds = segment["end_time_offset"][
            "seconds"] if "seconds" in segment["end_time_offset"] else 0

        end_time_nanos = segment["end_time_offset"][
            "nanos"] if "nanos" in segment["end_time_offset"] else 0

        start_time += (start_time_seconds +
                        start_time_nanos/(1*10**9))
        end_time += (end_time_seconds +
                        end_time_nanos/(1*10**9))

        time +=  end_time - start_time
        
        return time, start_time, end_time
        

    def process(self, something):

        clear_data = []
        with open(self.input_path.get()) as line:

            jsonAsString = line.read()

            data = json.loads(jsonAsString)

            for elems in data["annotation_results"]:

                for item in elems["logo_recognition_annotations"]:

                    time = 0
                    confidence = 0
                    start_time = 0
                    end_time = 0

                    getter_time = 0
                    getter_start = 0
                    getter_end = 0

                    for track in item["tracks"]:
                        confidence += track["confidence"]

                        ## this is the block using logo_recognition_annotations.tracks
                        getter_time, getter_start, getter_end = self.calculate_time_values(track["segment"])

                        time += getter_time
                        start_time += getter_start
                        end_time = getter_end

                    ## this is the block using logo_recognition_annotations.segments
                    ##for segment in item["segments"]:

                        ##getter_time, getter_start, getter_end = self.calculate_time_values(segment)

                        ##time += getter_time
                        ##start_time += getter_start
                        ##end_time = getter_end
                    
                    yield {
                        "time": time,
                        "confidence": confidence,
                        "start_time": start_time,
                        "end_time": end_time,
                        "description": item["entity"]["description"],
                    }


class DataflowOptions(PipelineOptions):

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_value_provider_argument("--input", type=str)

    def run(self, argv=None):
        pipeline_options = PipelineOptions()
        user_options = pipeline_options.view_as(DataflowOptions)

        with beam.Pipeline(options=pipeline_options) as pipeline:
            (pipeline
                | "Start" >> beam.Create([None])
                | "Read JSON" >> beam.ParDo(ReadFile(user_options.input))
                | "Write to BigQuery" >> beam.io.Write(beam.io.WriteToBigQuery("logo-project-306822:logo_dataset.logo_table", schema="description:STRING,time:FLOAT,start_time:FLOAT,end_time:FLOAT,confidence:FLOAT", write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND))
             )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    r = DataflowOptions()
    r.run()
