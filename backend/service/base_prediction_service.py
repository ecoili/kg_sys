# backend/service/base_prediction_service.py
import torch
from backend.service.model_loader import load_prediction_model


class BasePredictionService:
    def __init__(self, model_path=None, positions_file=None, relations_file=None,
                 events_file=None, impact_file=None):
        from backend import config
        self.model_path = model_path or config.MODEL_PATH
        self.positions_file = positions_file or config.POSITIONS_FILE
        self.relations_file = relations_file or config.RELATIONS_FILE
        self.events_file = events_file or config.EVENTS_FILE
        self.impact_file = impact_file or config.IMPACT_FILE

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 加载模型和数据
        self.model, self.node_id_map, self.event_type_map, \
            self.graph_data, self.reverse_node_id_map = load_prediction_model(
            self.model_path,
            self.positions_file,
            self.relations_file,
            self.events_file,
            self.impact_file
        )

        self.model.to(self.device)
        self.model.eval()