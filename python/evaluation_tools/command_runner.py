#!/usr/bin/env python

import logging
import os


def runCommand(exec_path, params_dict={}):
  """Runs a system command with parameters coming from a python dictionary.

  Input:
  - exec_path: path to the executable.
  - params_dict: dictionary in the form {key: value} which contains the
      additional arguments for the command.

  Assuming params_dict contains {key1: value1, key2: value2, ...}, the command
  that is executed will be of the form:
    <exec_path> --<key1>=<value1> --<key2>=<value2> ...

  If no file under exec_path can be found or the command returns a non-zero exit
  code, an exception will be raised.
  """
  cmd_seq = []
  if len(exec_path) > 0 and os.path.isfile(exec_path):
    if exec_path.endswith('.py'):
      cmd_seq.append('python')
    cmd_seq.append(exec_path)
  else:
    raise ValueError("No file under " + exec_path + " exists.")

  for param in params_dict:
    cmd_seq.append("--" + param + "=" + str(params_dict[param]))

  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger(__name__)
  logger.info("Executing command {}".format(cmd_seq))
  cmd_string = ""
  for cmd in cmd_seq:
    cmd_string = cmd_string + cmd + " "
  logger.info("Executing command {}".format(cmd_string))

  return_value = os.system(cmd_string)
  if return_value != 0:
    raise Exception(
        'Command "' + cmd_string + '" returned with a non-zero exit code: ' +
        str(return_value))
