#!/usr/bin/env python3
import os
import torch
import torch.distributed as dist

dist.init_process_group("nccl")
rank = dist.get_rank()
device = torch.device(f"cuda:{rank}")
tensor = torch.tensor([float(rank + 1)], device=device)
dist.all_reduce(tensor)
if rank == 0:
    print(f"NCCL all-reduce result={tensor.item():.1f}; visible GPUs={torch.cuda.device_count()}")
dist.destroy_process_group()
