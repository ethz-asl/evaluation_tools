#!/usr/bin/env python3
import logging
import yaml
import os
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt

class EntryStats(object):
    def __init__(self):
        self.count = 0
        self.mean = 0
        self.M2 = 0 # second order moments
        self.var = float('nan')
        self.data = []


    def add_sample(self, sample):
        self.data.append(sample)
        """
        Using Welford algorithm
        TODO makes no sense to use if we are appending data
        """
        self.count += 1
        delta = sample - self.mean
        self.mean += delta/self.count
        delta2 = sample - self.mean
        self.M2 += delta*delta2

        if self.count > 1:
            self.var = self.M2 / (self.count-1)


class TestEvaluation(object):
    def __init__(self, output_paths):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.output_paths = output_paths

        # Load data
        self.datasets = set()
        self.parameter_sets = defaultdict()
        self.results = defaultdict((dict))

        for output_file in output_paths:
            if not os.path.isfile(output_file):
                raise ValueError("Output file does not exist: {}".format(output_file))
            output = yaml.safe_load(open(output_file))
            if {'dataset', 'param_label', 'parameters', 'results'} > output.keys():
                raise ValueError('Malformed output file: {}'.format(output_file))
            
            dataset = output["dataset"]
            param_label = output["param_label"]
            parameters = output["parameters"]
            results = output["results"]

            self.datasets.add(dataset)
            self.parameter_sets[param_label] = parameters

            self.results[(dataset, param_label)] = results

        self.logger.info("Extracted data from {} runs, across {} datasets and {} parameter sets."
                         "".format(len(output_paths), len(self.datasets), len(self.parameter_sets)))

        aaa = self.marginalize_dataset('test2.bag')
        bbb = self.marginalize_paramset('param_set_1')
        ccc = self.join_datasets()
        ddd = self.get_metrics_from_joined_dataset(ccc)
        self.plot_metrics(ddd)
        import ipdb; ipdb.set_trace()
        pass


    def marginalize_dataset(self, dataset):
        if dataset not in self.datasets:
            raise ValueError("Could not marginalize {}: Dataset not found.".format(dataset))

        result = {}
        # result['_dataset'] = dataset
        for param_set in self.parameter_sets:
            if (dataset, param_set) in self.results.keys():
                result[param_set] = self.results[(dataset, param_set)]

        return result


    def marginalize_paramset(self, param_set):
        if param_set not in self.parameter_sets:
            raise ValueError("Could not marginalize {}: Parameter set not found.".format(param_set))

        result = {}
        for dataset in self.datasets:
            if (dataset, param_set) in self.results.keys():
                result[dataset] = self.results[(dataset, param_set)]

        return result


    def join_datasets(self, datasets='all'):
        # Join all datasets by default
        if datasets=='all':
            datasets = self.datasets
        if set(datasets) > self.datasets:
            raise Exception("Error. The datasets to be joined are not a subset of the stored datasets.")

        result_dict = defaultdict(dict)
        for dataset in datasets:
            dataset_runs = self.marginalize_dataset(dataset)
            # dataset_runs is a dict of form {param_label: { a: 1,
            #                                                b: 2,
            #                                                c: 3 }
            for param_label, run_results in dataset_runs.items():
                for key, metric in run_results.items():
                    if (key not in result_dict[param_label].keys()):
                        result_dict[param_label][key] = EntryStats()
                    result_dict[param_label][key].add_sample(metric)

        return result_dict # make this a proper class I think


    def get_metrics_from_joined_dataset(self, joined_datasets):
        metrics_dict = defaultdict(lambda: defaultdict(dict))
        for param_label, keys in joined_datasets.items():
            for key, value in keys.items():
                metrics_dict[key][param_label]["mean"] = value.mean
                metrics_dict[key][param_label]["var"] = value.var

        return metrics_dict

    def plot_metrics(self, metrics):
        for metric, occurrences in metrics.items():

            N = len(occurrences)
            ind = np.arange(N)
            
            means = []
            stddevs = []
            for key in sorted(occurrences):
                means.append(occurrences[key]["mean"])
                stddevs.append(occurrences[key]["var"])

            plt.figure()
            plt.bar(ind, means, 0.2, color='#d62728', yerr=stddevs)

            plt.title('Results for {}'.format(metric), fontsize=14)
            plt.xlabel('Parameter set')
            plt.ylabel('Value')
            
            plt.xticks(ind, sorted(occurrences))

        plt.show()



if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info('Evaluation started')
    
    output_paths=[]
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test1/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test2/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test3/output.yaml')

    ev = TestEvaluation(output_paths)

    