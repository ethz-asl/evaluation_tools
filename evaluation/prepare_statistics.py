#!/usr/bin/env python

import os
import yaml
import argparse
import logging
from collections import defaultdict

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger(__name__)

  parser = argparse.ArgumentParser(description="""Format a statistics file
        to be used in the standard evaluation.""")
  parser.add_argument('--data_dir', help='directory of the job')
  parser.add_argument('--dataset', help='dataset used in the job')
  parser.add_argument('--parameter_file', help='parameter file used in the job')

  args, unknown = parser.parse_known_args()

  logger.info("Formatting statistics in {}".format(args.data_dir))

  statistics_path = args.data_dir + '/statistics.yaml'
  if not os.path.isfile(statistics_path):
    raise ValueError(
        'Could not open statistics file in {}'.format(statistics_path))
  statistics = yaml.safe_load(open(statistics_path))

  formatted_stats = {}
  formatted_stats['dataset'] = args.dataset
  formatted_stats['parameter_file'] = args.parameter_file
  formatted_stats['metrics'] = statistics

  output_path = args.data_dir + '/formatted_stats.yaml'
  logger.info("Formatting complete. New file in {}".format(output_path))
  out_file_stream = open(output_path, "w")

  yaml.dump(formatted_stats, stream=out_file_stream, default_flow_style=False)
