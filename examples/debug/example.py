"""
Winton Kafka Streams

Main entrypoints

"""

import sys
import logging

from confluent_kafka import Consumer, KafkaError

from winton_kafka_streams.processor import BaseProcessor, ProcessorContext, TopologyBuilder
from winton_kafka_streams.state.simple import SimpleStore
import winton_kafka_streams.kafka_config as kafka_config
import winton_kafka_streams.kafka_stream as kafka_stream

log = logging.getLogger(__name__)

class DoubleProcessor(BaseProcessor):
    def __init__(self, _name, _context):
        super().__init__()

    def initialise(self, _name, _context):
        super().initialise(_name, _context)
        self.store = self.context.get_store("simple-store")

        self.context.schedule(1000)

    def process(self, key, value):
        self.store.add(key, value)

        print("DoubleProcessor::process("+str(key)+", "+str(value)+")")

        # TODO: In absence of a punctuate call schedule running:
        if len(self.store) == 4:
            self.punctuate()

        self.context.commit()

    def punctuate(self):
        log.debug('DoubleProcessor::punctuate')
        for k, v in iter(self.store):
            log.debug('Forwarding to sink  (%s, %s)', k, v)
            self.context.forward(k, v)
        self.store.clear()


def _debug_run(config_file):
    kafka_config.read_local_config(config_file)

    double_store = SimpleStore('simple-store')
    context = ProcessorContext()

    topology = TopologyBuilder()
    src = topology.source('prices', ['price'])
    proc_double = topology.processor('double', DoubleProcessor('double', context), 'prices', stores=[double_store])
    result = topology.sink('result', 'priceX2', 'double')

    ks = kafka_stream.KafkaStream(topology, kafka_config)
    ks.start()



if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    import argparse

    parser = argparse.ArgumentParser(description="Debug runner for Python Kafka Streams")
    parser.add_argument('--config-file', '-c', help="Local configuration - will override internal defaults")
    args = parser.parse_args()

    _debug_run(args.config_file)
