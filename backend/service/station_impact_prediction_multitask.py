# -*- coding: utf-8 -*-
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import os
import csv
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, mean_absolute_error # <<< CHANGE >>> Added MAE
from torch_geometric.nn import RGCNConv, GATConv
from torch_geometric.data import Data
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
import platform
import matplotlib
# --- 添加这个代码块来解决中文显示问题 ---
try:
    # 根据操作系统选择合适的字体
    system = platform.system()
    font_name = None
    if system == 'Windows':
        # 尝试常见的 Windows 中文字体
        # 你可以根据自己系统安装的字体修改，如 'Microsoft YaHei', 'SimSun' 等
        font_options = ['SimHei', 'Microsoft YaHei', 'DengXian']
    elif system == 'Darwin': # macOS
        # 尝试常见的 macOS 中文字体
        font_options = ['PingFang SC', 'STHeiti', 'Heiti TC', 'Songti SC']
    else: # Linux and others
        # 尝试常见的 Linux 中文字体 (可能需要用户手动安装)
        # 例如: sudo apt-get update && sudo apt-get install fonts-wqy-microhei
        font_options = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Source Han Sans SC', 'DejaVu Sans Fallback'] # 添加一个备选

    # 找到系统中第一个可用的字体
    available_fonts = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    available_font_names = [matplotlib.font_manager.FontProperties(fname=fname).get_name() for fname in available_fonts]

    for font in font_options:
        if font in available_font_names:
            font_name = font
            break
        # 尝试模糊匹配 (例如 'Noto Sans CJK SC Regular' 匹配 'Noto Sans CJK SC')
        for available in available_font_names:
             if font in available:
                  font_name = font # 使用选项中的名字，让 rcParams 查找
                  break
        if font_name: break


    if font_name:
        print(f"找到并设置 Matplotlib 字体为: {font_name}")
        plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif'] # 将找到的字体放在列表前面
    else:
        print(f"警告: 未能在系统中找到推荐的中文字体 {font_options}。中文可能无法正常显示。")
        print("请尝试安装 'SimHei'(Win), 'PingFang SC'(Mac), 或 'WenQuanYi Micro Hei'(Linux) 等字体。")

    # 解决更改字体后 负号'-' 显示为方块的问题
    plt.rcParams['axes.unicode_minus'] = False

except Exception as e:
    print(f"设置 Matplotlib 中文字体时出错: {e}")
    print("绘图中的中文可能无法正常显示。")


# ===================== 用户配置区域 (可根据需要修改) =====================

# 运行模式: "train" - 训练模型, "predict" - 单阵位预测, "batch" - 批量预测
# RUN_MODE = "train"
RUN_MODE = "predict"
# 预测/批量预测参数 (仅在对应模式下生效)
PREDICT_POSITION_ID = 25244
PREDICT_EVENT_TYPE = "guzhang_102"
PREDICT_SEVERITY = 0.80
PREDICT_DURATION = 45
# PREDICT_TIME_DIFF = 0.0 # No longer needed as input for prediction

BATCH_EVENT_TYPE = "hardware_failure"
BATCH_SEVERITY = 0.8
BATCH_DURATION = 60
# BATCH_TIME_DIFF = 0.0 # No longer needed as input for prediction

# 模型训练参数
EPOCHS = 100
BATCH_SIZE = 32
LEARNING_RATE =  8e-5# Start with the best LR from previous experiments
HIDDEN_DIM = 192    # Start with the best hidden dim
CONTEXT_DIM = 64
EMBED_DIM_EVENT_TYPE = 32
DROPOUT = 0.25      # Start with the best dropout
EARLY_STOPPING_PATIENCE = 10

# <<< CHANGE >>> Multi-task Learning Configuration
CLASSIFICATION_LOSS_WEIGHT = 1.0 # Weight for the classification task (impact probability)
REGRESSION_LOSS_WEIGHT = 0.5     # Weight for the regression task (impact time), adjust as needed
REGRESSION_LOSS_TYPE = 'l1'      # 'mse' or 'l1' (Mean Squared Error or Mean Absolute Error)

# 预测阈值 (for classification)
THRESHOLD = 0.5

# 文件路径 (确保指向正确的数据文件)
DATA_DIR = "D:\\DC20250407\\DC_entire_scheduling\\d_contingencyPlan\\20250422\\data"
POSITIONS_FILE = os.path.join(DATA_DIR, "positions.csv")
RELATIONS_FILE = os.path.join(DATA_DIR, "relations.csv")
EVENTS_FILE = os.path.join(DATA_DIR, "synthetic_events.csv") # Use the no-noise data if available
IMPACT_FILE = os.path.join(DATA_DIR, "synthetic_impact.csv") # Use the no-noise data if available
MODEL_DIR = os.path.join(DATA_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "rgcn_gat_transformer_multitask.pth") # New model name
BEST_MODEL_TEMP_PATH = os.path.join(MODEL_DIR, "temp_best_multitask_model.pth")
PLOTS_DIR = os.path.join(DATA_DIR, "plots")
RESULTS_DIR = os.path.join(DATA_DIR, "results")

# ===================== 模型定义 (修改输出层) =====================
# PositionalEncoding, TimeEncoding, RGCN_GAT_Layer, TransformerModel (no changes needed here)
# ... (省略与之前版本相同的模型定义代码) ...
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

class TimeEncoding(nn.Module): # Currently unused in forward, kept for potential future use
    def __init__(self, time_dim):
        super(TimeEncoding, self).__init__()
        self.time_dim = time_dim

    def forward(self, time_diff):
        time_diff = time_diff.unsqueeze(1)
        device = time_diff.device
        half_dim = self.time_dim // 2
        freq = torch.exp(
            torch.arange(0, half_dim, dtype=torch.float) * (-math.log(10000.0) / half_dim)
        ).to(device)
        enc = torch.zeros(time_diff.size(0), self.time_dim).to(device)
        enc[:, 0:half_dim] = torch.sin(time_diff * freq)
        enc[:, half_dim:2*half_dim] = torch.cos(time_diff * freq)
        return enc

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
        # 检查输入形状
        assert source_nodes.dim() == 2, f"source_nodes should be 2D, got {source_nodes.dim()}"
        assert event_types.dim() == 2, f"event_types should be 2D, got {event_types.dim()}"
        assert severities.dim() == 2, f"severities should be 2D, got {severities.dim()}"
        assert durations.dim() == 2, f"durations should be 2D, got {durations.dim()}"

        batch_size = source_nodes.size(0)
        device = node_feats.device

        # 1. Node features through GNNs
        x = self.node_embedding(node_feats)
        x = self.rgcn_gat1(x, edge_index, edge_type)
        x = self.rgcn_gat2(x, edge_index, edge_type)

        # 2. Create Event Context
        # type_embeds = self.event_type_embedding(event_types)
        # sev_unsqueezed = severities.unsqueeze(1).float()
        # dur_unsqueezed = durations.unsqueeze(1).float()
        # raw_context = torch.cat([type_embeds, sev_unsqueezed, dur_unsqueezed], dim=1)
        # event_contexts = self.event_context_proj(raw_context)

        # 修改后
        type_embeds = self.event_type_embedding(event_types.squeeze(1))  # shape: [batch_size, embed_dim]
        sev_unsqueezed = severities.float()  # shape: [batch_size, 1]
        dur_unsqueezed = durations.float()  # shape: [batch_size, 1]

        # 确保维度匹配
        raw_context = torch.cat([
            type_embeds,
            sev_unsqueezed,
            dur_unsqueezed
        ], dim=1)

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

# ===================== 数据处理与批次准备 (修改 prepare_batch) =====================
# load_and_preprocess_data (No significant changes needed, assuming time_diffs are calculated correctly)
# ... (省略与之前版本相同的 load_and_preprocess_data 代码) ...
def load_and_preprocess_data(positions_file, relations_file, events_file, impact_file):
    """加载并预处理数据 (确保 time_diffs 被正确处理)"""
    print(f"正在加载文件:\n  {positions_file}\n  {relations_file}\n  {events_file}\n  {impact_file}")
    positions_df = pd.read_csv(positions_file)
    relations_df = pd.read_csv(relations_file)
    events_df = pd.read_csv(events_file)
    impact_df = pd.read_csv(impact_file)
    print("文件加载完成.")

    node_ids = sorted(positions_df['position_id'].unique())
    node_id_map = {old_id: new_id for new_id, old_id in enumerate(node_ids)}
    num_nodes = len(node_ids)
    reverse_node_id_map = {v: k for k, v in node_id_map.items()}
    print(f"找到 {num_nodes} 个唯一节点ID.")

    # Node Features (same as before)
    node_features_df = positions_df[['position_id', 'x_coord', 'y_coord', 'position_type',
                                     'importance_level', 'failure_rate']].copy()
    if pd.api.types.is_string_dtype(node_features_df['position_type']):
        type_encoder = LabelEncoder()
        node_features_df['position_type_encoded'] = type_encoder.fit_transform(node_features_df['position_type'])
        print(f"节点类型已编码: {dict(zip(type_encoder.classes_, type_encoder.transform(type_encoder.classes_)))}")
        feature_cols = ['x_coord', 'y_coord', 'position_type_encoded', 'importance_level', 'failure_rate']
    else:
        feature_cols = ['x_coord', 'y_coord', 'position_type', 'importance_level', 'failure_rate']
    node_features_df['node_idx'] = node_features_df['position_id'].map(node_id_map)
    node_features_df = node_features_df.sort_values('node_idx').set_index('node_idx')
    numerical_features = node_features_df[feature_cols].values.astype(float)
    if np.isnan(numerical_features).any():
        print("警告: 节点特征中存在 NaN 值，将用 0 填充。")
        numerical_features = np.nan_to_num(numerical_features)
    scaler = StandardScaler()
    node_features_scaled = scaler.fit_transform(numerical_features)
    node_feat_dim = node_features_scaled.shape[1]
    print(f"节点特征维度: {node_feat_dim}")

    # Edge Features (same as before)
    edge_index = []
    edge_type = []
    relation_type_map = {'connection': 0, 'influence': 1}
    num_relations = len(relation_type_map)
    skipped_relations = 0
    for _, row in relations_df.iterrows():
        if row['source_id'] in node_id_map and row['target_id'] in node_id_map:
            src = node_id_map[row['source_id']]
            dst = node_id_map[row['target_id']]
            rel_type = relation_type_map.get(row['relation_type'], 0)
            edge_index.append([src, dst])
            edge_type.append(rel_type)
        else: skipped_relations += 1
    if skipped_relations > 0: print(f"警告: 跳过了 {skipped_relations} 条关系，因为源或目标ID未知。")
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_type = torch.tensor(edge_type, dtype=torch.long)
    print(f"图结构创建: {edge_index.size(1)} 条边, {num_relations} 种关系类型.")

    graph_data = Data(
        x=torch.tensor(node_features_scaled, dtype=torch.float),
        edge_index=edge_index,
        edge_type=edge_type,
        num_nodes=num_nodes
    )

    # Event and Impact Data
    event_type_encoder = LabelEncoder()
    events_df['event_type'] = events_df['event_type'].astype(str)
    events_df['event_type_encoded'] = event_type_encoder.fit_transform(events_df['event_type'])
    num_event_types = len(event_type_encoder.classes_)
    event_type_map = {name: code for code, name in enumerate(event_type_encoder.classes_)}
    print(f"事件类型已编码 ({num_event_types} 种): {event_type_map}")

    training_data_raw = []
    impact_groups = impact_df.groupby('event_id')
    processed_events = 0
    skipped_events = 0

    for _, event in events_df.iterrows():
        event_id = event['event_id']
        source_position = event['position_id']
        if source_position not in node_id_map: skipped_events += 1; continue
        source_node = node_id_map[source_position]
        event_type_encoded = event['event_type_encoded']
        severity = event['severity']
        duration = event['duration_minutes']

        try: start_time = datetime.strptime(str(event['start_time']), '%Y-%m-%dT%H:%M:%S')
        except (ValueError, TypeError): start_time = None

        try: event_impacts = impact_groups.get_group(event_id)
        except KeyError: event_impacts = pd.DataFrame()

        labels = {}
        time_diffs = {} # Store actual time differences for affected nodes
        for target_node_idx in range(num_nodes): # Initialize for all potential targets
             if target_node_idx != source_node:
                 labels[target_node_idx] = 0.0
                 time_diffs[target_node_idx] = 0.0 # Default time diff is 0 for unaffected

        for _, impact in event_impacts.iterrows():
             target_position = impact['target_position']
             if target_position in node_id_map:
                 target_node = node_id_map[target_position]
                 if target_node != source_node:
                     is_affected = float(impact['was_affected'])
                     labels[target_node] = is_affected
                     if is_affected == 1:
                         if start_time and pd.notna(impact['impact_start_time']):
                             try:
                                 impact_time = datetime.strptime(str(impact['impact_start_time']), '%Y-%m-%dT%H:%M:%S')
                                 diff_minutes = max(0.0, (impact_time - start_time).total_seconds() / 60.0)
                                 time_diffs[target_node] = diff_minutes
                             except (ValueError, TypeError):
                                 time_diffs[target_node] = 0.0 # Use 0 if time parsing fails for affected node
                         else:
                             time_diffs[target_node] = 0.0 # Use 0 if start_time missing or impact_time missing for affected node

        if len(labels) != num_nodes - 1: print(f"警告: 事件 {event_id} 的标签数量 ({len(labels)}) 与预期目标数量 ({num_nodes - 1}) 不符。")

        sample = {
            'event_id': event_id, 'source_node': source_node,
            'event_type_encoded': event_type_encoded, 'severity': severity, 'duration': duration,
            'labels': labels, 'time_diffs': time_diffs # Pass the dict containing time diffs for all targets
        }
        training_data_raw.append(sample)
        processed_events += 1

    if skipped_events > 0: print(f"警告: 跳过了 {skipped_events} 个事件，因为它们的源ID无效。")
    print(f"总共处理了 {processed_events} 个事件，生成了 {len(training_data_raw)} 个训练样本。")

    return graph_data, training_data_raw, node_id_map, reverse_node_id_map, event_type_map, node_feat_dim, num_relations, num_event_types


def prepare_batch(batch_samples, num_nodes):
    """准备批次数据 (修改版: 添加 true_times_tensor)"""
    if not batch_samples: return None

    source_nodes_list = [item['source_node'] for item in batch_samples]
    event_types_list = [item['event_type_encoded'] for item in batch_samples]
    severities_list = [item['severity'] for item in batch_samples]
    durations_list = [item['duration'] for item in batch_samples]
    labels_batch_list = []
    time_diffs_batch_list = [] # <<< CHANGE >>> List to store time difference vectors

    for item in batch_samples:
        source_node = item['source_node']
        labels_dict = item['labels']
        time_diffs_dict = item['time_diffs'] # <<< CHANGE >>> Get the time diffs dict
        label_vector = []
        time_vector = [] # <<< CHANGE >>> Vector for time differences
        valid_target_indices = [] # Should match the order of label_vector and time_vector

        for target_idx in range(num_nodes):
            if target_idx != source_node:
                label_vector.append(labels_dict.get(target_idx, 0.0))
                time_vector.append(time_diffs_dict.get(target_idx, 0.0)) # <<< CHANGE >>> Get time diff, default 0
                valid_target_indices.append(target_idx)

        labels_batch_list.append(torch.tensor(label_vector, dtype=torch.float))
        time_diffs_batch_list.append(torch.tensor(time_vector, dtype=torch.float)) # <<< CHANGE >>> Append time vector

    source_nodes_tensor = torch.tensor(source_nodes_list, dtype=torch.long)
    event_types_tensor = torch.tensor(event_types_list, dtype=torch.long)
    severities_tensor = torch.tensor(severities_list, dtype=torch.float)
    durations_tensor = torch.tensor(durations_list, dtype=torch.float)
    labels_tensor = torch.stack(labels_batch_list)
    true_times_tensor = torch.stack(time_diffs_batch_list) # <<< CHANGE >>> Stack time vectors

    # Remove avg_time_diffs as it's now directly handled by true_times_tensor
    return {
        'source_nodes': source_nodes_tensor, 'event_types': event_types_tensor,
        'severities': severities_tensor, 'durations': durations_tensor,
        'labels': labels_tensor,
        'true_times': true_times_tensor # <<< CHANGE >>> Return true times tensor
    }

# ===================== 训练函数 (修改损失计算和评估) =====================

def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

def train_model(graph_data, all_training_samples, node_id_map, event_type_map, node_feat_dim, num_relations, num_event_types):
    """训练模型 (多任务: 分类 + 回归)"""

    set_seed(42)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    graph_data = graph_data.to(device)

    config = {
        'hidden_dim': HIDDEN_DIM, 'context_dim': CONTEXT_DIM,
        'embed_dim_event_type': EMBED_DIM_EVENT_TYPE, 'num_bases': 8,
        'transformer_nhead': 4, 'transformer_layers': 2, 'dropout': DROPOUT,
        'lr': LEARNING_RATE, 'weight_decay': 1e-5, 'clip_grad': 1.0,
        'batch_size': BATCH_SIZE, 'epochs': EPOCHS,
        'early_stopping_patience': EARLY_STOPPING_PATIENCE,
        # <<< CHANGE >>> Multi-task config
        'classification_loss_weight': CLASSIFICATION_LOSS_WEIGHT,
        'regression_loss_weight': REGRESSION_LOSS_WEIGHT,
        'regression_loss_type': REGRESSION_LOSS_TYPE.lower() # Ensure lowercase
    }

    train_samples, val_samples = train_test_split(all_training_samples, test_size=0.2, random_state=42)
    print(f"数据集划分: {len(train_samples)} 训练样本, {len(val_samples)} 验证样本")

    # --- 计算类别权重 (for classification loss) ---
    print("正在计算训练数据的类别权重...")
    count_positives = 0
    total_targets_in_train = 0
    num_nodes = graph_data.num_nodes
    targets_per_sample = num_nodes - 1
    for sample in train_samples:
        total_targets_in_train += targets_per_sample
        pos_in_sample = sum(1 for label_value in sample['labels'].values() if label_value == 1.0)
        count_positives += pos_in_sample
    count_negatives = total_targets_in_train - count_positives
    pos_weight_value = 1.0
    if count_positives > 0 and count_negatives > 0:
        pos_weight_value = count_negatives / count_positives
        print(f"计算完成: 正样本数={count_positives}, 负样本数={count_negatives}, pos_weight={pos_weight_value:.4f}")
    elif count_positives == 0: print("警告: 训练数据中未找到正样本，pos_weight 将为 1.0。")
    elif count_negatives == 0: print("警告: 训练数据中未找到负样本？pos_weight 将为 1.0。")
    pos_weight_tensor = torch.tensor([pos_weight_value], device=device)
    # --- 类别权重计算结束 ---


    model = RGCN_GAT_Transformer(
        node_feat_dim=node_feat_dim, hidden_dim=config['hidden_dim'],
        context_dim=config['context_dim'], embed_dim_event_type=config['embed_dim_event_type'],
        num_event_types=num_event_types, num_relations=num_relations,
        num_bases=config['num_bases'], transformer_nhead=config['transformer_nhead'],
        transformer_layers=config['transformer_layers'], num_nodes=graph_data.num_nodes,
        dropout=config['dropout']
    ).to(device)

    optimizer = optim.Adam(model.parameters(), lr=config['lr'], weight_decay=config['weight_decay'])
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, verbose=True, min_lr=1e-7) # Increased patience slightly

    # <<< CHANGE >>> Define two loss functions
    criterion_classification = nn.BCEWithLogitsLoss(pos_weight=pos_weight_tensor)
    if config['regression_loss_type'] == 'mse':
        # Use reduction='none' to apply mask before averaging
        criterion_regression = nn.MSELoss(reduction='none')
        print("Using MSELoss for time regression.")
    elif config['regression_loss_type'] == 'l1':
        criterion_regression = nn.L1Loss(reduction='none')
        print("Using L1Loss (MAE) for time regression.")
    else:
        raise ValueError("Invalid REGRESSION_LOSS_TYPE. Choose 'mse' or 'l1'.")


    # <<< CHANGE >>> Track more metrics
    train_losses_total, train_losses_cls, train_losses_reg = [], [], []
    val_losses_total, val_losses_cls, val_losses_reg = [], [], []
    val_aucs, val_f1s, val_maes = [], [], [] # Add MAE tracking

    print(f"\n开始多任务训练模型 (带早停), 最多 {config['epochs']} 轮...")
    print(f"配置: LR={config['lr']:.1e}, BS={config['batch_size']}, Hidden={config['hidden_dim']}, Dropout={config['dropout']}")
    print(f"Loss Weights: Cls={config['classification_loss_weight']}, Reg={config['regression_loss_weight']} ({config['regression_loss_type'].upper()})")

    best_val_loss = float('inf') # Monitor total validation loss for early stopping
    epochs_no_improve = 0
    best_epoch = -1
    stopped_epoch = -1

    for epoch in range(config['epochs']):
        model.train()
        epoch_train_loss_total, epoch_train_loss_cls, epoch_train_loss_reg = 0.0, 0.0, 0.0
        np.random.shuffle(train_samples)
        num_train_batches = math.ceil(len(train_samples) / config['batch_size'])

        with tqdm(total=num_train_batches, desc=f"Epoch {epoch + 1}/{config['epochs']} Train", unit="batch") as pbar:
            for i in range(0, len(train_samples), config['batch_size']):
                batch_samples_list = train_samples[i : i + config['batch_size']]
                batch = prepare_batch(batch_samples_list, graph_data.num_nodes)
                if batch is None: continue
                source_nodes = batch['source_nodes'].to(device); event_types = batch['event_types'].to(device)
                severities = batch['severities'].to(device); durations = batch['durations'].to(device)
                true_labels = batch['labels'].to(device); true_times = batch['true_times'].to(device) # <<< CHANGE >>> Get true times

                optimizer.zero_grad()
                # <<< CHANGE >>> Model output shape: [batch_size, num_targets, 2]
                outputs, _ = model(graph_data.x, graph_data.edge_index, graph_data.edge_type,
                                   source_nodes, event_types, severities, durations)

                # Separate outputs
                logits_cls = outputs[:, :, 0] # Classification logits
                preds_time = outputs[:, :, 1] # Regression predictions (direct output, no activation needed for MSE/L1)

                # <<< CHANGE >>> Calculate Classification Loss
                loss_cls = criterion_classification(logits_cls, true_labels)

                # <<< CHANGE >>> Calculate Regression Loss (Masked)
                # Calculate raw loss for all targets
                loss_reg_raw = criterion_regression(preds_time, true_times)
                # Create mask for affected nodes (where true_label == 1)
                mask_reg = (true_labels == 1).float() # Ensure mask is float for multiplication
                # Apply mask - only sum loss for affected nodes
                loss_reg_masked = loss_reg_raw * mask_reg
                # Average the loss *only* over the number of affected nodes
                num_affected = mask_reg.sum()
                if num_affected > 0:
                    loss_reg = loss_reg_masked.sum() / num_affected
                else:
                    loss_reg = torch.tensor(0.0, device=device) # No regression loss if no nodes were affected in batch

                # <<< CHANGE >>> Calculate Total Loss
                total_loss = (config['classification_loss_weight'] * loss_cls +
                              config['regression_loss_weight'] * loss_reg)

                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), config['clip_grad'])
                optimizer.step()

                epoch_train_loss_total += total_loss.item()
                epoch_train_loss_cls += loss_cls.item()
                epoch_train_loss_reg += loss_reg.item() # Note: loss_reg is already averaged over affected samples
                pbar.update(1)
                pbar.set_postfix({"L_tot": f"{total_loss.item():.4f}", "L_cls": f"{loss_cls.item():.4f}", "L_reg": f"{loss_reg.item():.2f}"})

        avg_train_loss_total = epoch_train_loss_total / num_train_batches if num_train_batches > 0 else 0.0
        avg_train_loss_cls = epoch_train_loss_cls / num_train_batches if num_train_batches > 0 else 0.0
        avg_train_loss_reg = epoch_train_loss_reg / num_train_batches if num_train_batches > 0 else 0.0
        train_losses_total.append(avg_train_loss_total)
        train_losses_cls.append(avg_train_loss_cls)
        train_losses_reg.append(avg_train_loss_reg)

        # --- Validation ---
        model.eval()
        epoch_val_loss_total, epoch_val_loss_cls, epoch_val_loss_reg = 0.0, 0.0, 0.0
        all_val_outputs_cls, all_val_preds_time = [], [] # Store both outputs
        all_val_labels, all_val_true_times = [], []     # Store both true labels
        num_val_batches = math.ceil(len(val_samples) / config['batch_size'])

        with torch.no_grad(), tqdm(total=num_val_batches, desc=f"Epoch {epoch + 1}/{config['epochs']} Val", unit="batch") as pbar_val:
            for i in range(0, len(val_samples), config['batch_size']):
                 batch_samples_list = val_samples[i : i + config['batch_size']]
                 batch = prepare_batch(batch_samples_list, graph_data.num_nodes)
                 if batch is None: continue
                 source_nodes = batch['source_nodes'].to(device); event_types = batch['event_types'].to(device)
                 severities = batch['severities'].to(device); durations = batch['durations'].to(device)
                 true_labels = batch['labels'].to(device); true_times = batch['true_times'].to(device) # <<< CHANGE >>> Get true times

                 outputs, _ = model(graph_data.x, graph_data.edge_index, graph_data.edge_type,
                                    source_nodes, event_types, severities, durations)

                 logits_cls = outputs[:, :, 0]
                 preds_time = outputs[:, :, 1]

                 loss_cls = criterion_classification(logits_cls, true_labels)
                 loss_reg_raw = criterion_regression(preds_time, true_times)
                 mask_reg = (true_labels == 1).float()
                 loss_reg_masked = loss_reg_raw * mask_reg
                 num_affected = mask_reg.sum()
                 loss_reg = loss_reg_masked.sum() / num_affected if num_affected > 0 else torch.tensor(0.0, device=device)
                 total_loss = (config['classification_loss_weight'] * loss_cls +
                               config['regression_loss_weight'] * loss_reg)

                 epoch_val_loss_total += total_loss.item()
                 epoch_val_loss_cls += loss_cls.item()
                 epoch_val_loss_reg += loss_reg.item()

                 # Store outputs and labels for metric calculation after loop
                 all_val_outputs_cls.extend(logits_cls.view(-1).cpu().numpy())
                 all_val_preds_time.extend(preds_time.view(-1).cpu().numpy())
                 all_val_labels.extend(true_labels.view(-1).cpu().numpy())
                 all_val_true_times.extend(true_times.view(-1).cpu().numpy())
                 pbar_val.update(1)

        avg_val_loss_total = epoch_val_loss_total / num_val_batches if num_val_batches > 0 else 0.0
        avg_val_loss_cls = epoch_val_loss_cls / num_val_batches if num_val_batches > 0 else 0.0
        avg_val_loss_reg = epoch_val_loss_reg / num_val_batches if num_val_batches > 0 else 0.0
        val_losses_total.append(avg_val_loss_total)
        val_losses_cls.append(avg_val_loss_cls)
        val_losses_reg.append(avg_val_loss_reg)

        # --- Calculate Metrics ---
        val_auc, val_f1, val_precision, val_recall = 0.0, 0.0, 0.0, 0.0
        val_mae = float('nan') # <<< CHANGE >>> Initialize MAE

        if len(all_val_outputs_cls) > 0 and len(all_val_labels) > 0:
            try:
                # Classification metrics
                all_val_probs = torch.sigmoid(torch.tensor(all_val_outputs_cls)).numpy()
                val_auc = roc_auc_score(all_val_labels, all_val_probs)
                val_preds_cls = (all_val_probs >= THRESHOLD).astype(int)
                val_f1 = f1_score(all_val_labels, val_preds_cls, zero_division=0)
                val_precision = precision_score(all_val_labels, val_preds_cls, zero_division=0)
                val_recall = recall_score(all_val_labels, val_preds_cls, zero_division=0)

                # <<< CHANGE >>> Regression metric (MAE on affected samples)
                val_labels_tensor = torch.tensor(all_val_labels)
                val_preds_time_tensor = torch.tensor(all_val_preds_time)
                val_true_times_tensor = torch.tensor(all_val_true_times)
                mask_val_reg = (val_labels_tensor == 1)
                num_affected_val = mask_val_reg.sum().item()
                if num_affected_val > 0:
                     val_mae = torch.abs(val_preds_time_tensor[mask_val_reg] - val_true_times_tensor[mask_val_reg]).mean().item()
                else:
                     val_mae = 0.0 # Or NaN, depending on how you want to handle no affected samples in validation

            except ValueError as e: print(f"\n警告: 计算指标时出错: {e}")

        val_aucs.append(val_auc); val_f1s.append(val_f1); val_maes.append(val_mae) # <<< CHANGE >>> Append MAE

        scheduler.step(avg_val_loss_total) # Use total validation loss for LR scheduling
        current_lr = optimizer.param_groups[0]['lr']

        print(f"\nEpoch {epoch + 1}/{config['epochs']} - LR: {current_lr:.1e}")
        print(f"  Train Loss: Total={avg_train_loss_total:.4f} (Cls={avg_train_loss_cls:.4f}, Reg={avg_train_loss_reg:.2f})")
        print(f"  Val Loss:   Total={avg_val_loss_total:.4f} (Cls={avg_val_loss_cls:.4f}, Reg={avg_val_loss_reg:.2f})")
        print(f"  Val Metrics: AUC={val_auc:.4f} F1={val_f1:.4f} Prec={val_precision:.4f} Rec={val_recall:.4f} MAE={val_mae:.2f}") # <<< CHANGE >>> Print MAE

        # --- Early Stopping and Best Model Saving (based on total validation loss) ---
        if avg_val_loss_total < best_val_loss:
            best_val_loss = avg_val_loss_total
            epochs_no_improve = 0
            best_epoch = epoch + 1
            # Save best model state
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_val_loss': best_val_loss,
                'val_auc': val_auc, # Store best metrics
                'val_f1': val_f1,
                'val_mae': val_mae,
                'config': config
            }, BEST_MODEL_TEMP_PATH)
            print(f"  Total validation loss improved to {best_val_loss:.4f}. Saving best model state.")
        else:
            epochs_no_improve += 1
            print(f"  Total validation loss did not improve for {epochs_no_improve} epoch(s).")

        if epochs_no_improve >= config['early_stopping_patience']:
            print(f"\nEarly stopping triggered after {epoch + 1} epochs.")
            stopped_epoch = epoch + 1
            break

    # --- Training Finished ---
    if stopped_epoch == -1: stopped_epoch = config['epochs']
    print(f"\n训练完成 {stopped_epoch} 轮。")

    # Load best model state
    best_val_auc, best_val_f1, best_val_mae = 0.0, 0.0, float('nan')
    if os.path.exists(BEST_MODEL_TEMP_PATH):
        print(f"Loading best model state from epoch {best_epoch} (Val Loss Total: {best_val_loss:.4f})...")
        checkpoint = torch.load(BEST_MODEL_TEMP_PATH)
        model.load_state_dict(checkpoint['model_state_dict'])
        best_val_auc = checkpoint.get('val_auc', 0.0)
        best_val_f1 = checkpoint.get('val_f1', 0.0)
        best_val_mae = checkpoint.get('val_mae', float('nan'))
        print("Best model loaded.")
        os.remove(BEST_MODEL_TEMP_PATH)
    else:
        print("警告: 未找到最佳模型临时文件。将使用最后一轮的模型。")
        if val_aucs: best_val_auc = val_aucs[-1]
        if val_f1s: best_val_f1 = val_f1s[-1]
        if val_maes: best_val_mae = val_maes[-1]

    # Save final best model
    os.makedirs(MODEL_DIR, exist_ok=True)
    final_save_content = {
        'model_state_dict': model.state_dict(),
        'config': config, 'node_id_map': node_id_map, 'event_type_map': event_type_map,
        'node_feat_dim': node_feat_dim, 'num_relations': num_relations, 'num_event_types': num_event_types,
        'best_epoch': best_epoch, 'stopped_epoch': stopped_epoch, 'best_val_loss': best_val_loss,
        'best_val_auc': best_val_auc, 'best_val_f1': best_val_f1, 'best_val_mae': best_val_mae # <<< CHANGE >>> Save best MAE
    }
    torch.save(final_save_content, MODEL_PATH)
    print(f"\nBest multi-task model state saved to {MODEL_PATH}")

    # Plotting (add regression loss and MAE)
    epochs_ran = stopped_epoch if stopped_epoch > 0 else len(train_losses_total)
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.figure(figsize=(18, 5)) # Wider figure

    # Loss Plot (Total, Cls, Reg)
    plt.subplot(1, 3, 1)
    plt.plot(range(1, epochs_ran + 1), train_losses_total[:epochs_ran], label='Train Loss Total', alpha=0.8)
    plt.plot(range(1, epochs_ran + 1), val_losses_total[:epochs_ran], label='Val Loss Total', linewidth=2)
    plt.plot(range(1, epochs_ran + 1), train_losses_cls[:epochs_ran], label='Train Loss Cls', linestyle=':', alpha=0.7)
    plt.plot(range(1, epochs_ran + 1), val_losses_cls[:epochs_ran], label='Val Loss Cls', linestyle=':', alpha=0.7)
    plt.plot(range(1, epochs_ran + 1), train_losses_reg[:epochs_ran], label='Train Loss Reg', linestyle='--', alpha=0.7)
    plt.plot(range(1, epochs_ran + 1), val_losses_reg[:epochs_ran], label='Val Loss Reg', linestyle='--', alpha=0.7)
    if best_epoch > 0: plt.axvline(best_epoch, color='r', linestyle='--', label=f'Best Epoch ({best_epoch})')
    plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.title('Loss Curves')
    plt.ylim(bottom=0) # Ensure y-axis starts at 0 for losses

    # Classification Metrics Plot
    plt.subplot(1, 3, 2)
    plt.plot(range(1, epochs_ran + 1), val_aucs[:epochs_ran], label='AUC')
    plt.plot(range(1, epochs_ran + 1), val_f1s[:epochs_ran], label='F1')
    if best_epoch > 0: plt.axvline(best_epoch, color='r', linestyle='--', label=f'Best Epoch ({best_epoch})')
    plt.xlabel('Epoch'); plt.ylabel('Score'); plt.legend(); plt.title('Validation Classification Metrics'); plt.ylim(0, 1)

    # <<< CHANGE >>> Regression Metric Plot (MAE)
    plt.subplot(1, 3, 3)
    # Filter out potential NaNs if MAE couldn't be calculated in some epochs
    valid_mae_epochs = [i+1 for i, mae in enumerate(val_maes[:epochs_ran]) if not np.isnan(mae)]
    valid_maes = [mae for mae in val_maes[:epochs_ran] if not np.isnan(mae)]
    if valid_maes:
        plt.plot(valid_mae_epochs, valid_maes, label='MAE (on affected)')
        if best_epoch > 0: plt.axvline(best_epoch, color='r', linestyle='--', label=f'Best Epoch ({best_epoch})')
        plt.xlabel('Epoch'); plt.ylabel('MAE (minutes)'); plt.legend(); plt.title('Validation Regression Metric'); plt.ylim(bottom=0) # MAE >= 0
    else:
        plt.text(0.5, 0.5, 'No valid MAE data to plot', horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
        plt.title('Validation Regression Metric')


    plt.tight_layout()
    # 获取当前时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # 格式化为年月日_时分秒
    # 构造文件名
    file_name = f'training_curve_multitask{timestamp}.png'

    plot_path = os.path.join(PLOTS_DIR, file_name)
    plt.savefig(plot_path)
    print(f"训练曲线已保存到 {plot_path}")

    return model

# ===================== 预测函数 (修改以返回时间) =====================

def load_model(model_path, device):
    """加载已训练的最佳多任务模型"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件未找到: {model_path}")
    checkpoint = torch.load(model_path, map_location=device)
    config = checkpoint['config']; node_id_map = checkpoint['node_id_map']; event_type_map = checkpoint['event_type_map']
    node_feat_dim = checkpoint['node_feat_dim']; num_relations = checkpoint['num_relations']; num_event_types = checkpoint['num_event_types']
    num_nodes = len(node_id_map)

    model = RGCN_GAT_Transformer(
        node_feat_dim=node_feat_dim, hidden_dim=config['hidden_dim'], context_dim=config['context_dim'],
        embed_dim_event_type=config['embed_dim_event_type'], num_event_types=num_event_types, num_relations=num_relations,
        num_bases=config.get('num_bases', 8),
        transformer_nhead=config['transformer_nhead'], transformer_layers=config['transformer_layers'],
        num_nodes=num_nodes, dropout=config.get('dropout', 0.1)
    ).to(device)

    try: model.load_state_dict(checkpoint['model_state_dict'])
    except RuntimeError as e:
        print(f"加载模型状态时出错: {e}\n尝试非严格加载...")
        model.load_state_dict(checkpoint['model_state_dict'], strict=False)

    model.eval()
    print(f"多任务模型已从 {model_path} 加载 (最佳模型)")
    print(f"  训练配置: LR={config.get('lr', 'N/A'):.1e}, BS={config.get('batch_size', 'N/A')}, Hidden={config.get('hidden_dim', 'N/A')}, Dropout={config.get('dropout', 'N/A')}")
    print(f"  Loss Weights: Cls={config.get('classification_loss_weight','N/A')}, Reg={config.get('regression_loss_weight','N/A')} ({config.get('regression_loss_type','N/A').upper()})")
    print(f"  停止于 Epoch: {checkpoint.get('stopped_epoch', 'N/A')}, 最佳 Epoch: {checkpoint.get('best_epoch', 'N/A')} (Val Loss Total: {checkpoint.get('best_val_loss', float('inf')):.4f})")
    print(f"  最佳验证指标: AUC={checkpoint.get('best_val_auc', 0.0):.4f}, F1={checkpoint.get('best_val_f1', 0.0):.4f}, MAE={checkpoint.get('best_val_mae', float('nan')):.2f}")
    return model, node_id_map, event_type_map


def predict_single_position(model, graph_data, source_position_id, event_type_str, severity, duration,
                            node_id_map, event_type_map, reverse_node_id_map,
                            threshold=0.5): # <<< CHANGE >>> Removed time_diff input
    """预测单个阵位发生指定特情时的影响 (概率 + 时间)"""
    device = next(model.parameters()).device
    model.eval()
    if source_position_id not in node_id_map: print(f"错误: 源阵位ID {source_position_id} 不存在"); return None
    source_node = node_id_map[source_position_id]
    if event_type_str not in event_type_map: print(f"错误: 事件类型 '{event_type_str}' 未知"); return None
    event_type_encoded = event_type_map[event_type_str]

    source_nodes_tensor = torch.tensor([source_node], dtype=torch.long, device=device)
    event_types_tensor = torch.tensor([event_type_encoded], dtype=torch.long, device=device)
    severities_tensor = torch.tensor([severity], dtype=torch.float, device=device)
    durations_tensor = torch.tensor([duration], dtype=torch.float, device=device)

    with torch.no_grad():
        # <<< CHANGE >>> Output shape: [1, num_targets, 2]
        outputs, target_node_masks = model(
            graph_data.x.to(device), graph_data.edge_index.to(device), graph_data.edge_type.to(device),
            source_nodes_tensor, event_types_tensor, severities_tensor, durations_tensor
        )

    # <<< CHANGE >>> Separate outputs
    logits_cls = outputs[:, :, 0].squeeze(0) # Shape: [num_targets]
    preds_time = outputs[:, :, 1].squeeze(0) # Shape: [num_targets]

    probabilities = torch.sigmoid(logits_cls).cpu().numpy()
    predicted_times = preds_time.cpu().numpy()

    target_nodes_indices = target_node_masks[0]
    predictions = []
    if len(probabilities) != len(target_nodes_indices) or len(predicted_times) != len(target_nodes_indices):
        print(f"警告: 预测输出数量与目标节点索引数量不匹配!")
        return None

    for i, node_idx in enumerate(target_nodes_indices):
        if node_idx in reverse_node_id_map:
             real_node_id = reverse_node_id_map[node_idx]
             prob = float(probabilities[i])
             pred_time = float(predicted_times[i])
             # Ensure predicted time is non-negative (optional, depends on model output characteristics)
             pred_time = max(0.0, pred_time)
             predictions.append({
                 'position_id': real_node_id,
                 'impact_probability': prob,
                 'is_affected': 1 if prob >= threshold else 0,
                 'predicted_impact_time_minutes': pred_time # <<< CHANGE >>> Add predicted time
             })
        else:
             print(f"警告: 在 reverse_node_id_map 中找不到索引 {node_idx}")

    predictions.sort(key=lambda x: x['impact_probability'], reverse=True)
    return predictions

# visualize_impact (Minor change to annotation if desired)
def visualize_impact(predictions, positions_df, source_position_id, threshold=0.5, save_path=None):
    """可视化特情影响预测结果 (可选择显示预测时间)"""
    if predictions is None: print("无预测结果可供可视化。"); return
    source_info_rows = positions_df[positions_df['position_id'] == source_position_id]
    if source_info_rows.empty: print(f"警告: 在 positions.csv 中找不到源阵位 {source_position_id} 的信息。"); return
    source_info = source_info_rows.iloc[0]

    plt.figure(figsize=(12, 10))
    plt.scatter(positions_df['x_coord'], positions_df['y_coord'], c='lightgray', s=80, alpha=0.5, label='未影响/低概率阵位')

    affected_positions = [p['position_id'] for p in predictions if p['is_affected'] == 1]
    affected_df = positions_df[positions_df['position_id'].isin(affected_positions)]
    if not affected_df.empty: plt.scatter(affected_df['x_coord'], affected_df['y_coord'], c='orange', s=100, alpha=0.8, label=f'受影响 (Prob>={threshold})')

    plt.scatter(source_info['x_coord'], source_info['y_coord'], c='red', s=250, marker='*', edgecolors='black', label=f'特情源: {source_position_id}')

    top_n = 10
    predictions_sorted = sorted(predictions, key=lambda x: x['impact_probability'], reverse=True)
    for pred in predictions_sorted[:top_n]:
        if pred['impact_probability'] > 0.1: # Only annotate reasonably likely ones
             pos_info_rows = positions_df[positions_df['position_id'] == pred['position_id']]
             if not pos_info_rows.empty:
                 pos_info = pos_info_rows.iloc[0]
                 # <<< CHANGE >>> Add predicted time to annotation
                 annotation_text = f"{pred['position_id']}\nP={pred['impact_probability']:.2f}\nT={pred['predicted_impact_time_minutes']:.1f}m"
                 plt.annotate(annotation_text,
                              (pos_info['x_coord'], pos_info['y_coord']),
                              textcoords="offset points", xytext=(0,10), ha='center', fontsize=8,
                              bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.6))

    plt.legend(loc='upper right')
    plt.title(f'阵位 {source_position_id} 发生特情的影响预测 (多任务模型)')
    plt.xlabel('X 坐标'); plt.ylabel('Y 坐标'); plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    if save_path:
        try: plt.savefig(save_path); print(f"可视化结果已保存到: {save_path}")
        except Exception as e: print(f"保存可视化图像时出错: {e}")
    # plt.show() # Optionally display plot
    plt.close()


def batch_prediction(model, graph_data, positions_df, node_id_map, event_type_map, reverse_node_id_map,
                     event_type_str, severity, duration, threshold=0.5): # <<< CHANGE >>> Removed time_diff input
    """批量预测所有阵位发生指定特情的影响 (概率 + 时间)"""
    results = {}
    position_ids = sorted(positions_df['position_id'].unique())
    if event_type_str not in event_type_map: print(f"错误: 用于批量预测的事件类型 '{event_type_str}' 未知。"); return None

    all_predictions_list = [] # Store detailed predictions for all source-target pairs
    for pos_id in tqdm(position_ids, desc="批量预测阵位"):
        predictions = predict_single_position(
            model, graph_data, pos_id, event_type_str, severity, duration,
            node_id_map, event_type_map, reverse_node_id_map, threshold=threshold
        )
        if predictions is None: continue

        affected_count = 0
        sum_pred_time_affected = 0.0
        high_risk_positions = [] # Store IDs of high probability nodes
        top_5_impacted = []      # Store {id, prob, time} for top 5

        for pred in predictions:
             # <<< CHANGE >>> Append detailed prediction including time
             all_predictions_list.append({
                 'source_position_id': pos_id,
                 'target_position_id': pred['position_id'],
                 'impact_probability': pred['impact_probability'],
                 'is_affected': pred['is_affected'],
                 'predicted_impact_time_minutes': pred['predicted_impact_time_minutes']
             })
             if pred['is_affected'] == 1:
                 affected_count += 1
                 sum_pred_time_affected += pred['predicted_impact_time_minutes']
             if pred['impact_probability'] >= 0.8:
                 high_risk_positions.append(pred['position_id'])

        total_possible_targets = graph_data.num_nodes - 1
        impact_ratio = affected_count / total_possible_targets if total_possible_targets > 0 else 0.0
        avg_pred_time_affected = sum_pred_time_affected / affected_count if affected_count > 0 else 0.0

        # Get top 5 impacted (by probability) including their predicted time
        predictions_sorted = sorted(predictions, key=lambda x: x['impact_probability'], reverse=True)
        top_5_impacted = [{'id': p['position_id'], 'prob': p['impact_probability'], 'time': p['predicted_impact_time_minutes']} for p in predictions_sorted[:5]]

        results[pos_id] = {
            'affected_count': affected_count, 'total_targets': total_possible_targets, 'impact_ratio': impact_ratio,
            'avg_predicted_time_affected_minutes': avg_pred_time_affected, # <<< CHANGE >>> Add avg predicted time
            'high_risk_positions': high_risk_positions,
            'top_5_impacted': top_5_impacted
        }

    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Save statistics
    impact_stats = pd.DataFrame.from_dict(results, orient='index')
    impact_stats.index.name = 'source_position_id'
    impact_stats['high_risk_positions_str'] = impact_stats['high_risk_positions'].apply(lambda x: ','.join(map(str, x)) if x else '')
    impact_stats['top_5_impacted_str'] = impact_stats['top_5_impacted'].apply(lambda x: ';'.join([f"{item['id']}(P:{item['prob']:.3f},T:{item['time']:.1f}m)" for item in x]) if x else '')
    stats_cols = ['affected_count', 'total_targets', 'impact_ratio', 'avg_predicted_time_affected_minutes', 'high_risk_positions_str', 'top_5_impacted_str'] # <<< CHANGE >>> Add time stat col
    stats_file = os.path.join(RESULTS_DIR, 'impact_statistics_multitask.csv')
    try: impact_stats[stats_cols].to_csv(stats_file)
    except Exception as e: print(f"保存统计信息时出错: {e}")

    # Save all predictions
    all_preds_df = pd.DataFrame(all_predictions_list)
    all_preds_file = os.path.join(RESULTS_DIR, 'all_impact_predictions_multitask.csv') # <<< CHANGE >>> New file name
    try: all_preds_df.to_csv(all_preds_file, index=False, float_format='%.4f') # Format floats
    except Exception as e: print(f"保存详细预测结果时出错: {e}")

    print(f"\n统计信息和详细预测结果已保存到 {RESULTS_DIR}")
    most_influential = impact_stats.sort_values('impact_ratio', ascending=False)
    return most_influential


# ===================== 主函数 (修改预测调用和结果显示) =====================
def main():
    os.makedirs(MODEL_DIR, exist_ok=True); os.makedirs(PLOTS_DIR, exist_ok=True); os.makedirs(RESULTS_DIR, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    mode = RUN_MODE; print(f"当前运行模式: {mode}")
    try:
        required_files = [POSITIONS_FILE, RELATIONS_FILE]
        if mode == 'train': required_files.extend([EVENTS_FILE, IMPACT_FILE])
        elif mode in ['predict', 'batch']:
             if not os.path.exists(MODEL_PATH): print(f"错误: 预测模式需要模型文件，但未找到: {MODEL_PATH}"); return
        for f in required_files:
            if not os.path.exists(f): print(f"错误: 必需文件不存在 {f}"); return

        print("正在加载并预处理数据..."); start_time = time.time()
        graph_data, training_samples_list, node_id_map, reverse_node_id_map, event_type_map, node_feat_dim, num_relations, num_event_types = load_and_preprocess_data(
            POSITIONS_FILE, RELATIONS_FILE, EVENTS_FILE, IMPACT_FILE)
        end_time = time.time(); print(f"数据加载完成，用时 {(end_time - start_time):.2f} 秒.")
        positions_df = pd.read_csv(POSITIONS_FILE) # Load positions for visualization/lookup

        if mode == 'train':
            print("\n开始多任务训练模型 (带早停)..."); start_time = time.time()
            model = train_model(graph_data, training_samples_list, node_id_map, event_type_map, node_feat_dim, num_relations, num_event_types)
            end_time = time.time(); print(f"\n模型训练完成，总用时 {(end_time - start_time):.2f} 秒")

        elif mode == 'predict':
            model, loaded_node_id_map, loaded_event_type_map = load_model(MODEL_PATH, device)
            node_id_map = loaded_node_id_map; reverse_node_id_map = {v: k for k, v in node_id_map.items()}; event_type_map = loaded_event_type_map
            print(f"\n预测阵位 {PREDICT_POSITION_ID} ..."); start_time = time.time()
            # <<< CHANGE >>> Removed time_diff input
            predictions = predict_single_position(model, graph_data, PREDICT_POSITION_ID, PREDICT_EVENT_TYPE, PREDICT_SEVERITY, PREDICT_DURATION,
                                               node_id_map, event_type_map, reverse_node_id_map, threshold=THRESHOLD)
            end_time = time.time()
            if predictions is not None:
                affected_count = sum(1 for p in predictions if p['is_affected'] == 1)
                print(f"\n预测结果: {affected_count} 个阵位可能受影响, 用时 {(end_time - start_time):.2f} 秒")
                print(f"\n影响概率 Top 10 (预测时间):")
                for i, pred in enumerate(predictions[:10]):
                    status = '受影响' if pred['is_affected'] == 1 else '未影响'
                    # <<< CHANGE >>> Print predicted time
                    print(f"  {i+1}. 阵位 {pred['position_id']}: Prob={pred['impact_probability']:.4f} ({status}), Pred Time={pred['predicted_impact_time_minutes']:.1f} min")

                # Save plot and results


                save_path_plot = os.path.join(PLOTS_DIR, f"impact_prediction_multitask_{PREDICT_POSITION_ID}.png")
                visualize_impact(predictions, positions_df, PREDICT_POSITION_ID, threshold=THRESHOLD, save_path=save_path_plot)
                result_file = os.path.join(RESULTS_DIR, f"impact_prediction_multitask_{PREDICT_POSITION_ID}.csv")
                try:
                    pd.DataFrame(predictions).to_csv(result_file, index=False, float_format='%.4f') # <<< CHANGE >>> Save time column
                    print(f"详细预测结果已保存到: {result_file}")
                except Exception as e: print(f"保存预测结果时出错: {e}")
            else: print("预测失败。")

        elif mode == 'batch':
            model, loaded_node_id_map, loaded_event_type_map = load_model(MODEL_PATH, device)
            node_id_map = loaded_node_id_map; reverse_node_id_map = {v: k for k, v in node_id_map.items()}; event_type_map = loaded_event_type_map
            print(f"\n开始批量预测所有阵位 ..."); start_time = time.time()
            # <<< CHANGE >>> Removed time_diff input
            most_influential = batch_prediction(model, graph_data, positions_df, node_id_map, event_type_map, reverse_node_id_map,
                                             BATCH_EVENT_TYPE, BATCH_SEVERITY, BATCH_DURATION, threshold=THRESHOLD)
            end_time = time.time()
            if most_influential is not None:
                print(f"\n批量预测完成，用时 {(end_time - start_time):.2f} 秒")
                # <<< CHANGE >>> Display avg predicted time stat
                print("\n影响最广泛的前10个源阵位 (按影响比例):"); print(most_influential[['affected_count', 'impact_ratio', 'avg_predicted_time_affected_minutes']].head(10).to_string(float_format="%.3f"))
            else: print("批量预测失败。")
        else: print(f"错误: 未知的运行模式 '{mode}'.")
    except FileNotFoundError as e: print(f"\n文件错误: {e}")
    except KeyError as e: print(f"\n数据错误: 键错误 {e}"); import traceback; traceback.print_exc()
    except Exception as e: print(f"\n发生未预料的错误: {type(e).__name__} - {str(e)}"); import traceback; traceback.print_exc()

if __name__ == "__main__":
    main()