import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import RGCNConv, GATConv
from torch_geometric.data import Data
import math
import pandas as pd
from py2neo import Graph, Node, Relationship
from datetime import datetime
from backend.extensions import neo4j


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_seq_length=100):
        super(PositionalEncoding, self).__init__()
        position = torch.arange(max_seq_length).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_seq_length, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model % 2 != 0:
             pe[:, 1::2] = torch.cos(position * div_term[:-1])
        else:
             pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1), :]
        return x


class RGCN_GAT_Layer(nn.Module):
    def __init__(self, in_dim, hidden_dim, num_relations, num_bases, dropout=0.1):
        super(RGCN_GAT_Layer, self).__init__()
        self.rgcn = RGCNConv(in_channels=in_dim, out_channels=hidden_dim, num_relations=num_relations, num_bases=num_bases)
        self.gat = GATConv(in_channels=hidden_dim, out_channels=hidden_dim, heads=4, dropout=dropout, concat=False)
        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.skip_connection = nn.Identity()
        if in_dim != hidden_dim:
            self.skip_connection = nn.Linear(in_dim, hidden_dim)

    def forward(self, x, edge_index, edge_type):
        x_res = self.skip_connection(x)
        x = self.rgcn(x, edge_index, edge_type)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.gat(x, edge_index)
        x = x + x_res
        x = self.norm(x)
        return x


class TransformerModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, nhead, num_layers, dropout=0.1):
        super(TransformerModel, self).__init__()
        self.pos_encoder = PositionalEncoding(input_dim)
        encoder_layers = nn.TransformerEncoderLayer(
            d_model=input_dim, nhead=nhead, dim_feedforward=hidden_dim,
            dropout=dropout, batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.input_dim = input_dim

    def forward(self, src, src_mask=None):
        if src.size(-1) != self.input_dim:
             raise ValueError(f"Transformer input dim mismatch: got {src.size(-1)}, expected {self.input_dim}")
        src = self.pos_encoder(src)
        output = self.transformer_encoder(src, src_mask)
        return output


class RGCN_GAT_Transformer(nn.Module):
    def __init__(self, node_feat_dim, hidden_dim, context_dim, embed_dim_event_type, num_event_types,
                 num_relations, num_bases, transformer_nhead, transformer_layers, num_nodes, dropout=0.1):
        super(RGCN_GAT_Transformer, self).__init__()

        self.hidden_dim = hidden_dim
        self.context_dim = context_dim
        self.num_nodes = num_nodes
        self.transformer_input_dim = hidden_dim + context_dim

        self.node_embedding = nn.Linear(node_feat_dim, hidden_dim)
        self.rgcn_gat1 = RGCN_GAT_Layer(hidden_dim, hidden_dim, num_relations, num_bases, dropout)
        self.rgcn_gat2 = RGCN_GAT_Layer(hidden_dim, hidden_dim, num_relations, num_bases, dropout)

        self.event_type_embedding = nn.Embedding(num_event_types, embed_dim_event_type)
        self.event_context_proj = nn.Sequential(
            nn.Linear(embed_dim_event_type + 2, context_dim),
            nn.ReLU(),
            nn.LayerNorm(context_dim)
        )

        self.transformer = TransformerModel(
            input_dim=self.transformer_input_dim,
            hidden_dim=hidden_dim * 4,
            nhead=transformer_nhead,
            num_layers=transformer_layers,
            dropout=dropout
        )

        # <<< CHANGE >>> Modify output layer for multi-task (classification logit + time regression)
        self.output_layer = nn.Sequential(
            nn.Linear(self.transformer_input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 2) # Output 2 values: [logit_classification, predicted_time]
        )

    def forward(self, node_feats, edge_index, edge_type, source_nodes,
                event_types, severities, durations,
                time_diffs=None): # time_diffs input still optional, not used in forward directly
        batch_size = source_nodes.size(0)
        device = node_feats.device

        # 1. Node features through GNNs
        x = self.node_embedding(node_feats)
        x = self.rgcn_gat1(x, edge_index, edge_type)
        x = self.rgcn_gat2(x, edge_index, edge_type)

        # 2. Create Event Context
        type_embeds = self.event_type_embedding(event_types)
        sev_unsqueezed = severities.unsqueeze(1).float()
        dur_unsqueezed = durations.unsqueeze(1).float()
        raw_context = torch.cat([type_embeds, sev_unsqueezed, dur_unsqueezed], dim=1)
        event_contexts = self.event_context_proj(raw_context)

        # 3. Prepare sequences for Transformer
        sequences = []
        target_node_masks = []

        for i in range(batch_size):
            source_id = source_nodes[i].item()
            target_ids = [j for j in range(self.num_nodes) if j != source_id]
            target_node_masks.append(target_ids)
            num_targets = len(target_ids)

            source_feat_gnn = x[source_id]
            target_feats_gnn = x[target_ids]
            event_context_i = event_contexts[i]

            source_feat_combined = torch.cat([source_feat_gnn, event_context_i])
            padding = torch.zeros(num_targets, self.context_dim, device=device)
            target_feats_padded = torch.cat([target_feats_gnn, padding], dim=1)

            seq = torch.cat([source_feat_combined.unsqueeze(0), target_feats_padded], dim=0)
            sequences.append(seq)

        try:
            node_sequences = torch.stack(sequences)
        except RuntimeError as e:
             print(f"Error stacking sequences: {e}. Check sequence lengths.")
             raise e

        # 4. Pass through Transformer
        transformer_out = self.transformer(node_sequences)

        # 5. Extract target node outputs
        target_out = transformer_out[:, 1:, :] # Shape: [batch_size, num_targets, transformer_input_dim]

        # 6. Final Prediction Layer
        # <<< CHANGE >>> Output now has shape [batch_size, num_targets, 2]
        predictions = self.output_layer(target_out)

        return predictions, target_node_masks


class PredictionService:
    def __init__(self, model_path, positions_file, relations_file):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model(model_path)
        self.graph_data, self.node_id_map, self.reverse_node_id_map, self.event_type_map = self._prepare_graph_data(
            positions_file, relations_file)

    def _load_model(self, model_path):
        checkpoint = torch.load(model_path, map_location=self.device)
        model = ...  # 模型初始化代码(同文档2)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        return model

    def _prepare_graph_data(self, positions_file, relations_file):
        # 加载并预处理图数据(同文档2中的load_and_preprocess_data函数)
        positions_df = pd.read_csv(positions_file)
        relations_df = pd.read_csv(relations_file)

        # 节点特征处理
        node_features = ...  # 特征标准化处理

        # 边处理
        edge_index = ...
        edge_type = ...

        graph_data = Data(
            x=torch.tensor(node_features, dtype=torch.float),
            edge_index=edge_index,
            edge_type=edge_type,
            num_nodes=len(node_id_map)
        )

        return graph_data, node_id_map, reverse_node_id_map, event_type_map

    def predict_impact(self, source_position_id, event_type, severity, duration):
        # 调用预测函数(同文档2中的predict_single_position)
        predictions = ...  # 预测结果

        # 将预测结果保存到知识图谱
        self._save_to_neo4j(source_position_id, event_type, predictions)

        return predictions

    def _save_to_neo4j(self, source_position_id, event_type, predictions):
        # 连接到Neo4j
        from py2neo import Graph
        graph = Graph()

        # 创建事件节点
        event_node = Node("Event",
                          event_id=f"EVENT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                          type=event_type,
                          severity=severity,
                          timestamp=datetime.now().isoformat())
        graph.create(event_node)

        # 连接到源阵位
        source_node = graph.nodes.match("Position", id=source_position_id).first()
        if source_node:
            rel = Relationship(source_node, "HAS_EVENT", event_node)
            graph.create(rel)

        # 添加预测结果
        for pred in predictions:
            if pred['is_affected'] == 1:
                target_node = graph.nodes.match("Position", id=pred['position_id']).first()
                if target_node:
                    impact_rel = Relationship(event_node, "PREDICTED_IMPACT", target_node,
                                              probability=pred['impact_probability'],
                                              time_minutes=pred['predicted_impact_time_minutes'])
                    graph.create(impact_rel)