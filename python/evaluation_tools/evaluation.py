#!/usr/bin/env python

import os
import yaml
import argparse
import logging
import utils as eval_utils
import IPython
from command_runner import CommandRunner


class Evaluation(object):

  def __init__(self, job_dir, root_folder):
    logging.basicConfig(level=logging.DEBUG)
    self.logger = logging.getLogger(__name__)
    self.job_dir = job_dir
    self.root_folder = root_folder

    job_filename = os.path.join(job_dir, 'job.yaml')
    if not os.path.isfile(job_filename):
      raise ValueError("Job info file does not exist: " + job_filename)
    self.job = yaml.safe_load(open(job_filename))
    self.evaluation_scripts = []
    if "evaluation_scripts" in self.job and \
        self.job['evaluation_scripts'] is not None:
      self.evaluation_scripts = self.job["evaluation_scripts"]
      self.logger.info("Registering " + str(len(self.evaluation_scripts)) \
                       + " evaluation scripts.")
    else:
      self.logger.info("No evaluation scripts in job.")

  def runEvaluations(self):
    for evaluation in self.evaluation_scripts:
      self.logger.info("=== Run Evaluation ===")
      if 'name' not in evaluation:
        raise Exception("Missing name tag")
      evaluation_script = evaluation['name']
      evaluation_script_with_path = eval_utils.findFileOrDir(
          self.root_folder, "evaluation", evaluation_script)

      params_dict = {
          "data_dir": self.job_dir,
          "localization_map": self.job['localization_map']
      }
      if "parameter_file" in self.job:
        params_dict["parameter_file"] = self.job["parameter_file"]
      if "dataset" in self.job:
        params_dict["dataset"] = self.job["dataset"]
      cmd_runner = CommandRunner(
          evaluation_script_with_path, params_dict=params_dict)
      cmd_runner.execute()


if __name__ == '__main__':

  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger(__name__)

  parser = argparse.ArgumentParser(description="""Evaluate single job""")
  parser.add_argument('job_dir', help='directory of the job', default='')
  args = parser.parse_args()

  if args.job_dir:
    j = Evaluation(args.job_dir)
    j.runEvaluations()
