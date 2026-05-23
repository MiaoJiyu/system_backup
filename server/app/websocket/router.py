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
        await manager.disconnect(ws)
    except Exception:
        await manager.disconnect(ws)


async def ws_logs_endpoint(ws: WebSocket, client_id: int):
    """WebSocket endpoint for log streaming to web frontend."""
    await ws.accept()
    manager.add_log_viewer(client_id, ws)
    try:
        while True:
            # Keep connection alive, listen for pings (or just wait for disconnect)
            data = await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.remove_log_viewer(client_id, ws)
