import torch
import torch.nn
from long_tail_bench.core.executer import Executer


def conv2d(input_image, in_channels, out_channels, kernel_size, bias, stride, padding, dilation, groups):
    conv2d = torch.nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, groups=groups, bias=bias).cuda()
    ret = conv2d(input_image)
    return ret


def args_adaptor(np_args):
    input_image = torch.from_numpy(np_args[0]).to(torch.float32).cuda()
    in_channels = np_args[1][1]
    out_channels = np_args[2][0]
    kernel_size = [np_args[2][2], np_args[2][3]]
    bias = np_args[3][0]
    stride = np_args[4]
    padding = np_args[5]
    dilation = np_args[6]
    groups = np_args[7][0]
    return [input_image, in_channels, out_channels, kernel_size, bias, stride, padding, dilation, groups]


def executer_creator():
    return Executer(conv2d, args_adaptor)
