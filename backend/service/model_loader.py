import os

import torch
from .station_impact_prediction_multitask import load_model, load_and_preprocess_data
from backend import config


# 加载模型
def load_prediction_model(model_path, positions_file, relations_file, events_file, impact_file):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model, node_id_map, event_type_map = load_model(model_path, device)

    # 确保node_id_map的键是字符串类型
    node_id_map = {str(k): v for k, v in node_id_map.items()}

    graph_data, _, _, reverse_node_id_map, _, _, _, _ = load_and_preprocess_data(
        positions_file, relations_file, events_file, impact_file
    )
    # 确保reverse_node_id_map的值是字符串类型（与node_id_map的键类型一致）
    reverse_node_id_map = {k: str(v) for k, v in reverse_node_id_map.items()}
    return model, node_id_map, event_type_map, graph_data, reverse_node_id_map


# 在加载前检查文件是否存在
if not os.path.exists(config.MODEL_PATH):
    raise FileNotFoundError(f"模型文件不存在: {config.MODEL_PATH}")
# 全局变量保存模型和图数据
model, node_id_map, event_type_map, graph_data, reverse_node_id_map = load_prediction_model(
    config.MODEL_PATH,
    config.POSITIONS_FILE,
    config.RELATIONS_FILE,
    config.EVENTS_FILE,
    config.IMPACT_FILE
)