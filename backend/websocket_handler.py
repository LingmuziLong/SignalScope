"""
WebSocket处理器模块
WebSocket handler module
"""
import asyncio
import json
from typing import Dict, Any
from fastapi import WebSocket
from signal_generator import signal_gen  
from config import SIGNAL_CONFIG, NODE_TYPES

class WebSocketManager:
    """WebSocket连接管理器 / WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections = []
        # 默认显示模拟数据节点 / Default to simulated data source
        self.current_node_type = NODE_TYPES["simulated"]
        # 动态节点数量，初始读取配置 / Dynamic node count, initially from config
        self.node_count = SIGNAL_CONFIG["node_count"]
    
    async def connect(self, websocket: WebSocket):
        """接受新的WebSocket连接 / Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"新的WebSocket客户端连接，当前连接数 / New WebSocket client, active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接 / Disconnect WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket客户端断开，剩余连接数 / WebSocket client disconnected, remaining connections: {len(self.active_connections)}")
    
    async def switch_node_type(self, node_type: str, websocket: WebSocket):
        """切换节点类型 / Switch node type"""
        if node_type in NODE_TYPES.values():
            self.current_node_type = node_type
            print(f"切换到节点类型 / Switched to node type: {node_type}")
            await websocket.send_json({
                "type": "notification",
                "message": f"已切换到 / Switched to {node_type}"
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"未知的节点类型 / Unknown node type: {node_type}"
            })
    
    async def set_node_count(self, count: int, websocket: WebSocket):
        """设置节点数量 / Set node count"""
        # 限制范围 1-100 / Limit range 1-100
        count = max(1, min(100, count))
        if count == self.node_count:
            return
        self.node_count = count
        SIGNAL_CONFIG["node_count"] = count   # 同步到全局配置 / Sync to global config
        print(f"节点数量已更改为 / Node count changed to: {count}")
        await websocket.send_json({
            "type": "notification",
            "message": f"节点数量已设置为 {count} / Node count set to {count}"
        })
        # 立即广播一次新数量的数据 / Broadcast new data immediately
        await self.broadcast_data()
    
    async def broadcast_data(self):
        """广播数据到所有连接的客户端 / Broadcast data to all connected clients"""
        if not self.active_connections:
            return
        
        try:
            # 生成所有节点数据 / Generate data for all nodes
            all_nodes_data = []
            # 根据当前节点类型生成数据 / Generate data based on current node type
            for node_idx in range(self.node_count):
                if self.current_node_type == NODE_TYPES["real"]:
                    node_data = signal_gen.generate_node_data(node_idx, "real")
                else:
                    node_data = signal_gen.generate_node_data(node_idx, "simulated")
                all_nodes_data.append(node_data)
            
            # 构建数据包 / Build data packet
            data_packet = {
                "type": "data",
                "nodes": all_nodes_data,
                "timestamp": asyncio.get_event_loop().time(),
                "current_node": self.current_node_type
            }
            
            # 广播到所有客户端 / Broadcast to all clients
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(data_packet)
                except Exception as e:
                    print(f"发送数据到客户端失败 / Failed to send data to client: {e}")
                    disconnected.append(connection)
            
            # 清理断开连接的客户端 / Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection)
                
        except Exception as e:
            print(f"生成或发送数据时出错 / Error generating or sending data: {e}")
    
    async def handle_client(self, websocket: WebSocket):
        """处理单个客户端连接 / Handle single client connection"""
        await self.connect(websocket)
        
        try:
            while True:
                # 非阻塞接收客户端消息 / Non-blocking receive client message
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(), 
                        timeout=0.1
                    )
                    msg = json.loads(data)
                    
                    if msg.get("action") == "switch_node":
                        await self.switch_node_type(msg.get("node", ""), websocket)
                    elif msg.get("action") == "set_node_count":
                        new_count = int(msg.get("count", 20))
                        await self.set_node_count(new_count, websocket)
                        
                except asyncio.TimeoutError:
                    pass
                
                # 等待下一次数据发送 / Wait for next data transmission
                await asyncio.sleep(SIGNAL_CONFIG["update_interval"])
                
        except Exception as e:
            print(f"WebSocket连接错误 / WebSocket connection error: {e}")
        finally:
            self.disconnect(websocket)


# 全局WebSocket管理器实例 / Global WebSocket manager instance
ws_manager = WebSocketManager()