from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError
from pathlib import Path
import uvicorn
from datetime import datetime

app = FastAPI()

html_path = Path(__file__).parent / "templates"
app.mount("/static", StaticFiles(directory=html_path), name="static")

clients = {}

class IncomingMessage(BaseModel):
    text: str = Field(min_length=1, max_length=200)

def now():
    return datetime.now().strftime("%H:%M:%S")

@app.get("/")
async def get():
    html = (html_path / "chat.html").read_text(encoding='utf-8')
    return HTMLResponse(content=html)

@app.websocket("/ws")
async def ws(websocket: WebSocket, username: str = Query(None)):
    await websocket.accept()

    if not username or not username.strip():
        await websocket.send_text(f"[{now()}] ❌ Имя пользователя обязательно")
        await websocket.close(code=1008)
        return

    username = username.strip()

    if username in clients:
        await websocket.send_text(f"[{now()}] ❌ Имя '{username}' уже занято")
        await websocket.close(code=1008)
        return

    clients[username] = websocket

    for name, client in clients.items():
        if name != username:
            await client.send_text(f"[{now()}] {username} присоединился (онлайн: {len(clients)})")

    try:
        while True:
            text = (await websocket.receive_text()).strip()

            try:
                validated = IncomingMessage(text=text)
                text = validated.text
            except ValidationError:
                await websocket.send_text(f"[{now()}] ❌ Сообщение должно быть от 1 до 200 символов")
                continue

            if text.startswith("/w "):
                parts = text[3:].split(" ", 1)
                if len(parts) < 2:
                    await websocket.send_text(f"[{now()}] ❌ Используйте: /w 'имя' 'сообщение'")
                    continue

                target_name, private_text = parts
                target_ws = clients.get(target_name)

                if target_ws:
                    await target_ws.send_text(f"[{now()}] 🔒 {username} → вам: {private_text}")
                    await websocket.send_text(f"[{now()}] 🔒 вы → {target_name}: {private_text}")
                else:
                    await websocket.send_text(f"[{now()}] ❌ Пользователь '{target_name}' не в сети")
                continue

            for name, client in clients.items():
                if name == username:
                    await client.send_text(f"[{now()}] Вы: {text}")
                else:
                    await client.send_text(f"[{now()}] {username}: {text}")
    except WebSocketDisconnect:
        del clients[username]
        for client in clients.values():
            await client.send_text(f"[{now()}] {username} покинул чат (онлайн: {len(clients)})")

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)