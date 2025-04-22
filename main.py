from grafo import AgenteCondicionesRios

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

agente = AgenteCondicionesRios()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mostrar index.html en la raíz
@app.get("/", response_class=HTMLResponse)
async def get_index():
    return FileResponse("static/index.html")

# Modelo para mensajes de chat
class ChatMessage(BaseModel):
    message: str
    chat_id: str

@app.post("/chat")
async def chat_endpoint(msg: ChatMessage):
    response = agente.pregunta(msg.chat_id, msg.message)
    return { "reply": response }

