#!/usr/bin/env python3
from collections import defaultdict
from math import sqrt
import logging
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import os
import yaml


class EntryStats(object):
    def __init__(self):
        self.count = 0
        self.mean = 0
        self.M2 = 0 # second order moments
        self.var = float('nan')
        self.data = []


    def addSample(self, sample):
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
            self.stddev = sqrt(self.var)


class TestEvaluation(object):
    def __init__(self, output_paths):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.output_paths = output_paths

        # To create the bars later
        self.colors = ['#69c6bf', '#97d7ce', '#b9ee98', '#d5f396', '#f0f79a']

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

        aaa = self.marginalizeDataset('test2.bag')
        bbb = self.marginalizeParamset('param_set_1')
        ccc = self.joinDatasets()
        ddd = self.getMetricsFromJoinedDataset(ccc)
        eee = self.getMetricsByParamset(ccc)
        self.plotIndividualMetrics(ddd)
        self.plotMetricsByParamset(eee)
        plt.show()
        import ipdb; ipdb.set_trace()
        pass


    def marginalizeDataset(self, dataset):
        if dataset not in self.datasets:
            raise ValueError("Could not marginalize {}: Dataset not found.".format(dataset))

        result = {}
        # result['_dataset'] = dataset
        for param_set in self.parameter_sets:
            if (dataset, param_set) in self.results.keys():
                result[param_set] = self.results[(dataset, param_set)]

        return result


    def marginalizeParamset(self, param_set):
        if param_set not in self.parameter_sets:
            raise ValueError("Could not marginalize {}: Parameter set not found.".format(param_set))

        result = {}
        for dataset in self.datasets:
            if (dataset, param_set) in self.results.keys():
                result[dataset] = self.results[(dataset, param_set)]

        return result


    def joinDatasets(self, datasets='all'):
        # Join all datasets by default
        if datasets=='all':
            datasets = self.datasets
        if set(datasets) > self.datasets:
            raise Exception("Error. The datasets to be joined are not a subset of the stored datasets.")

        result_dict = defaultdict(dict)
        for dataset in datasets:
            dataset_runs = self.marginalizeDataset(dataset)
            # dataset_runs is a dict of form {param_label: { a: 1,
            #                                                b: 2,
            #                                                c: 3 }
            for param_label, run_results in dataset_runs.items():
                for key, metric in run_results.items():
                    if (key not in result_dict[param_label].keys()):
                        result_dict[param_label][key] = EntryStats()
                    result_dict[param_label][key].addSample(metric)

        return result_dict # make this a proper class I think


    def getMetricsFromJoinedDataset(self, joined_datasets):
        metrics_dict = defaultdict(lambda: defaultdict(dict))
        for param_label, keys in joined_datasets.items():
            for key, value in keys.items():
                metrics_dict[key][param_label]["mean"] = value.mean
                metrics_dict[key][param_label]["stddev"] = value.stddev

        return metrics_dict


    def getMetricsByParamset(self, joined_datasets):
        metrics_dict = defaultdict(lambda: defaultdict(dict))
        for param_label, keys in joined_datasets.items():
            # import ipdb; ipdb.set_trace()

            for key, value in keys.items():
                metrics_dict[param_label][key]["mean"] = value.mean
                metrics_dict[param_label][key]["stddev"] = value.stddev

        return metrics_dict


    def plotMetricsByParamset(self, metrics):
        plt.figure()
        turn = 0
        patches = []

        for param_set, metrics in metrics.items():

            N = len(metrics)
            ind = 1.3*np.arange(N) + 0.3*turn

            means = []
            stddevs = []
            for key in sorted(metrics):
                means.append(metrics[key]["mean"])
                stddevs.append(metrics[key]["stddev"])

            plt.bar(ind, means, 0.3, color=self.colors[turn], yerr=stddevs)

            # plt.title('{}'.format(param_set), fontsize=14)
            plt.xlabel('Metric')
            plt.ylabel('Value')
            
            plt.xticks(ind, sorted(metrics))
            patches.append(mpatches.Patch(color=self.colors[turn], label=param_set))
            turn += 1

        plt.legend(handles=patches)
        plt.grid()
        
        plt.show()


    def plotIndividualMetrics(self, metrics):
        plt.figure()
        turn = 0
        patches = []

        for metric, occurrences in metrics.items():

            N = len(occurrences)
            ind = 1.3*np.arange(N) + 0.2*turn
            
            means = []
            stddevs = []
            for key in sorted(occurrences):
                means.append(occurrences[key]["mean"])
                stddevs.append(occurrences[key]["stddev"])

            plt.bar(ind, means, 0.2, color=self.colors[turn], yerr=stddevs)

            # plt.title('{}'.format(metric), fontsize=14)
            plt.xlabel('Parameter set')
            plt.ylabel('Value')
            
            plt.xticks(ind, sorted(occurrences))
            patches.append(mpatches.Patch(color=self.colors[turn], label=metric))
            turn += 1

        plt.legend(handles=patches)
        plt.grid()

        plt.show()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info('Evaluation started')
    
    output_paths=[]
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test1/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test2/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test3/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test4/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test5/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test6/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test7/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test8/output.yaml')
    output_paths.append('/home/rafa/maplab_ws/src/evaluation_tools/results/test9/output.yaml')

    ev = TestEvaluation(output_paths)
