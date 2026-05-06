"""
后端配置文件
Backend configuration file
"""

# 服务器配置
# Server configuration
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True
}

# 信号生成配置
# Signal generation configuration
SIGNAL_CONFIG = {
    "node_count": 20,               # 节点数量 / Number of nodes
    "samples_per_node": 500,        # 每节点采样点数 / Samples per node
    "update_interval": 1.0,         # 秒 / seconds
    "max_amplitude": 100,           # 最大幅度 / Max amplitude (adjusted for wider range)
    "min_amplitude": -100           # 最小幅度 / Min amplitude
}

# 节点信号类型配置
# Node signal type configuration
NODE_TYPES = {
    "simulated": "Simulated Data (Generated)",   # 模拟数据节点 / Simulated data source
    "real": "Real Data (Hardware)"               # 真实数据节点 / Real data source (for SDR, radio telescope, etc.)
}