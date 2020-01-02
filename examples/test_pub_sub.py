from experimentor.config import settings
from experimentor.core.publisher import Publisher
from experimentor.models.experiments.base_experiment import Experiment

publisher = Publisher(settings.GENERAL_STOP_EVENT)

exp = Experiment()
print('here')
test_func = lambda x: print(x)

exp.start.connect(test_func)

exp.start.emit('AAAA')
