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


class Preprocessing(object):

    def __init__(self, job_dir):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        self.job_dir = job_dir
        
        job_filename = os.path.join(job_dir, 'job.yaml')
        if not os.path.isfile(job_filename):
            raise ValueError("Job info file does not exist: " + job_filename)
        self.job = yaml.safe_load(open(job_filename))
        self.preprocessing_scripts = []
        if "preprocessing_scripts" in self.job and self.job['preprocessing_scripts'] is not None:
            self.preprocessing_scripts = self.job["preprocessing_scripts"]
            self.logger.info("Registering " + str(len(self.preprocessing_scripts)) \
                             + " preprocessing scripts.")
        else:
            self.logger.info("No preprocessing scripts in job.")
        
    def run_preprocessing(self):
        for script in self.preprocessing_scripts:
            self.logger.info("=== Run Preprocessing ===")            
            eval_utils.assert_param(script, "app_name")
            eval_utils.assert_param(script, "app_executable")            
            jp = Job()
            jp.set_python_executable(script["app_name"], script["app_executable"])
            jp.add_param("data_dir", self.job_dir)
            if "parameters" in script:
                for key, value in script["parameters"].items():
                    jp.add_param(key, value)
            jp.execute()

if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="""Preprocessing single job""")
    parser.add_argument('--job_dir', help='directory of the job', default='')
    args = parser.parse_args()
       
    if args.job_dir:
        j = Preprocessing(args.job_dir)
        j.run_preprocessing()
