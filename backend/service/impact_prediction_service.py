# backend/service/impact_prediction_service.py
from backend.service.base_prediction_service import BasePredictionService
import torch


class ImpactPredictionService(BasePredictionService):
    def predict_impact(self, source_position_id, event_type, severity, duration):
        """预测单个事件的影响"""
        try:
            source_position_id = str(source_position_id)

            if source_position_id not in self.node_id_map:
                raise ValueError(f"Invalid source_position_id: {source_position_id}")
            if event_type not in self.event_type_map:
                raise ValueError(f"Invalid event_type: {event_type}")

            # 准备输入数据
            source_node_idx = self.node_id_map[source_position_id]
            event_type_idx = self.event_type_map[event_type]

            source_nodes_tensor = torch.tensor([[source_node_idx]], device=self.device)
            event_types_tensor = torch.tensor([[event_type_idx]], device=self.device)
            severity_tensor = torch.tensor([[severity]], device=self.device).float()
            duration_tensor = torch.tensor([[duration]], device=self.device).float()

            # 调用模型预测
            with torch.no_grad():
                outputs, _ = self.model(
                    self.graph_data.x.to(self.device),
                    self.graph_data.edge_index.to(self.device),
                    self.graph_data.edge_type.to(self.device),
                    source_nodes_tensor,
                    event_types_tensor,
                    severity_tensor,
                    duration_tensor
                )

            # 处理预测结果
            return self._process_prediction_results(outputs)

        except Exception as e:
            self._handle_prediction_error(e)

    def predict_multitask_impact(self, source_position_ids, event_types, severities, durations):
        """批量预测多个事件的影响"""
        try:
            if len(source_position_ids) != len(event_types) != len(severities) != len(durations):
                raise ValueError("所有输入列表的长度必须一致")

            batch_size = len(source_position_ids)
            source_node_indices = []
            event_type_indices = []

            for i in range(batch_size):
                pos_id = str(source_position_ids[i])
                if pos_id not in self.node_id_map:
                    raise ValueError(f"无效的阵位ID: {pos_id}")

                event_type = event_types[i]
                if event_type not in self.event_type_map:
                    raise ValueError(f"无效的事件类型: {event_type}")

                source_node_indices.append(self.node_id_map[pos_id])
                event_type_indices.append(self.event_type_map[event_type])

            # 转换为2D张量，形状为 [batch_size, 1]
            source_node_indices = torch.tensor(source_node_indices, device=self.device).view(-1, 1)
            event_type_indices = torch.tensor(event_type_indices, device=self.device).view(-1, 1)
            severity_tensor = torch.tensor(severities, device=self.device).float().view(-1, 1)
            duration_tensor = torch.tensor(durations, device=self.device).float().view(-1, 1)

            # 批量预测
            with torch.no_grad():
                outputs = self.model(
                    self.graph_data.x.to(self.device),
                    self.graph_data.edge_index.to(self.device),
                    self.graph_data.edge_type.to(self.device),
                    source_node_indices,
                    event_type_indices,
                    severity_tensor,
                    duration_tensor
                )

            # 确保模型输出形状正确 [batch_size, num_nodes, 2]
            if isinstance(outputs, tuple):
                outputs = outputs[0]  # 如果模型返回的是元组，取第一个元素
            outputs = outputs.unsqueeze(0) if outputs.dim() == 2 else outputs

            # 处理批量预测结果
            return self._process_batch_prediction_results(
                outputs, source_position_ids, event_types
            )

        except Exception as e:
            self._handle_prediction_error(e)

    def _process_prediction_results(self, outputs):
        """处理单个预测结果"""
        impact_logits = outputs[0, :, 0]
        impact_times = outputs[0, :, 1]
        impact_probs = torch.sigmoid(impact_logits)

        predictions = []
        for node_idx in range(len(impact_probs)):
            position_id = str(self.reverse_node_id_map[node_idx])
            predictions.append({
                "position_id": position_id,
                "impact_probability": impact_probs[node_idx].item(),
                "is_affected": 1 if impact_probs[node_idx] > 0.5 else 0,
                "predicted_impact_time_minutes": max(0, impact_times[node_idx].item())
            })
        return predictions

    def _process_batch_prediction_results(self, outputs, source_ids, event_types):
        """处理批量预测结果"""
        # outputs形状应为 [batch_size, num_nodes, 2]
        impact_probs = torch.sigmoid(outputs[:, :, 0])  # 第一列是影响概率logits
        impact_times = outputs[:, :, 1]  # 第二列是影响时间

        all_predictions = []
        for batch_idx in range(len(source_ids)):
            predictions = []
            for node_idx in range(impact_probs.size(1)):
                position_id = str(self.reverse_node_id_map[node_idx])
                predictions.append({
                    "position_id": position_id,
                    "impact_probability": impact_probs[batch_idx, node_idx].item(),
                    "is_affected": 1 if impact_probs[batch_idx, node_idx] > 0.5 else 0,
                    "predicted_impact_time_minutes": max(0, impact_times[batch_idx, node_idx].item()),
                    "source_position_id": source_ids[batch_idx],
                    "event_type": event_types[batch_idx]
                })
            all_predictions.append(predictions)
        return all_predictions

    def _handle_prediction_error(self, error):
        """统一处理预测错误"""
        print(f"预测失败: {str(error)}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"预测过程中发生错误: {str(error)}") from error