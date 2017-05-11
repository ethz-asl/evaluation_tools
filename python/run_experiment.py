#!/usr/bin/env python

from evaluation import Evaluation
from job import Job
from preprocessing import Preprocessing
from simple_summarization import SimpleSummarization
import argparse
import catkin_utils
import copy
import datasets
import IPython
import logging
import numpy as np
import os
import shutil
import time
import utils as eval_utils
import yaml

class Experiment(object):
    
    def __init__(self, experiment_file, results_folder, automatic_dataset_download):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Checking parameters")
        experiment_path, experiment_file = os.path.split(experiment_file)
        if experiment_path == '':
          self.root_folder = catkin_utils.catkinFindSrc("evaluation_tools")
          self.results_folder = results_folder
        else:
          self.root_folder = os.path.split(experiment_path)[0]
          self.results_folder = self.root_folder + '/results/'
                            
        if len(self.root_folder) == 0:
          raise Exception("Unable to find the root folder of package evaluation_tools in the \
                          catkin workspace.")
                
        if not os.path.exists(self.results_folder):
          os.makedirs(self.results_folder)
          
        # Check Parameters
        if not experiment_file.endswith('.yaml'):
            experiment_file += '.yaml'
            
        self.experiment_file = self.root_folder + '/experiments/' + experiment_file
        if not os.path.isfile(self.experiment_file):
            raise ValueError("Could not find experiment YAML file: " + experiment_file)
                       
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
        else:
            experiment_basename = self.eval_dict['experiment_generated_time'] \
                + '_' + self.eval_dict["experiment_name"]

        # Find calibration file:
        if 'ncamera_calibration_file' in self.eval_dict.keys():
            ncamera_calibration_file = str(self.root_folder + '/calibrations/' + self.eval_dict['ncamera_calibration_file'])
            if not os.path.isfile(ncamera_calibration_file):
                raise Exception('Unable to find ncamera calibration file: ' + ncamera_calibration_file)

            self.eval_dict['ncamera_calibration_file'] = ncamera_calibration_file
            self.logger.info("NCamera calibration file: " + ncamera_calibration_file)
        else:
            self.eval_dict['ncamera_calibration_file'] = ''

        if 'wheel_odometry_calibration_file' in self.eval_dict.keys():
            wheel_odometry_calibration_file = str(self.root_folder + '/calibrations/' + self.eval_dict['wheel_odometry_calibration_file'])
            if not os.path.isfile(wheel_odometry_calibration_file):
                raise Exception('Unable to find wheel-odometry calibration file: ' + wheel_odometry_calibration_file)
            
            self.eval_dict['wheel_odometry_calibration_file'] = wheel_odometry_calibration_file
            self.logger.info("Wheel-odometry calibration file: " + wheel_odometry_calibration_file)
        else:
            self.eval_dict['wheel_odometry_calibration_file'] = ''

        if 'rt3k_calibration_file' in self.eval_dict.keys():
          rt3k_calibration_file = str(self.root_folder + '/calibrations/' + self.eval_dict['rt3k_calibration_file'])
          if not os.path.isfile(rt3k_calibration_file):
            raise Exception('Unable to find rt3k calibration file: ' + rt3k_calibration_file)
          
          self.eval_dict['rt3k_calibration_file'] = rt3k_calibration_file
          self.logger.info("RT3K calibration file: " + rt3k_calibration_file)
        else:
          self.eval_dict['rt3k_calibration_file'] = ''

        # Find the map if there is any.
        if 'localization_map' in self.eval_dict.keys() and not self.eval_dict['localization_map'] == None and not self.eval_dict['localization_map'] == '':
            localization_map = str(self.root_folder + '/maps/' + self.eval_dict['localization_map'])
            if not os.path.isdir(localization_map):
                raise Exception('Unable to find the localizatoin map: ' + localization_map)
                          
            self.eval_dict['localization_map'] = localization_map
            self.logger.info("Localization map: " + localization_map)
        else:
            self.eval_dict['localization_map'] = ''

        # Check if summarization is enabled
        self.summarize_statistics = False
        if 'summarize_statistics' in self.eval_dict:
            if 'enabled' in self.eval_dict['summarize_statistics']:
                if self.eval_dict['summarize_statistics']['enabled']:
                    self.summarize_statistics = True
                    # Summarization requires that each job runs the prepare_statistics.py script after execution
                    if 'evaluation_scripts' not in self.eval_dict or self.eval_dict['evaluation_scripts'] is None:
                        self.eval_dict['evaluation_scripts'] = []
                    self.eval_dict['evaluation_scripts'].append({'name': 'prepare_statistics.py'})

        # Create set of datasets and download them if needed
        self.datasets = set()
        local_dataset_dir = datasets.getLocalDatasetsFolder()
        available_datasets = datasets.getDatasetList()
        downloaded_datasets, data_dir = datasets.getDownloadedDatasets()
        for dataset in self.eval_dict['datasets']:
            # Check if dataset is available:
            dataset_path, dataset_name = os.path.split(dataset['name'])
            if not dataset_path == '':
                # Absolute path. 
                self.eval_dict['dataset'] = str(os.path.join(dataset_path, dataset_name))
            
            elif dataset['name'] not in downloaded_datasets:
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
            
            self.datasets.add(str(os.path.join(local_dataset_dir, dataset['name'])))
            # if os.path.isfile(self.eval_dict['dataset']):
            #     self.dataset_type = 'rosbag'
            #elif os.path.isdir(self.eval_dict['dataset']):
            #    self.dataset_type = 'csv'
            # else:
            #     raise ValueError('Dataset instance does not exist: '+self.eval_dict['dataset'])

        # Create set of parameter files
        self.parameter_files = set()
        for filename in self.eval_dict["parameter_files"]:
            if not os.path.isfile(self.root_folder + '/parameter_files/' + filename):
                raise ValueError(filename + ' parameter file was not found')
            self.parameter_files.add(filename)
          
        # Create jobs for all dataset-parameter file combination.
        self.job_paths = []
        for dataset in self.datasets:
            for parameter_file in self.parameter_files:
                filepath = self.root_folder + '/parameter_files/' + parameter_file
                params = yaml.safe_load(open(filepath))

                if 'parameter_sweep' in params:
                    p_name = params['parameter_sweep']["name"]
                    p_min = params['parameter_sweep']["min"]
                    p_max = params['parameter_sweep']["max"]
                    p_step_size = params['parameter_sweep']["step_size"]

                    step = 0
                    max_steps = 100
                    p_current = p_min
                    while p_current <= p_max and step < max_steps:
                        params[p_name] = p_current
                        self.eval_dict['experiment_name'] = str(experiment_basename + '/' \
                            + os.path.basename(dataset).replace('.bag','') + '__' \
                            + parameter_file.replace('.yaml', '') + '__SWEEP_' + str(step))
                        parameter_tag = str(parameter_file) + "_SWEEP_" + str(p_current)
                        self.job_paths.append(self._createJobFolder(params, str(dataset), parameter_tag))
                        p_current += p_step_size
                        step += 1
                else:
                    self.eval_dict['experiment_name'] = str(experiment_basename + '/' \
                        + os.path.basename(dataset).replace('.bag','') + '__' \
                        + parameter_file.replace('.yaml', ''))
                    self.job_paths.append(self._createJobFolder(params, str(dataset), str(parameter_file)))
                
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
        for key, value in job_parameters.items():
            if isinstance(value, str):
                value = value.replace('LOG_DIR', job_folder)
                value = value.replace('NCAM_CALIB_FILENAME', self.eval_dict['ncamera_calibration_file'])
                value = value.replace('WHEEL_ODO_CALIB_FILENAME', self.eval_dict['wheel_odometry_calibration_file'])
                value = value.replace('RT3K_CALIB_FILENAME', self.eval_dict['rt3k_calibration_file'])
                value = value.replace('BAG_FILENAME', dataset_name)
                value = value.replace('MAP', self.eval_dict['localization_map'])
                value = value.replace('OUTPUT_DIR', job_folder)
                job_parameters[key] = value
        # We do not want to pass parameter_sweep as an argument to the executable
        if 'parameter_sweep' in job_parameters:
            del job_parameters['parameter_sweep']
        if self.summarize_statistics:
            job_parameters['swe_write_statistics_to_file'] = 1

        # Write options to file.
        job_settings = copy.deepcopy(self.eval_dict)
        job_settings['parameter_file'] = parameter_file
        job_settings['dataset'] = dataset_name
        job_settings['parameters'] = job_parameters
        del job_settings['parameter_files']
        del job_settings['datasets']

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
            j.loadConfigFromFolder(job_path)
            j.execute()
            j.writeSummary("job_summary.yaml")
            
            self.logger.info("Run evaluation: " + job_path)
            j = Evaluation(job_path, self.root_folder)            
            j.runEvaluations()
    
    def runSummarization(self):
        if self.summarize_statistics:
            whitelist = []
            blacklist = []
            if 'whitelisted_metrics' in self.eval_dict['summarize_statistics']:
                whitelist = self.eval_dict['summarize_statistics']['whitelisted_metrics']
            if 'blacklisted_metrics' in self.eval_dict['summarize_statistics']:
                blacklist = self.eval_dict['summarize_statistics']['blacklisted_metrics']

            files_to_summarize = []
            for job_path in self.job_paths:
                files_to_summarize.append(job_path + "/formatted_stats.yaml")

            s = SimpleSummarization(files_to_summarize, whitelist, blacklist)
            s.runSummarization()

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

    # Run summarizations
    e.runSummarization()