import torch
print("Torch module:", torch)
print("Torch optim scheduler:", torch.optim.lr_scheduler)
print("Has ReduceLROnPlateau?", hasattr(torch.optim.lr_scheduler, "ReduceLROnPlateau"))
