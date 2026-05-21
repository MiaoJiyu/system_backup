from fastapi import WebSocket, WebSocketDisconnect, Query
from app.websocket.manager import manager
from app.websocket.handler import handle_message


async def websocket_endpoint(ws: WebSocket, uuid: str = Query(...)):
    """Main WebSocket endpoint for client connections."""
    client_ip = ws.client.host if ws.client else "unknown"
    await manager.connect(ws, uuid, client_ip)

    try:
        while True:
            data = await ws.receive_text()
            await handle_message(ws, data)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


async def ws_logs_endpoint(ws: WebSocket, client_id: int):
    """WebSocket endpoint for log streaming to web frontend."""
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            # Echo back - the frontend will filter by client_id
            await ws.send_text(data)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
