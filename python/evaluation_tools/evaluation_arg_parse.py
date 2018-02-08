import argparse


class EvaluationArgParse:

  def __init__(self, description=''):
    self.parser = argparse.ArgumentParser(description)
    self.parser.add_argument('--data_dir')
    self.parser.add_argument('--localization_map', default='')
    self.parser.add_argument('--parameter_file', default='')
    self.parser.add_argument('--dataset', default='')
