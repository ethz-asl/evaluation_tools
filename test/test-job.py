#!/usr/bin/env python

from __future__ import print_function

from evaluation_tools.catkin_utils import catkinFindSrc
from evaluation_tools.job import Job
from evaluation_tools.run_experiment import Experiment
import os

RESULTS_FOLDER = './results'
AUTOMATIC_DATASET_DOWNLOAD = True


def test_create_job():
  experiment_path = os.path.join(
      catkinFindSrc('evaluation_tools'), 'experiments',
      'sample_experiment.yaml')
  assert os.path.isfile(
      experiment_path), 'File ' + experiment_path + ' not found.'
  experiment = Experiment(experiment_path, RESULTS_FOLDER,
                          AUTOMATIC_DATASET_DOWNLOAD)
  jobs = experiment.job_list
  print('Number of jobs:', len(jobs))
  for job in jobs:
    print('Checking job:', job.job_path)
    job_from_file = Job()
    job_from_file.loadConfigFromFolder(job.job_path)
    assert job == job_from_file, \
        "Job %s wasn't loaded correctly from file" % job.job_path
