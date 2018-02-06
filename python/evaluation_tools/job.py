#!/usr/bin/env python

import os
import yaml
import argparse
import logging
import catkin_utils
import IPython


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
    console_cmd_string = "rosrun maplab_console batch_runner --log_dir " + \
        self.job_path + " --batch_control_file " + os.path.join(
        self.job_path, "console_commands.yaml")
    self.logger.info("Executing command: " + console_cmd_string)
    os.system(console_cmd_string)

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
