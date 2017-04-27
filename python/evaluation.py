#!/usr/bin/env python3
"""
Zurich Eye
"""

import os
import yaml
import argparse
import logging
import utils as eval_utils
from job import Job
import IPython

class Evaluation(object):

    def __init__(self, job_dir):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.job_dir = job_dir
        
        job_filename = os.path.join(job_dir, 'job.yaml')
        if not os.path.isfile(job_filename):
            raise ValueError("Job info file does not exist: " + job_filename)
        self.job = yaml.safe_load(open(job_filename))
        self.evaluation_scripts = []
        if "evaluation_scripts" in self.job and self.job['evaluation_scripts'] is not None:
            self.evaluation_scripts = self.job["evaluation_scripts"]
            self.logger.info("Registering " + str(len(self.evaluation_scripts)) \
                             + " evaluation scripts.")
        else:
            self.logger.info("No evaluation scripts in job.")
        
    def runEvaluations(self):
        for evaluation, eval_arguments in self.evaluation_scripts.items():

            self.logger.info("=== Run Evaluation ===")
            eval_utils.assertParam(eval_arguments, "app_name")
            eval_utils.assertParam(eval_arguments, "app_executable")
            jp = Job()
            jp.setPythonExecutable(eval_arguments["app_name"], eval_arguments["app_executable"])
            jp.addParam("job_dir", self.job_dir)
            if "parameter_file" in self.job:
                jp.addParam("parameter_file", self.job["parameter_file"])
            if "dataset" in self.job:
                jp.addParam("dataset", self.job["dataset"])
            if "parameters" in eval_arguments:
                for key, value in eval_arguments["parameters"].items():
                    jp.addParam(key, value)
            jp.execute()


if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="""Evaluate single job""")
    parser.add_argument('job_dir', help='directory of the job', default='')
    args = parser.parse_args()
       
    if args.job_dir:
        j = Evaluation(args.job_dir)
        j.runEvaluations()
