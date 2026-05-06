"""
主应用入口
Main application entry
"""
import os
import sys
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
from contextlib import asynccontextmanager

# 导入自定义模块
# Import custom modules
from config import SERVER_CONFIG, NODE_TYPES, SIGNAL_CONFIG   # 添加 SIGNAL_CONFIG 导入
from websocket_handler import ws_manager

# 计算路径
# Compute paths
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, '..', 'frontend')
frontend_html_path = os.path.join(frontend_dir, 'index.html')

# 检查目录
# Check directories
if not os.path.exists(frontend_dir):
    print(f"错误：前端目录不存在 / Error: frontend directory not found: {frontend_dir}")
    sys.exit(1)
if not os.path.exists(frontend_html_path):
    print(f"错误：HTML文件不存在 / Error: HTML file not found: {frontend_html_path}")
    sys.exit(1)


# 应用生命周期管理
# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用生命周期 / Manage application lifecycle"""
    # 启动服务器 / Server startup
    print("=" * 50)
    print("多通道信号可视化服务器启动 / Multi-channel Signal Visualizer started")
    print(f"服务器地址 / Server address: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    print("=" * 50)
    
    # 启动数据广播任务 / Start data broadcast task
    broadcast_task = asyncio.create_task(broadcast_data_loop())
    
    yield
    
    # 关闭服务器 / Server shutdown
    broadcast_task.cancel()
    print("服务器关闭 / Server shutdown")
    
"""数据广播循环 / Data broadcast loop"""
async def broadcast_data_loop():
    while True:
        try:
            await ws_manager.broadcast_data()
            await asyncio.sleep(1)  # 每秒广播一次 / broadcast once per second
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"数据广播循环错误 / Data broadcast loop error: {e}")
            await asyncio.sleep(1)

# 创建FastAPI应用 / Create FastAPI app
app = FastAPI(
    title="SignalScope - Multi-channel Signal Visualizer",
    description="实时多通道信号可视化系统，适用于射电天文、SDR等 / Real-time multi-channel signal visualization for radio astronomy, SDR, etc.",
    version="3.0.0",
    lifespan=lifespan
)

# 挂载静态文件 / Mount static files
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

"""提供前端主页面 / Serve frontend homepage"""
@app.get("/")
async def get_homepage():   
    return FileResponse(frontend_html_path)

@app.get("/api/config")
async def get_config():
    """获取服务器配置 / Get server configuration"""
    return {
        "node_count": SIGNAL_CONFIG["node_count"],
        "node_types": list(NODE_TYPES.values()),
        "update_interval": SIGNAL_CONFIG["update_interval"]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点 / WebSocket endpoint"""
    await ws_manager.handle_client(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=SERVER_CONFIG["host"],
        port=SERVER_CONFIG["port"],
        reload=SERVER_CONFIG["debug"]
    )