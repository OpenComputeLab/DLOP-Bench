# Copyright (c) OpenComputeLab. All Rights Reserved.

import torch
import torch.nn
import numpy as np
from bench.core.executer import Executer


def manual_seed(seed):
    return torch.manual_seed(seed)


def args_adaptor(np_args):
    seed = np_args[0]
    return [seed]


def executer_creator():
    return Executer(manual_seed, args_adaptor)
