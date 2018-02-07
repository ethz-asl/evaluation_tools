#!/usr/bin/env python

import IPython
import argparse
import catkin_utils
import copy
import logging
import os
import yaml


class Job(object):

  def __init__(self):
    logging.basicConfig(level=logging.DEBUG)
    self.logger = logging.getLogger(__name__)
    self.params_dict = {}

  def setPythonExecutable(self, eval_app, executable):
    self.exec_app = eval_app
    self.exec_name = executable

  def setPythonExecutable(self, executable):
    self.exec_app = None
    self.exec_name = executable

  def loadConfigFromFolder(self, job_path):
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
    self.exec_path = os.path.join(self.exec_folder, self.info["app_executable"])

    if 'parameters' in self.info:
      self.params_dict = self.info['parameters']

  def addParam(self, key, value):
    self.params_dict[key] = value

  def _getCmdSeq(self):
    cmd_seq = []
    if self.exec_name.endswith('.py'):
      if self.exec_app is None:
        cmd_seq.append('python')
      else:
        cmd_seq.append('rosrun')
        cmd_seq.append(self.exec_app)

      cmd_seq.append(self.exec_name)
    else:
      if os.path.isfile(self.exec_path):
        cmd_seq.append(self.exec_path)
      else:
        cmd_seq.append(self.exec_name)
    for param in self.params_dict:
      cmd_seq.append("--" + param + "=" + str(self.params_dict[param]))
    return cmd_seq

  def execute(self):
    # Run estimator.
    cmd_seq = self._getCmdSeq()
    self.logger.info("Executing command {}".format(cmd_seq))
    cmd_string = ""
    for cmd in cmd_seq:
      cmd_string = cmd_string + cmd + " "
    self.logger.info("Executing command: " + cmd_string)
    os.system(cmd_string)

    # Run console commands.
    batch_runner_settings_file = os.path.join(self.job_path,
                                              "console_commands.yaml")
    if os.path.isfile(batch_runner_settings_file):
      console_cmd_string = "rosrun maplab_console batch_runner --log_dir " + \
          self.job_path + " --batch_control_file " + batch_runner_settings_file
      self.logger.info("Executing command: " + console_cmd_string)
      os.system(console_cmd_string)
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


def createJobFolder(dataset_name,
                    results_folder,
                    experiment_dict,
                    parameter_name,
                    parameter_dict,
                    summarize_statistics=False):
  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger("createJobFolder")
  job_folder = str(
      os.path.join(results_folder, experiment_dict['experiment_name']))
  logger.info("==> Creating job folder '{}'".format(job_folder))
  if not os.path.exists(job_folder):
    os.makedirs(job_folder)
  else:
    logger.info("Job folder already exists '{}'".format(job_folder))

  # Replace variables in parameters:
  job_parameters = copy.deepcopy(parameter_dict)
  job_parameters['log_dir'] = job_folder
  output_map_key = os.path.basename(dataset_name).replace('.bag', '')
  output_map_folder = os.path.join(job_folder, output_map_key)
  for key, value in job_parameters.items():
    if isinstance(value, str):
      value = value.replace('<LOG_DIR>', job_folder)
      value = value.replace('<SENSORS_YAML>', experiment_dict['sensors_file'])
      value = value.replace('<BAG_FILENAME>', dataset_name)
      value = value.replace('<LOCALIZATION_MAP>',
                            experiment_dict['localization_map'])
      value = value.replace('<OUTPUT_MAP_FOLDER>', output_map_folder)
      value = value.replace('<OUTPUT_DIR>', job_folder)
      job_parameters[key] = value

  # We do not want to pass parameter_sweep as an argument to the executable
  if 'parameter_sweep' in job_parameters:
    del job_parameters['parameter_sweep']
  if summarize_statistics:
    job_parameters['swe_write_statistics_to_file'] = 1

  # Write options to file.
  job_settings = copy.deepcopy(experiment_dict)
  job_settings['parameter_file'] = parameter_name
  job_settings['dataset'] = dataset_name
  job_settings['parameters'] = job_parameters
  del job_settings['parameter_files']
  del job_settings['datasets']

  # Write console batch runner file.
  if 'console_commands' in experiment_dict and len(
      experiment_dict['console_commands']) > 0:
    console_batch_runner_settings = {
        "vi_map_folder_paths": [output_map_folder],
        "commands": []
    }
    for command in experiment_dict['console_commands']:
      if isinstance(command, str):
        command = command.replace('<LOG_DIR>', job_folder)
        command = command.replace('<OUTPUT_MAP_FOLDER>', output_map_folder)
        command = command.replace('<OUTPUT_MAP_KEY>', output_map_key)
        console_batch_runner_settings['commands'].append(command)
        command = command.replace('<OUTPUT_DIR>', job_folder)
    del job_settings['console_commands']

    console_batch_runner_filename = os.path.join(job_folder,
                                                 "console_commands.yaml")
    logger.info("Write " + console_batch_runner_filename)
    with open(console_batch_runner_filename, "w") as out_file_stream:
      print console_batch_runner_settings
      yaml.dump(
          console_batch_runner_settings,
          stream=out_file_stream,
          default_flow_style=False,
          width=10000)  # Prevent random line breaks in long strings.

  job_filename = os.path.join(job_folder, "job.yaml")
  logger.info("Write " + job_filename)
  with open(job_filename, "w") as out_file_stream:
    yaml.dump(job_settings, stream=out_file_stream, default_flow_style=False)

  return job_folder


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
