# Permitir CORS (recomenda-se especificar o IP em produção)
from http.client import ImproperConnectionState
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


@app.get("/")
def read_root():
    return{"massage": "Servidor OnLine"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gerenciador de conexões por sala


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(room, []).append(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        self.active_connections[room].remove(websocket)

    async def broadcast(self, room: str, message: str):
        for connection in self.active_connections.get(room, []):
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str,
                             token: str = Query(...)):
    await manager.connect(room, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(room, f"{token}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(room, websocket)
        await manager.broadcast(room, f"{token} saiu da sala.")