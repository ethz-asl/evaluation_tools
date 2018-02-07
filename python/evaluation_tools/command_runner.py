#!/usr/bin/env python

import logging
import os

class CommandRunner:
  def __init__(self, exec_path, params_dict={}):
    logging.basicConfig(level=logging.DEBUG)
    self.logger = logging.getLogger(__name__)
    self.exec_path = exec_path
    self.params_dict = params_dict
    self.cmd_seq = self._getCmdSeq()

  def _getCmdSeq(self):
    cmd_seq = []
    if len(self.exec_path) > 0 and os.path.isfile(self.exec_path):
      if self.exec_path.endswith('.py'):
        cmd_seq.append('python')
      cmd_seq.append(self.exec_path)

    for param in self.params_dict:
      cmd_seq.append("--" + param + "=" + str(self.params_dict[param]))
    return cmd_seq

  def execute(self, text=''):
    if len(text) > 0:
      text = '[' + text + '] '
    self.logger.info("{}Executing command {}".format(text, self.cmd_seq))
    cmd_string = ""
    for cmd in self.cmd_seq:
      cmd_string = cmd_string + cmd + " "
    self.logger.info("{}Executing command {}".format(text, cmd_string))
    os.system(cmd_string)
