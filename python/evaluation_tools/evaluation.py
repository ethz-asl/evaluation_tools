#!/usr/bin/env python

from __future__ import print_function

import os
import yaml
import argparse
import logging
import utils as eval_utils
from command_runner import CommandRunnerException, runCommand


class Evaluation(object):

  def __init__(self, job, root_folder):
    logging.basicConfig(level=logging.DEBUG)
    self.logger = logging.getLogger(__name__)
    self.job = job
    self.job_dir = job.job_path
    self.root_folder = root_folder

    self.evaluation_scripts = []
    if "evaluation_scripts" in self.job.info and \
        self.job.info['evaluation_scripts'] is not None:
      self.evaluation_scripts = self.job.info["evaluation_scripts"]
      self.logger.info("Registering " + str(len(self.evaluation_scripts)) \
                       + " evaluation scripts.")
    else:
      self.logger.info("No evaluation scripts in job.")

  def runEvaluations(self):
    evaluation_script_results = {}
    additional_dataset_parameters_str = yaml.dump(
        self.job.dataset_additional_parameters, width=10000)
    additional_dataset_parameters_str = \
        '"' + additional_dataset_parameters_str + '"'
    for evaluation in self.evaluation_scripts:
      self.logger.info("=== Run Evaluation ===")
      if 'name' in evaluation:
        if 'package' in evaluation:
          package_path = catkin_utils.catkinFindLib(evaluation['package'])
          evaluation_script_with_path = os.path.join(
              package_path, evaluation['name'])
        else:
          evaluation_script = evaluation['name']
          evaluation_script_with_path = eval_utils.findFileOrDir(
              self.root_folder, "evaluation", evaluation_script)
      else:
        raise Exception(
            'Please provide a "name" entry and optionally a "package" entry in '
            'the evaluation script listing.')

      params_dict = {
          "data_dir": self.job_dir,
          "localization_map": self.job.info['localization_map'],
          "additional_dataset_parameters": additional_dataset_parameters_str
      }
      if 'arguments' in evaluation:
        params_dict.update(evaluation['arguments'])
      if "parameter_file" in self.job.info:
        params_dict["parameter_file"] = self.job.info["parameter_file"]
      params_dict["datasets"] = ' '.join(self.job.dataset_names)
      try:
        runCommand(evaluation_script_with_path, params_dict=params_dict)
        evaluation_script_results[evaluation['name']] = 0
      except CommandRunnerException as ex:
        print(
            'Evaluation "',
            evaluation['name'],
            '" from job "',
            self.job.job_name,
            '" exited with non-zero return value: ',
            ex.return_value,
            sep='')
        evaluation_script_results[evaluation['name']] = ex.return_value

    return evaluation_script_results


if __name__ == '__main__':

  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger(__name__)

  parser = argparse.ArgumentParser(description="""Evaluate single job""")
  parser.add_argument('job_dir', help='directory of the job', default='')
  args = parser.parse_args()

  if args.job_dir:
    j = Evaluation(args.job_dir)
    j.runEvaluations()
