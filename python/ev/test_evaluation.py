#!/usr/bin/env python3
import logging
import yaml
import os
from collections import defaultdict

class TestEvaluation(object):
    def __init__(self, output_paths):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.output_paths = output_paths

        # Load data
        self.datasets = set() # debug
        self.parameter_sets = set()
        self.results = defaultdict(lambda: defaultdict(dict));

        for output_file in output_paths:
            if not os.path.isfile(output_file):
                raise ValueError("Output file does not exist: " + output_file)
            output = yaml.safe_load(open(output_file))
            if not {'dataset', 'param_label', 'parameters', 'results'} <= output.keys():
                raise ValueError('Malformed output file: ' + output_file)
            
            dataset = output["dataset"]
            param_label = output["param_label"]
            parameters = output["parameters"]
            results = output["results"]

            self.datasets.add(dataset)
            self.parameter_sets.add(param_label)

            self.results[dataset][param_label]["parameters"] = parameters
            self.results[dataset][param_label]["results"] = results

        self.logger.info("Extracted data from {} runs, across {} datasets and {} parameter sets."
                         "".format(len(output_paths), len(self.datasets), len(self.parameter_sets)))

        
        import ipdb; ipdb.set_trace()
        pass

    def join_datasets(self, datasets):
        pass


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info('Evaluation started')
    
    output_paths=[]
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test1/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test2/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test3/output.yaml')

    ev = TestEvaluation(output_paths)

    

