import pytest

from nncf.utils import training_mode_switcher

from tests.helpers import BasicConvTestModel, TwoConvTestModel, MockModel
from tests.quantization.test_saturation_issue_export import DepthWiseConvTestModel, EightConvTestModel

@pytest.mark.parametrize('model', [BasicConvTestModel(), TwoConvTestModel(), MockModel(),
                                   DepthWiseConvTestModel(), EightConvTestModel()])
def test_training_mode_switcher(model, _seed):
    saved_model_state = {}

    def save_model_training_state(module):
        for ch in module.children():
            saved_model_state[ch] = ch.training
            save_model_training_state(ch)

    def compare_saved_model_state_and_current_model_state(module):
        for ch in module.children():
            assert saved_model_state[ch] == ch.training
            compare_saved_model_state_and_current_model_state(ch)

    def randomly_change_model_training_state(module):
        import random
        for ch in module.children():
            if random.uniform(0, 1) > 0.5:
                ch.training = False
            else:
                ch.training = True
            randomly_change_model_training_state(ch)

    randomly_change_model_training_state(model)

    save_model_training_state(model)

    with training_mode_switcher(model, True):
        pass

    compare_saved_model_state_and_current_model_state(model)
