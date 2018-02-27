import argparse
import yaml


class EvaluationArgParse:

  def __init__(self, description=''):
    self.parser = argparse.ArgumentParser(description)
    self.parser.add_argument('--data_dir')
    self.parser.add_argument('--localization_map', default='')
    self.parser.add_argument('--parameter_file', default='')
    self.parser.add_argument('--datasets', default='', nargs='+')
    self.parser.add_argument('--additional_dataset_parameters', type=yaml.load)
