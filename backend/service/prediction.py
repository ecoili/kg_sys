# services/prediction_service.py
import torch
import os
from flask import app


class PredictionService:
    def __init__(self, app=None):
        self.model = None
        self.graph_data = None
        self.node_id_map = None
        self.event_type_map = None
        self.reverse_node_id_map = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """初始化模型和数据结构"""
        model_path = os.path.join(app.config['MODEL_DIR'], 'rgcn_gat_transformer_multitask.pth')

        # 加载模型和数据
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        checkpoint = torch.load(model_path, map_location=device)

        # 初始化模型
        self.model = RGCN_GAT_Transformer(
            node_feat_dim=checkpoint['node_feat_dim'],
            hidden_dim=checkpoint['config']['hidden_dim'],
            context_dim=checkpoint['config']['context_dim'],
            embed_dim_event_type=checkpoint['config']['embed_dim_event_type'],
            num_event_types=checkpoint['num_event_types'],
            num_relations=checkpoint['num_relations'],
            num_bases=checkpoint['config'].get('num_bases', 8),
            transformer_nhead=checkpoint['config']['transformer_nhead'],
            transformer_layers=checkpoint['config']['transformer_layers'],
            num_nodes=len(checkpoint['node_id_map']),
            dropout=checkpoint['config'].get('dropout', 0.1)
        ).to(device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

        # 加载图数据
        self.graph_data, _, self.node_id_map, self.reverse_node_id_map, self.event_type_map, _, _, _ = load_and_preprocess_data(
            app.config['POSITIONS_FILE'],
            app.config['RELATIONS_FILE'],
            app.config['EVENTS_FILE'],
            app.config['IMPACT_FILE']
        )
        self.graph_data = self.graph_data.to(device)

    def predict(self, position_id, event_type, severity, duration, threshold=0.5):
        """执行预测"""
        if self.model is None:
            raise RuntimeError("Prediction model not initialized")

        return self._predict_single_position(
            position_id, event_type, severity, duration, threshold
        )

    def _predict_single_position(self, position_id, event_type_str, severity, duration, threshold):
        """内部预测方法"""
        device = next(self.model.parameters()).device

        if position_id not in self.node_id_map:
            raise ValueError(f"源阵位ID {position_id} 不存在")

        if event_type_str not in self.event_type_map:
            raise ValueError(f"事件类型 '{event_type_str}' 未知")

        source_node = self.node_id_map[position_id]
        event_type_encoded = self.event_type_map[event_type_str]

        with torch.no_grad():
            outputs, target_node_masks = self.model(
                self.graph_data.x,
                self.graph_data.edge_index,
                self.graph_data.edge_type,
                torch.tensor([source_node], dtype=torch.long, device=device),
                torch.tensor([event_type_encoded], dtype=torch.long, device=device),
                torch.tensor([severity], dtype=torch.float, device=device),
                torch.tensor([duration], dtype=torch.float, device=device)
            )

        logits_cls = outputs[:, :, 0].squeeze(0)
        preds_time = outputs[:, :, 1].squeeze(0)

        probabilities = torch.sigmoid(logits_cls).cpu().numpy()
        predicted_times = preds_time.cpu().numpy()

        predictions = []
        for i, node_idx in enumerate(target_node_masks[0]):
            if node_idx in self.reverse_node_id_map:
                real_node_id = self.reverse_node_id_map[node_idx]
                prob = float(probabilities[i])
                pred_time = max(0.0, float(predicted_times[i]))

                predictions.append({
                    'position_id': real_node_id,
                    'impact_probability': prob,
                    'is_affected': 1 if prob >= threshold else 0,
                    'predicted_impact_time_minutes': pred_time
                })

        return sorted(predictions, key=lambda x: x['impact_probability'], reverse=True)