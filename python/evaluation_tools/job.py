#!/usr/bin/env python

import IPython
import argparse
import catkin_utils
import copy
import logging
import os
import yaml
from command_runner import runCommand


class Job(object):
  """Contains the information to run the experiment (estimator and console)."""

  def __init__(self):
    logging.basicConfig(level=logging.DEBUG)
    self.logger = logging.getLogger(__name__)
    self.params_dict = {}

  def createJob(self,
                dataset_name,
                results_folder,
                experiment_dict,
                parameter_name,
                parameter_dict,
                summarize_statistics=False):
    """Initializes the job.

    Input:
    - dataset_name: name of the dataset to be used.
    - results_folder: location to store the results in.
    - experiment_dict: dictionary containing the loaded information from the
          experiment yaml.
    - parameter_name: name of the parameter set of this job.
    - parameter_dict: dictionary containing all parameters for this job (loaded
          from the corresponding parameter yaml).
    - summarize_statistics: (only works with SWE).

    This function will do various things to initialize a job:
    1) Create a job folder in <results_folder>/<experiment_name>
       (experiment_name is read from the experiment_dict).
    2) Read parameters and replace all placedholders.
    3) Create control file for the maplab batch runner to later run console
       commands.
    4) Export the job control information to yaml for later reference.

    This function needs to be called once per job so that all necessary files
    are created on disks.
    """
    self.job_path = os.path.join(results_folder,
                                 experiment_dict['experiment_name'])
    self.logger.info("==> Creating job:in folder '{}'".format(self.job_path))
    if not os.path.exists(self.job_path):
      os.makedirs(self.job_path)
    else:
      self.logger.info("Job folder already exists '{}'".format(self.job_path))

    self.dataset_name = dataset_name
    self.sensors_file = experiment_dict['sensors_file']
    self.localization_map = experiment_dict['localization_map']
    self.output_map_key = os.path.basename(self.dataset_name).replace(
        '.bag', '')
    self.output_map_folder = os.path.join(self.job_path, self.output_map_key)

    self.params_dict = copy.deepcopy(parameter_dict)
    for key, value in self.params_dict.items():
      if isinstance(value, str):
        self.params_dict[key] = self.replacePlaceholdersInString(value)

    # We do not want to pass parameter_sweep as an argument to the executable.
    if 'parameter_sweep' in self.params_dict:
      del self.params_dict['parameter_sweep']
    if summarize_statistics:
      # TODO(eggerk): generalize or remove.
      self.params_dict['swe_write_statistics_to_file'] = 1

    # Write console batch runner file.
    if 'console_commands' in experiment_dict and \
        len( experiment_dict['console_commands']) > 0:
      console_batch_runner_settings = {
          "vi_map_folder_paths": [self.output_map_folder],
          "commands": []
      }
      for command in experiment_dict['console_commands']:
        if isinstance(command, str):
          console_batch_runner_settings['commands'].append(
              self.replacePlaceholdersInString(command))

      console_batch_runner_filename = os.path.join(self.job_path,
                                                   "console_commands.yaml")
      self.logger.info("Write " + console_batch_runner_filename)
      with open(console_batch_runner_filename, "w") as out_file_stream:
        yaml.dump(
            console_batch_runner_settings,
            stream=out_file_stream,
            default_flow_style=False,
            width=10000)  # Prevent random line breaks in long strings.

    # Write options to file.
    self.info = copy.deepcopy(experiment_dict)
    self.info['dataset'] = dataset_name
    self.info['parameter_file'] = parameter_name
    self.info['parameters'] = self.params_dict
    del self.info['parameter_files']
    del self.info['datasets']
    if 'console_commands' in self.info:
      del self.info['console_commands']

    job_filename = os.path.join(self.job_path, "job.yaml")
    self.logger.info("Write " + job_filename)
    with open(job_filename, "w") as out_file_stream:
      yaml.dump(self.info, stream=out_file_stream, default_flow_style=False)

    self.exec_app = self.info["app_package_name"]
    self.exec_name = self.info["app_executable"]
    self.exec_folder = catkin_utils.catkinFindLib(self.exec_app)
    self.exec_path = os.path.join(self.exec_folder, self.exec_name)

  def replacePlaceholdersInString(self, string):
    """Replaces placeholders in a string with the actual value for the job.

    This is used to adapt the parameters and console commands to the current
    running job. Replaced placeholders include the current job directory, the
    bag file and others.
    """
    string = string.replace('<LOG_DIR>', self.job_path)
    string = string.replace('<SENSORS_YAML>', self.sensors_file)
    string = string.replace('<BAG_FILENAME>', self.dataset_name)
    string = string.replace('<LOCALIZATION_MAP>', self.localization_map)
    string = string.replace('<OUTPUT_MAP_FOLDER>', self.output_map_folder)
    string = string.replace('<OUTPUT_MAP_KEY>', self.output_map_key)
    string = string.replace('<OUTPUT_DIR>', self.job_path)
    return string

  def loadConfigFromFolder(self, job_path):
    """Loads the job configuration from disk.

    Reads the file named job.yaml inside job_path to initialize the job.
    """
    self.job_path = job_path
    self.logger = logging.getLogger(__name__)

    job_filename = os.path.join(job_path, 'job.yaml')
    self.logger.info("Loading job config from file: " + job_filename)
    if not os.path.isfile(job_filename):
      raise ValueError("Job info file does not exist: " + job_filename)
    self.info = yaml.safe_load(open(job_filename))
    self.exec_app = self.info["app_package_name"]
    self.exec_name = self.info["app_executable"]
    self.exec_folder = catkin_utils.catkinFindLib(self.exec_app)
    self.exec_path = os.path.join(self.exec_folder, self.exec_name)

    if 'parameters' in self.info:
      self.params_dict = self.info['parameters']

  def execute(self):
    """Runs the estimator and maplab console as defined in this job."""
    # Run estimator.
    runCommand(self.exec_path, params_dict=self.params_dict)

    # Run console commands.
    batch_runner_settings_file = os.path.join(self.job_path,
                                              "console_commands.yaml")
    if os.path.isfile(batch_runner_settings_file):
      console_executable_path = catkin_utils.catkinFindLib("maplab_console")
      runCommand(
          os.path.join(console_executable_path, "batch_runner"),
          params_dict={
              "log_dir": self.job_path,
              "batch_control_file": batch_runner_settings_file
          })
    else:
      self.logger.info("No console commands to be run.")

  def writeSummary(self, filename):
    summary_dict = {}
    summary_dict["executable"] = {}
    summary_dict["executable"]["name"] = self.exec_name
    summary_dict["executable"]["path"] = self.exec_path
    summary_dict["executable"]["rev"] = \
        catkin_utils.getSrcRevision(self.exec_app)

    if "cam_id" in self.info:
      summary_dict["calib"] = {}
      summary_dict["calib"]["file"] = self.info["cam_calib_file"]
      summary_dict["calib"]["id"] = self.info["cam_id"]
      summary_dict["calib"]["rev"] = \
          catkin_utils.get_calib_revision(self.info["cam_id"])

    out_file_path = os.path.join(self.job_path, filename)
    out_file_stream = open(out_file_path, "w")
    yaml.dump(summary_dict, stream=out_file_stream, default_flow_style=False)


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger(__name__)

  parser = argparse.ArgumentParser(description="""Process single job""")
  parser.add_argument('job_dir', help='directory of the job', default='')
  args = parser.parse_args()

  if args.job_dir:
    j = Job()
    j.load_config_from_folder(args.job_dir)
    j.execute()
