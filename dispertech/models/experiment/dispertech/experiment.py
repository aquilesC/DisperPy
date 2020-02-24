from experimentor.models.experiments.base_experiment import Experiment


class Dispertech(Experiment):
    def __init__(self, config_file=None):
        super().__init__(filename=config_file)


