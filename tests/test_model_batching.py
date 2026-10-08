"""Exercise batching and deadline behavior without loading model weights."""
import threading
from types import SimpleNamespace

import pytest
import torch

from mymanah.errors import ServiceError
from mymanah.models import Models


def adapter(length, observed, on_forward=lambda: None):
    models = object.__new__(Models)
    models.cpu_lock = threading.RLock()
    models.torch = torch
    models.entailment = 1

    def tokenize(premises, hypotheses, **kwargs):
        return {"input_ids": torch.tensor([[int(p)] * length for p in premises])}

    def forward(input_ids):
        observed.append(tuple(input_ids.shape))
        on_forward()
        return SimpleNamespace(logits=torch.stack((torch.zeros(len(input_ids)), input_ids[:, 0].float()), dim=1))

    models.nli_tokenizer = tokenize
    models.nli = forward
    return models


@pytest.mark.parametrize("length,shapes", [(32, [(8, 32), (1, 32)]), (400, [(2, 400)] * 4 + [(1, 400)])])
def test_nli_batches_bound_padded_tokens_and_preserve_pair_order(length, shapes):
    observed = []
    result = adapter(length, observed).support([(str(i), "hypothesis") for i in range(9)])
    assert observed == shapes
    assert result == pytest.approx(torch.sigmoid(torch.arange(9).float()).tolist())


def test_expired_classifier_stops_before_starting_another_batch(monkeypatch):
    clock, observed = [0.0], []
    monkeypatch.setattr("mymanah.models.time.monotonic", lambda: clock[0])
    models = adapter(400, observed, lambda: clock.__setitem__(0, 2.0))
    with pytest.raises(ServiceError) as failure:
        models.support([(str(i), "hypothesis") for i in range(9)], deadline=1.0)
    assert failure.value.status == 504
    assert observed == [(2, 400)]
