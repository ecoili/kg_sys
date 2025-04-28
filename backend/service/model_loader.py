import torch
from .station_impact_prediction_multitask import load_model, load_and_preprocess_data


# 加载模型
def load_prediction_model(model_path, positions_file, relations_file, events_file, impact_file):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model, node_id_map, event_type_map = load_model(model_path, device)
    graph_data, _, _, reverse_node_id_map, _, _, _, _ = load_and_preprocess_data(
        positions_file, relations_file, events_file, impact_file
    )
    return model, node_id_map, event_type_map, graph_data, reverse_node_id_map

# 全局变量保存模型和图数据
model, node_id_map, event_type_map, graph_data, reverse_node_id_map = load_prediction_model(
    "E:/py_prjs/flask3/backend/models/pths/rgcn_gat_transformer_multitask.pth",
    "E:/py_prjs/flask3/backend/models/data/positions.csv",
    "E:/py_prjs/flask3/backend/models/data/relations.csv",
    "E:/py_prjs/flask3/backend/models/data/synthetic_events.csv",
    "E:/py_prjs/flask3/backend/models/data/synthetic_impact.csv"
)