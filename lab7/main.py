from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles 
from pathlib import Path
import uvicorn
import json
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError

app = FastAPI()

html_path = Path(__file__).parent / "templates" 
app.mount("/static", StaticFiles(directory=html_path), name="static") 

clients = {}

class IncomingMessage(BaseModel):
    text: str = Field(min_length=1, max_length=200)

def create_error_message(detail: str) -> str:
    return json.dumps({
        "type": "error",
        "detail": detail,
        "ts": datetime.now().isoformat()
    })

def create_chat_message(user: str, text: str) -> str:
    return json.dumps({
        "type": "message",
        "user": user,
        "text": text,
        "ts": datetime.now().isoformat()
    })

def create_private_message(from_user: str, to_user: str, text: str) -> str:
    return json.dumps({
        "type": "private",
        "from": from_user,
        "to": to_user,
        "text": text,
        "ts": datetime.now().isoformat()
    })
    
@app.get("/") 
async def get(): 
    html = (html_path / "chat.html").read_text(encoding='utf-8')
    return HTMLResponse(content=html, status_code=200)

@app.websocket("/ws")
async def ws(websocket: WebSocket, username: str = Query(None)):
    await websocket.accept()
    if not username or username.strip() == "":
        await websocket.send_text(create_error_message("Имя пользователя обязательно"))
        await websocket.close(code=1008)
        return
    
    username = username.strip()
    
    if username in clients.values():
        await websocket.send_text(create_error_message(f"Имя '{username}' уже занято"))
        await websocket.close(code=1008)
        return
    
    clients[websocket] = username

    for client in clients:
        if client != websocket:
            await client.send_text(create_chat_message(username, f"присоединился (онлайн: {len(clients)})"))
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                validated = IncomingMessage(**message_data)
                text = validated.text
            except json.JSONDecodeError:
                await websocket.send_text(create_error_message("Невалидный JSON"))
                continue
            except ValidationError:
                await websocket.send_text(create_error_message("Сообщение должно быть от 1 до 200 символов"))
                continue
            
            if text.startswith("/w "):
                rest = text[3:]
                parts = rest.split(" ", 1)
                
                if len(parts) < 2:
                    await websocket.send_text(create_error_message("Используйте: /w 'имя' 'сообщение'"))
                    continue
                
                target_user = parts[0]
                private_text = parts[1]
                
                target_ws = None
                for ws, name in clients.items():
                    if name == target_user:
                        target_ws = ws
                        break
                
                if target_ws:
                    await target_ws.send_text(create_private_message(username, target_user, private_text))
                    await websocket.send_text(create_private_message(username, target_user, private_text))
                else:
                    await websocket.send_text(create_error_message(f"Пользователь '{target_user}' не в сети"))
                continue
            
            for client in clients:
                if client == websocket:
                    await client.send_text(create_chat_message("Вы", text))
                else:
                    await client.send_text(create_chat_message(username, text))
                
    except WebSocketDisconnect:
        if websocket in clients:
            del clients[websocket]
        for client in clients:
            await client.send_text(create_chat_message(username, f"покинул чат (онлайн: {len(clients)})"))

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)