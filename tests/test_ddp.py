import pytest
import torch
import torch.nn as nn
import torch.multiprocessing as mp
import time
from typing import Tuple
from nncf import create_compressed_model
from nncf import register_default_init_args
from nncf import NNCFConfig

from tests.helpers import create_mock_dataloader


class TestModelWithChangedTrain(nn.Module):
    def __init__(self, in_out_channels: Tuple[Tuple[int, int]] = ((1, 3), (3, 5), (5, 7), (7, 10)),
                 freezing_stages: int = -1):
        super(TestModelWithChangedTrain, self).__init__()
        self.freezing_stages = freezing_stages
        self.features = nn.ModuleList()
        for i in range(len(in_out_channels)):
            block = nn.ModuleList()
            block.append(nn.Conv2d(*in_out_channels[i], 3))
            block.append(nn.BatchNorm2d(in_out_channels[i][1]))
            block.append(nn.ReLU())
            self.features.append(block)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for blocks in self.features:
            for module in blocks:
                x = module(x)
        return x

    def train(self: nn.Module, mode: bool = True) -> nn.Module:
        super().train(mode)
        for i in range(self.freezing_stages):
            for module in self.features[i]:
                for p in module.parameters():
                    p.requires_grad = False


def worker(rank: int, world_size: int) -> None:
    torch.distributed.init_process_group(backend="nccl", init_method='tcp://127.0.0.1:8999',
                                         world_size=world_size, rank=rank)
    model = TestModelWithChangedTrain(freezing_stages=1)
    model.cuda()
    model.to(rank)

    nncf_config = NNCFConfig()
    nncf_config.update({
        "input_info": {
            "sample_size": [1, 1, 30, 30]
        },
        "compression": {
            "algorithm": "quantization",
            "initializer": {
                "range": {
                    "num_init_samples": 10
                },
                "batchnorm_adaptation": {
                    "num_bn_adaptation_samples": 10,
                }
            }
        }
    })
    dataloader = create_mock_dataloader(nncf_config, 10)
    register_default_init_args(nncf_config, dataloader)

    _, compressed_model = create_compressed_model(model, nncf_config)

    # At this part the additional processes may be freezing

    compressed_model = torch.nn.parallel.DistributedDataParallel(compressed_model, device_ids=[rank])


@pytest.mark.parametrize('waiting_time', [30.0])
def test_is_ddp_frezing(waiting_time: float) -> None:
    # Number of processes the same as GPU count
    n_procs = torch.cuda.device_count()
    ctx = mp.spawn(fn=worker, args=(n_procs,), nprocs=n_procs, join=False)

    start_time = time.monotonic()
    while not ctx.join(waiting_time):
        current_time = time.monotonic()
        if current_time - start_time >= waiting_time:
            for process in ctx.processes:
                if process.is_alive():
                    process.terminate()
            raise TimeoutError("DDP wrapper may be freezing")
