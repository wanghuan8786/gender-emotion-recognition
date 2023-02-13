# part of the code was referenced from SUPERB: https://github.com/s3prl/s3prl
import pdb
import torch
import itertools
import s3prl.hub as hub

from torch import nn
from collections import OrderedDict
from typing import Optional, Callable
from torch.nn import functional as F
from torch.nn.functional import normalize
from transformers import Wav2Vec2Model, Wav2Vec2Config, Wav2Vec2Processor, AutoProcessor

    
class Wav2Vec(nn.Module):
    def __init__(self):
        super(Wav2Vec, self).__init__()
        
        # First we take the pretrained xlsr model
        self.backbone_model = Wav2Vec2Model.from_pretrained(
            "facebook/wav2vec2-base-960h",
            output_hidden_states=True
        )

        # setting require grad = true only if we want to fine tune the pretrained model
        for name, param in self.backbone_model.named_parameters(): param.requires_grad = False
        
    def forward(self, x, norm="nonorm", length=None):
        with torch.no_grad():
            feat = self.backbone_model(x).hidden_states
        # stacked feature
        stacked_feature = torch.stack(feat, dim=0)
        # get length and feature
        if length is not None:
            length = self.get_feat_extract_output_lengths(length.detach().cpu())
            mask = prepare_mask(length, feat[0].shape[:2], x.dtype)
            length, mask = length.cuda(), mask.cuda()
            return stacked_feature, length, mask
        return stacked_feature
    
    # From huggingface
    def get_feat_extract_output_lengths(self, input_length):
        """
        Computes the output length of the convolutional layers
        """
        def _conv_out_length(input_length, kernel_size, stride):
            # 1D convolutional layer output length formula taken
            # from https://pytorch.org/docs/stable/generated/torch.nn.Conv1d.html
            return (input_length - kernel_size) // stride + 1
        for kernel_size, stride in zip(self.backbone_model.config.conv_kernel, self.backbone_model.config.conv_stride):
            input_length = _conv_out_length(input_length, kernel_size, stride)
        return input_length

class APC(nn.Module):
    def __init__(self):
        super(APC, self).__init__()
        
        # First we take the apc model
        self.backbone_model = getattr(hub, "apc")()
        # setting require grad = true only if we want to fine tune the pretrained model
        for name, param in self.backbone_model.named_parameters(): param.requires_grad = False
        
    def forward(self, x, norm="nonorm", length=None):
        new_x = list()
        if length is not None:
             for idx in range(len(length)):
                new_x.append(x[idx][:length[idx]])
        with torch.no_grad():
            if length is not None: feat = self.backbone_model(new_x)['hidden_states']
            else: feat = self.backbone_model(x)['hidden_states']
        # stacked feature
        stacked_feature = torch.stack(feat, dim=0)[-1]
        # get length and feature
        if length is not None:
            length = self.get_feat_extract_output_lengths(length.detach().cpu())
            mask = prepare_mask(length, feat[0].shape[:2], x.dtype)
            length, mask = length.cuda(), mask.cuda()
            return stacked_feature, length, mask
        return stacked_feature
    
    # From huggingface
    def get_feat_extract_output_lengths(self, input_length):
        """
        Computes the output length
        """
        def _out_length(input_length, window, stride):
            return (input_length - window) // stride + 1
        input_length = _out_length(input_length, 400, 160)
        return input_length


def prepare_mask(length, shape, dtype):
    # Modified from huggingface
    mask = torch.zeros(
        shape, dtype=dtype
    )
    # these two operations makes sure that all values
    # before the output lengths indices are attended to
    mask[(torch.arange(mask.shape[0]), length.cpu() - 1)] = 1
    mask = mask.flip([-1]).cumsum(-1).flip([-1]).bool()
    return mask
    