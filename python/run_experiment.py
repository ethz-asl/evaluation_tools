#!/usr/bin/env python3
"""
Zurich Eye
"""

import os
import yaml
import copy
import time
import shutil
import logging
import argparse
import numpy as np
from job import Job
from evaluation import Evaluation
from preprocessing import Preprocessing
from rafa_evaluation import TestEvaluation
import catkin_utils
import utils as eval_utils
import datasets
import IPython

class Experiment(object):
    
    def __init__(self, experiment_file, results_folder, automatic_dataset_download):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Checking parameters")
        
        root_folder = catkin_utils.catkinFindSrc("evaluation_tools")
        if len(root_folder) == 0:
          raise Exception("Unable to find the root folder of package evaluation_tools in the \
                          catkin workspace.")
                
        # Check Parameters
        if not experiment_file.endswith('.yaml'):
            experiment_file += '.yaml'
            
        self.experiment_file = root_folder + '/experiments/' + experiment_file
        if not os.path.isfile(self.experiment_file):
            raise ValueError("Could not find evaluation YAML file: " + experiment_file)
        
        if not os.path.exists(results_folder):
          os.makedirs(results_folder)
        self.results_folder = results_folder
                
        # Read Evaluation File
        self.experiment_filename = os.path.basename(experiment_file).replace('.yaml','')
        self.eval_dict = yaml.safe_load(open(self.experiment_file))
        self.experiment_file = experiment_file
        
        # Check necessary parameters in evaluation file:
        eval_utils.assertParam(self.eval_dict, "app_package_name")        
        eval_utils.assertParam(self.eval_dict, "app_executable")        
        eval_utils.assertParam(self.eval_dict, "datasets")
        eval_utils.assertParam(self.eval_dict, "parameter_files")
        eval_utils.checkParam(self.eval_dict, "cam_calib_source", "dataset_folder")
        
        # Information stored in the job but not used to run the algorithm.
        self.eval_dict['experiment_generated_time'] = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        self.eval_dict['experiment_filename'] = self.experiment_filename
        
        # Set experiment basename
        if "experiment_name" not in self.eval_dict:
          experiment_basename = self.eval_dict['experiment_generated_time'] \
              + '_' + self.eval_dict['experiment_filename'] 
        
        # Find calibration files:
        if 'ncamera_calibration_file' in self.eval_dict.keys():
          ncamera_calibration_file = str(root_folder + '/calibrations/' + self.eval_dict['ncamera_calibration_file'])
          if not os.path.isfile(ncamera_calibration_file):
            raise Exception('Unable to find ncamera calibration file: ' + ncamera_calibration_file)
          
          self.eval_dict['ncamera_calibration_file'] = ncamera_calibration_file
          self.logger.info("NCamera calibration file: " + ncamera_calibration_file)

        if 'additional_odometry_calibration_file' in self.eval_dict.keys():
          additional_odometry_calibration_file = str(root_folder + '/calibrations/' + self.eval_dict['additional_odometry_calibration_file'])
          if not os.path.isfile(additional_odometry_calibration_file):
            raise Exception('Unable to find additional odometry calibration file: ' + additional_odometry_calibration_file)
          
          self.eval_dict['additional_odometry_calibration_file'] = additional_odometry_calibration_file
          self.logger.info("Additional odometry calibration file: " + additional_odometry_calibration_file)
  
        # Datasets
        local_dataset_dir = datasets.getLocalDatasetsFolder()
        available_datasets = datasets.getDatasetList()
        downloaded_datasets, data_dir = datasets.getDownloadedDatasets()
        self.job_paths = []
        self.datasets = []
        for dataset in self.eval_dict['datasets']:        
            # Check if dataset is available:
            if dataset['name'] not in downloaded_datasets:
                self.logger.info("Dataset '" + dataset['name'] + "' is not available")
                if dataset['name'] not in available_datasets:
                    self.logger.info("Dataset is not available on the server.")
                    #raise Exception("Dataset not found.")
                
                # Download dataset:
                if automatic_dataset_download:
                    download = True
                else:
                    download = eval_utils.userYesNoQuery("Download datasets from server?")
                if download:                
                    datasets.downloadDataset(dataset['name'])
                    available_datasets = datasets.getDatasetList()
                    downloaded_datasets, local_dataset_dir = datasets.getDownloadedDatasets()
                
            # Get name of bagfile/csv.
            dataset_path = str(os.path.join(local_dataset_dir, dataset['name']))
            self.datasets.append(dataset_path)
            if os.path.isfile(dataset_path):
                self.dataset_type = 'rosbag'
            #elif os.path.isdir(self.eval_dict['dataset']):
            #    self.dataset_type = 'csv'
            else:
                raise ValueError('Dataset instance does not exist: '+self.eval_dict['dataset'])
                     
        # Gather all parameters (from files, yaml, sweep, dataset specific)
        self.parameter_files = []
        for filename in self.eval_dict["parameter_files"]:
            if os.path.isfile(root_folder + '/parameter_files/' + filename):
                self.parameter_files.append(filename)
            else:
                raise ValueError(filename + ' parameter file was not found')
            # filepath = root_folder + '/parameter_files/' + filename
            # for key, value in params.items():
            #     parameters[key] = value # ordering of files is important as we may overwrite parameters.
        
        # and create the job folder.
        for parameter_file in self.parameter_files:
            filepath = root_folder + '/parameter_files/' + filename
            params = yaml.safe_load(open(filepath))
            for dataset in self.datasets:
                self.eval_dict['experiment_name'] = str(experiment_basename + '/' \
                    + os.path.basename(dataset).replace('.bag','') + '__' \
                    + parameter_file.replace('.yaml', ''))
                self.job_paths.append(self._createJobFolder(params, str(dataset), str(parameter_file)))
                
        # if "parameter_sweep" in self.eval_dict:
        #     raise Exception("Currently not supported")
        #     #self.logger.info("Generating parameter sweep jobs")
        #     #param_sweep = self.eval_dict["parameter_sweep"]
        #     #p_name = param_sweep["name"]
        #     #p_min = param_sweep["min"]
        #     #p_max = param_sweep["max"]
        #     #p_num_steps = param_sweep["num_steps"]

        #     #for value in np.linspace(p_min, p_max, p_num_steps):
        #     #    parameters[p_name] = float(value)
        #     #    self.eval_dict['experiment_name'] = experiment_basename + \
        #     #    '_' + dataset['name'] + '_' + dataset['instance'].replace('.bag','') + \
        #     #    '_' + p_name + '=' + str(value) 
        #     #    self.job_paths.append(self._create_job_folder(parameters, dataset['name']))
            
        # else:
        #     self.eval_dict['experiment_name'] = str(experiment_basename + '_' \
        #         + dataset['name'].replace('.bag',''))
        #     self.job_paths.append(self._createJobFolder(parameters, str(dataset['name'])))
                
    def _createJobFolder(self, parameters, dataset_name, parameter_file):
        job_folder = str(os.path.join(self.results_folder, self.eval_dict['experiment_name']))
        self.logger.info("==> Creating job folder '{}'".format(job_folder))
        if not os.path.exists(job_folder):
            os.makedirs(job_folder)
        else:
            self.logger.info("Job folder already exists '{}'".format(job_folder))
               
        # Replace variables in parameters:
        job_parameters = copy.deepcopy(parameters)
        job_parameters['log_dir'] = job_folder
        job_parameters['swe_write_statistics_to_file'] = 1 # TODO make this an option
        for key, value in job_parameters.items():
          if isinstance(value, str):
              value = value.replace('LOG_DIR', job_folder)
              value = value.replace('NCAM_CALIB_FILENAME', self.eval_dict['ncamera_calibration_file'])
              value = value.replace('ODOM_CALIB_FILENAME', self.eval_dict['additional_odometry_calibration_file'])
              value = value.replace('BAG_FILENAME', dataset_name)
              job_parameters[key] = value

        # Write options to file
        job_settings = copy.deepcopy(self.eval_dict)
        del job_settings['parameter_files']
        del job_settings['datasets']
        job_settings['parameter_file'] = parameter_file
        job_settings['dataset'] = dataset_name
        job_settings['parameters'] = job_parameters
        job_filename = os.path.join(job_folder, "job.yaml")
        self.logger.info("Write " + job_filename)
        out_file_stream = open(job_filename, "w")
        yaml.dump(job_settings, stream=out_file_stream, default_flow_style=False)
        
        # Copy groundtruth if available
        #if self.dataset_type == 'rosbag':
        #    gt_filename = self.eval_dict['dataset'].replace('.bag','_groundtruth.csv')
        #else:
        #    gt_filename = os.path.join(self.eval_dict['dataset'], 'groundtruth.csv')
        #if os.path.isfile(gt_filename):
        #    gt_filename_copied = os.path.join(job_folder, 'traj_gt.csv')
        #    self.logger.info('Copy groundtruth ' + gt_filename + ' to job folder: ' \
        #                     + gt_filename_copied)
        #    shutil.copyfile(gt_filename, gt_filename_copied)
        
        return job_folder

    def preprocessing(self):
        for job_path in self.job_paths:
            self.logger.info("Preprocessing: " + job_path)
            j = Preprocessing(job_path)            
            j.runPreprocessing()
        
    def runAndEvaluate(self):       
        for job_path in self.job_paths:
            self.logger.info("Run job: " + job_path + "/job.yaml")
            j = Job()
            j.loadConfigFromFolder(job_path)
            j.execute()
            j.writeSummary("job_summary.yaml")
            
            self.logger.info("Run evaluation: " + job_path)
            j = Evaluation(job_path)
            j.runEvaluations()

    def runRafaEvaluation(self):
        evaluation_files = []
        for job_path in self.job_paths:
            evaluation_files.append(job_path + "/statistics.yaml")

        j = TestEvaluation(evaluation_files)

          
if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info('Experiment started')

    local_data_folder_default = datasets.getLocalDatasetsFolder()
    experiments_folder = catkin_utils.catkinFindSrc('evaluation_tools')
    if experiments_folder:
        input_folder_default = os.path.join(experiments_folder, 'experiments')        
        output_folder_default = os.path.join(experiments_folder, 'results')
    else:
        input_folder_default = ''
        output_folder_default = ''
    
    parser = argparse.ArgumentParser(description='''Experiment''')
    parser.add_argument('experiment_yaml_file', help='Experiment YAML file in input_folder')
    #parser.add_argument('--input_folder', help='The path to the evaluation files',
    #                    default=input_folder_default)
    parser.add_argument('--results_output_folder', help='The folder where to store results',
                        default=output_folder_default)
    parser.add_argument('--data_folder', help='the path to the input data',
                        default=local_data_folder_default)
    parser.add_argument('--automatic_download', action='store_true',
                        help='download dataset if it is not available locally')
    args = parser.parse_args()
    
    eval_file = args.experiment_yaml_file
    
    # Create experiment folders.
    e = Experiment(eval_file, args.results_output_folder, args.automatic_download)
                   
    # Run Preprocessing
    e.preprocessing()
    
    # Run each job and the evaluation of each job.
    e.runAndEvaluate()

    e.runRafaEvaluation()