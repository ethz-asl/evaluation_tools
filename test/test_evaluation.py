#!/usr/bin/env python

from __future__ import print_function

from evaluation_tools.catkin_utils import catkinFindSrc
from evaluation_tools.evaluation import Evaluation
from evaluation_tools.run_experiment import Experiment
import nose.tools
import os

RESULTS_FOLDER = './results'
AUTOMATIC_DATASET_DOWNLOAD = True


def _create_jobs():
  experiment_path = os.path.join(
      catkinFindSrc('evaluation_tools'), 'experiments',
      'sample_experiment.yaml')
  assert os.path.isfile(
      experiment_path), 'File ' + experiment_path + ' not found.'
  experiment = Experiment(experiment_path, RESULTS_FOLDER,
                          AUTOMATIC_DATASET_DOWNLOAD)
  return experiment.job_list, os.path.dirname(experiment_path)


def test_evaluation_creation():
  jobs, root_folder = _create_jobs()
  for job in jobs:
    evaluation = Evaluation(job)
