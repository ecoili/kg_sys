import torch
from backend import config
model = torch.load(config.MODEL_PATH)
print("加载成功！")