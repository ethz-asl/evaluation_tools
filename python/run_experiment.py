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
import catkin_utils
import utils as eval_utils
import datasets
import IPython

class Experiment(object):
    
    def __init__(self, experiment_file, results_folder, automatic_dataset_download):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Checking parameters")
        
        # Check Parameters
        if not experiment_file.endswith('.yaml'):
            experiment_file += '.yaml'
        if not os.path.isfile(experiment_file):
            raise ValueError("Could not find evaluation YAML file: " + experiment_file)
        self.experiment_file = experiment_file
        
        if not os.path.exists(results_folder):
            raise ValueError("Folder to store results does not exist: " + results_folder)            
        self.results_folder = results_folder
                
        # Read Evaluation File
        self.experiment_filename = os.path.basename(experiment_file).replace('.yaml','')
        self.experiment_path = os.path.dirname(experiment_file)
        self.eval_dict = yaml.safe_load(open(self.experiment_file))
        self.experiment_file = experiment_file
        
        # Check necessary parameters in evaluation file:
        eval_utils.assertParam(self.eval_dict, "app_name")        
        eval_utils.assertParam(self.eval_dict, "app_executable")        
        eval_utils.assertParam(self.eval_dict, "datasets")
        eval_utils.checkParam(self.eval_dict, "cam_calib_source", "dataset_folder")
        
        # Information stored in the job but not used to run the algorithm.
        self.eval_dict['experiment_generated_time'] = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        self.eval_dict['experiment_filename'] = self.experiment_filename
        
        # Set experiment basename
        if "experiment_name" not in self.eval_dict:
          experiment_basename = self.eval_dict['experiment_generated_time'] \
              + '_' + self.eval_dict['experiment_filename'] 
                    
        # Datasets
        available_datasets = datasets.getDatasetList()
        downloaded_datasets, data_dir = datasets.getDownloadedDatasets()
        self.job_paths = []  
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
            self.eval_dict['dataset'] = os.path.join(local_dataset_dir, dataset['name'], dataset['instance'])
            if os.path.isfile(self.eval_dict['dataset']):
                self.dataset_type = 'rosbag'
            elif os.path.isdir(self.eval_dict['dataset']):
                self.dataset_type = 'csv'
            else:
                raise ValueError('Dataset instance does not exist: '+self.eval_dict['dataset'])
                     
            # Find calibration file:
            #if self.eval_dict["ncamera_calibration_id"] == "ze_calibration":
            #    self.logger.info("Calibration source: ze_calibration repository")
            #    cam_calib_folder = catkin_utils.catkin_find_cam_calib(str(self.eval_dict["cam_id"]))
            #    self.eval_dict["cam_calib_path"] = os.path.join(cam_calib_folder, self.eval_dict["cam_calib_file"])  
            #    self.eval_dict["cam_calib_rev"] = catkin_utils.get_calib_revision(self.eval_dict["cam_id"])
            
            #elif self.eval_dict["cam_calib_source"] == "dataset_folder":
            #    self.logger.info("Calibration source: dataset folder")
            #    self.eval_dict["cam_calib_path"] = \
            #        os.path.join(data_folder, dataset["name"], self.eval_dict["cam_calib_file"])
            
            #if not os.path.isfile(self.eval_dict["cam_calib_path"]):
            #    raise ValueError("Calibration file does not exist: "+self.eval_dict["cam_calib_path"])
            self.logger.info("Calibration file: " + self.eval_dict["cam_calib_path"])
            
            # Gather all parameters (from files, yaml, sweep, dataset specific)
            # and create the job folder.
            parameters = {}
            if "parameter_files" in self.eval_dict:
              raise Exception("Currently not supported")
              #for filename in self.eval_dict["parameter_files"]:
              #    filepath = os.path.join(self.experiment_path, filename)
              #    params = yaml.safe_load(open(filepath))
              #    for key, value in params.items():
              #        parameters[key] = value # ordering of files is important as we may overwrite parameters.
                        
            if "parameters" in self.eval_dict:
                for key, value in self.eval_dict["parameters"].items():
                    parameters[key] = value
                    
            if "parameter_sweep" in self.eval_dict:
              raise Exception("Currently not supported")
              #self.logger.info("Generating parameter sweep jobs")
              #param_sweep = self.eval_dict["parameter_sweep"]
              #p_name = param_sweep["name"]
              #p_min = param_sweep["min"]
              #p_max = param_sweep["max"]
              #p_num_steps = param_sweep["num_steps"]
              
              #for value in np.linspace(p_min, p_max, p_num_steps):
              #    parameters[p_name] = float(value)
              #    self.eval_dict['experiment_name'] = experiment_basename + \
              #    '_' + dataset['name'] + '_' + dataset['instance'].replace('.bag','') + \
              #    '_' + p_name + '=' + str(value) 
              #    self.job_paths.append(self._create_job_folder(parameters, dataset['name']))
                
            else:
                self.eval_dict['experiment_name'] = experiment_basename + \
                '_' + dataset['name'] + '_' + dataset['instance'].replace('.bag','')
                self.job_paths.append(self._createJobFolder(parameters, dataset['name']))
                
    def _createJobFolder(self, parameters, dataset_name):
        job_folder = os.path.join(self.results_folder, self.eval_dict['experiment_name'])
        self.logger.info("==> Creating job folder '{}'".format(job_folder))
        if not os.path.exists(job_folder):
            os.makedirs(job_folder)
        else:
            self.logger.info("Job folder already exists '{}'".format(job_folder))
               
        # Replace variables in parameters:
        job_parameters = copy.deepcopy(parameters)
        job_parameters['log_dir'] = job_folder
        experiments_folder = catkin_utils.catkin_find_experiments_folder()
        for key, value in job_parameters.items():
          print 'alpha'
          IPython.embed()
          if isinstance(value, str):
              value = value.replace('ZE_EXPERIMENTS', experiments_folder)
              value = value.replace('DATASET_DIR', os.path.join(self.data_folder, dataset_name))
              value = value.replace('LOG_DIR', job_folder)
              value = value.replace('CAM_CALIB_FILENAME', self.eval_dict['cam_calib_path'])
              value = value.replace('BAG_FILENAME', self.eval_dict['dataset'])
              job_parameters[key] = value

        # Write options to file
        job_settings = copy.deepcopy(self.eval_dict)
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
            j.run_preprocessing()
        
    def runAndEvaluate(self):       
        for job_path in self.job_paths:
            self.logger.info("Run job: " + job_path + "/job.yaml")
            j = Job()
            j.load_config_from_folder(job_path)
            j.execute()
            j.writeSummary("job_summary.yaml")
            
            self.logger.info("Run evaluation: " + job_path)
            j = Evaluation(job_path)            
            j.runEvaluations()
          
          
if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info('Experiment started')

    local_data_folder_default = datasets.getLocalDatasetsFolder()
    experiments_folder = catkin_utils.catkinFindExperimentsFolder()
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
    e.run_and_evaluate()
