#!/usr/bin/env python3

import logging
import sys
from distutils.util import strtobool

def assertParam(options, parameter_name):
    if parameter_name not in options:
        raise ValueError(parameter_name + " not set")
    
def checkParam(options, parameter_name, default_value):
    if parameter_name not in options:
        options[parameter_name] = default_value
        logger = logging.getLogger(__name__)
        logger.info("Setting default value for parameter '" + parameter_name  \
                    + "' = "+str(default_value))
                    
def userYesNoQuery(question):
    #sys.stdout.write('%s [y/n]\n' % question)
    while True:
      val = raw_input(question + " - Yes o No?\n")
      if val == 'y' or val == 'yes':
        return True
      elif val == 'n' or val == 'no':
        return False
      else:
        sys.stdout.write('Please respond with \'y\' or \'n\'.\n')
