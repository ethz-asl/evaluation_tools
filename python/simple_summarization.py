#!/usr/bin/env python

from collections import defaultdict
from collections import OrderedDict
from math import sqrt
import argparse
import logging
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import os
import yaml

class Metric(object):
    def __init__(self):
        self.count = 0
        self.mean = 0
        self.stddev = 0
        self.var = 0
        self.min = float('nan')
        self.max = float('nan')

    def addSample(self, sample):
        m = Metric()
        m.count = sample["samples"]
        m.mean = sample["mean"]
        m.stddev = sample["stddev"]
        m.var = m.stddev * m.stddev
        m.min = sample["min"]
        m.max = sample["max"]

        self.joinMetric(m)

    def joinMetric(self, other):
        if self.count == 0:
            self.mean = other.mean
            self.var = other.var
            self.stddev = other.stddev
            self.min = other.min
            self.max = other.max
        # TODO check the formulas
        else:
            self.mean = (self.mean * self.count + other.mean * other.count) \
                        / (self.count + other.count)

            self.var = ((self.count - 1) * self.var + (other.count - 1) * other.var \
                       + (self.count * other.count) / (self.count + other.count) \
                       * (self.mean * self.mean + other.mean * other.mean - 2 * self.mean * other.mean)) \
                       / (self.count + other.count - 1)
            self.stddev = sqrt(self.var)

            self.min = min(self.min, other.min)
            self.max = max(self.max, other.max)

        self.count += other.count


class SimpleSummarization(object):

    def __init__(self, files_to_summarize, whitelist = [], blacklist = []):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.files_to_summarize = files_to_summarize
        self.whitelist = whitelist
        self.blacklist = blacklist

        # To create the bars later
        self.colors = ['#69c6bf', '#97d7ce', '#b9ee98', '#d5f396', '#f0f79a', '#ffd993', '#ffc966', \
            '#111111', '#222222', '#333333', '#444444', '#555555', '#666666', '#777777' \
          , '#888888', '#999999', '#aaaaaa', '#bbbbbb', '#cccccc', '#dddddd', '#eeeeee', '#ffffff']

        # Load data
        self.datasets = set()
        self.parameter_files = set()
        self.metrics = defaultdict((dict))

        self.metrics = defaultdict(lambda: defaultdict(Metric))
        for file in files_to_summarize:
            if not os.path.isfile(file):
                raise ValueError("Output file does not exist: {}".format(file))
            statistics = yaml.safe_load(open(file))
            if not {'dataset', 'metrics', 'parameter_file'}.issubset(statistics.keys()):
                raise ValueError('Malformed statistics file: {}'.format(file))
            
            dataset = statistics["dataset"]
            parameter_file = statistics["parameter_file"]
            metrics = statistics["metrics"]

            # Remove unwanted metrics
            if self.whitelist:
                metrics = {key: metrics[key] for key in metrics if key in self.whitelist}

            else:
                metrics = {key: metrics[key] for key in metrics if key not in self.blacklist}

            self.datasets.add(dataset)
            self.parameter_files.add(parameter_file)

            for metric, values in metrics.items():
                self.metrics[(dataset, parameter_file)][metric].addSample(values)

        self.logger.info("Extracted data from {} runs, across {} datasets and {} parameter sets."
                         "".format(len(self.files_to_summarize), len(self.datasets), len(self.parameter_files)))

        # aaa = self.marginalizeDataset('test2.bag')
        # bbb = self.marginalizeParameterFile('parameter_file_1')
        ccc = self.joinDatasets()
        ddd = self.getMetricsFromJoinedDataset(ccc)
        eee = self.getMetricsByParamset(ccc)
        self.plotIndividualMetrics(ddd)
        self.plotMetricsByParamset(eee)
        plt.show()
        pass

    def marginalizeDataset(self, dataset):
        if dataset not in self.datasets:
            raise ValueError("Could not marginalize {}: Dataset not found.".format(dataset))

        output_dict = {}
        # output_dict['_dataset'] = dataset

        for parameter_file in self.parameter_files:
            if (dataset, parameter_file) in self.metrics.keys():
                output_dict[parameter_file] = self.metrics[(dataset, parameter_file)]

        return output_dict

    def marginalizeParameterFile(self, parameter_file):
        if parameter_file not in self.parameter_files:
            raise ValueError("Could not marginalize {}: Parameter set not found.".format(parameter_file))

        output_dict = {}
        for dataset in self.datasets:
            if (dataset, parameter_file) in self.metrics.keys():
                output_dict[dataset] = self.metrics[(dataset, parameter_file)]

        return output_dict

    def joinDatasets(self, datasets='all'):
        # Join all datasets by default
        if datasets=='all':
            datasets = self.datasets
        if not set(datasets) <= self.datasets:
            raise Exception("Error. The datasets to be joined are not a subset of the stored datasets.")

        result_dict = defaultdict(dict)
        for dataset in datasets:
            dataset_runs = self.marginalizeDataset(dataset)
            # TODO Obsolete comment dataset_runs is a dict of form {parameter_file: { a: 1,
            #                                                   b: 2,
            #                                                   c: 3 }
            for parameter_file, metrics in dataset_runs.items():
                for key, metric in metrics.items():
                    if key not in result_dict[parameter_file].keys():
                        result_dict[parameter_file][key] = Metric()

                    result_dict[parameter_file][key].joinMetric(metric)

        return result_dict # TODO make this a proper class I think

    def getMetricsFromJoinedDataset(self, joined_datasets):
        metrics_dict = defaultdict(lambda: defaultdict(dict))
        for parameter_file, keys in joined_datasets.items():
            for key, value in keys.items():
                metrics_dict[key][parameter_file]["mean"] = value.mean
                metrics_dict[key][parameter_file]["stddev"] = value.stddev
                metrics_dict[key][parameter_file]["max"] = value.max
                metrics_dict[key][parameter_file]["min"] = value.min
                metrics_dict[key][parameter_file]["count"] = value.count

        return metrics_dict

    def getMetricsByParamset(self, joined_datasets):
        metrics_dict = defaultdict(lambda: defaultdict(dict))
        for parameter_file, keys in joined_datasets.items():

            for key, value in keys.items():
                metrics_dict[parameter_file][key]["mean"] = value.mean
                metrics_dict[parameter_file][key]["stddev"] = value.stddev
                metrics_dict[parameter_file][key]["max"] = value.max
                metrics_dict[parameter_file][key]["min"] = value.min
                metrics_dict[parameter_file][key]["count"] = value.count

        return metrics_dict

    def plotMetricsByParamset(self, metrics_dict):
        plt.figure()
        turn = 0
        patches = []

        ordered_metrics_dict = OrderedDict(sorted(metrics_dict.items()))

        for parameter_file, metrics in ordered_metrics_dict.items():
            # import ipdb; ipdb.set_trace()
            N = len(metrics)
            ind = 1.3*np.arange(N) + 0.2*turn

            means = []
            stddevs = []
            for key in sorted(metrics):
                # import ipdb; ipdb.set_trace()
                means.append(metrics[key]["mean"])
                stddevs.append(metrics[key]["stddev"])

            plt.bar(ind, means, 0.2, color=self.colors[turn], yerr=stddevs)

            # plt.title('{}'.format(parameter_file), fontsize=14)
            plt.xlabel('Metric')
            plt.ylabel('Value')
            
            plt.xticks(ind - 0.1 * (len(ordered_metrics_dict) - 1), sorted(metrics))
            patches.append(mpatches.Patch(color=self.colors[turn], label=parameter_file))
            turn += 1

        plt.legend(handles=patches)
        plt.grid()
        
        plt.show()

    def plotIndividualMetrics(self, metrics_dict):
        plt.figure()
        turn = 0
        patches = []

        ordered_metrics_dict = OrderedDict(sorted(metrics_dict.items()))

        for metric, occurrences in ordered_metrics_dict.items():

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
            
            plt.xticks(ind - 0.1 * (len(ordered_metrics_dict) - 1), sorted(occurrences))
            patches.append(mpatches.Patch(color=self.colors[turn], label=metric))
            turn += 1

        plt.legend(handles=patches)
        plt.grid()

        plt.show()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info('Summarization started')
    
    parser = argparse.ArgumentParser(description="""Sumarization job""")
    parser.add_argument('--files_to_summarize', help='test', default=[], action='append')
    args = parser.parse_args()

    import ipdb; ipdb.set_trace()
    # TODO add evaliuation paths as arg parameter
    files_to_summarize=[]

    ev = SimpleSummarization(files_to_summarize)
