# Copyright (c) OpenComputeLab. All Rights Reserved.

import io
import numpy as np
from torch import nn
import torch.utils.model_zoo as model_zoo
import torch.onnx

import torch.nn as nn
import torch.nn.init as init
from gen_data import gen_np_args, args_adaptor

import onnx
# import onnxoptimizer

def bbox_rescale(bboxes, scale_factor=1.0):
    """Rescale bounding box w.r.t. scale_factor.

    Args:
        bboxes (Tensor): Shape (n, 4) for bboxes or (n, 5) for rois
        scale_factor (float): rescale factor

    Returns:
        Tensor: Rescaled bboxes.
    """
    if bboxes.size(1) == 5:
        bboxes_ = bboxes[:, 1:]
        inds_ = bboxes[:, 0]
    else:
        bboxes_ = bboxes
    cx = (bboxes_[:, 0] + bboxes_[:, 2]) * 0.5
    cy = (bboxes_[:, 1] + bboxes_[:, 3]) * 0.5
    w = bboxes_[:, 2] - bboxes_[:, 0]
    h = bboxes_[:, 3] - bboxes_[:, 1]
    w = w * scale_factor
    h = h * scale_factor
    x1 = cx - 0.5 * w
    x2 = cx + 0.5 * w
    y1 = cy - 0.5 * h
    y2 = cy + 0.5 * h
    if bboxes.size(1) == 5:
        rescaled_bboxes = torch.stack([inds_, x1, y1, x2, y2], dim=-1)
    else:
        rescaled_bboxes = torch.stack([x1, y1, x2, y2], dim=-1)
    return rescaled_bboxes


def generate_buckets(proposals, num_buckets=8, scale_factor=1.0):
    """Generate buckets w.r.t bucket number and scale factor of proposals.

    Args:
        proposals (Tensor): Shape (n, 4)
        num_buckets (int): Number of buckets.
        scale_factor (float): Scale factor to rescale proposals.

    Returns:
        tuple[Tensor]: (bucket_w, bucket_h, l_buckets, r_buckets,
         t_buckets, d_buckets)

            - bucket_w: Width of buckets on x-axis. Shape (n, ).
            - bucket_h: Height of buckets on y-axis. Shape (n, ).
            - l_buckets: Left buckets. Shape (n, ceil(side_num/2)).
            - r_buckets: Right buckets. Shape (n, ceil(side_num/2)).
            - t_buckets: Top buckets. Shape (n, ceil(side_num/2)).
            - d_buckets: Down buckets. Shape (n, ceil(side_num/2)).
    """
    proposals = bbox_rescale(proposals, scale_factor)

    # number of buckets in each side
    side_num = int(np.ceil(num_buckets / 2.0))
    pw = proposals[..., 2] - proposals[..., 0]
    ph = proposals[..., 3] - proposals[..., 1]
    px1 = proposals[..., 0]
    py1 = proposals[..., 1]
    px2 = proposals[..., 2]
    py2 = proposals[..., 3]

    bucket_w = pw / num_buckets
    bucket_h = ph / num_buckets

    # left buckets
    l_buckets = (
        px1[:, None] +
        (0.5 + torch.arange(0, side_num).to(proposals).float())[None, :] *
        bucket_w[:, None])
    # right buckets
    r_buckets = (
        px2[:, None] -
        (0.5 + torch.arange(0, side_num).to(proposals).float())[None, :] *
        bucket_w[:, None])
    # top buckets
    t_buckets = (
        py1[:, None] +
        (0.5 + torch.arange(0, side_num).to(proposals).float())[None, :] *
        bucket_h[:, None])
    # down buckets
    d_buckets = (
        py2[:, None] -
        (0.5 + torch.arange(0, side_num).to(proposals).float())[None, :] *
        bucket_h[:, None])
    return bucket_w, bucket_h, l_buckets, r_buckets, t_buckets, d_buckets


class Bbox(nn.Module):
    def __init__(self):
        super(Bbox, self).__init__()
        self.bbox_rescale = bbox_rescale
        self.generate_buckets = generate_buckets

    def forward(self, proposals):
        return self.generate_buckets(proposals)

torch_model = Bbox()

torch_model.eval()

proposals = args_adaptor(gen_np_args(64, 4))
torch_out = torch_model(proposals)

torch.onnx.export(torch_model, 
        (proposals),
        "generate_buckets.onnx",
        verbose=True,
        export_params=True,
        opset_version=12,
        input_names=['proposals'],
        output_names = ['output'])
