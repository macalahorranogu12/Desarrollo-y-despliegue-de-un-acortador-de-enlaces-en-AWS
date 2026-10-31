import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3

app = FastAPI()

# Configuración CORS para permitir peticiones desde el frontend en S3
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción, reemplazar "*" por la URL de S3
    allow_methods=["*"],
    allow_headers=["*"],
)

# Boto3 tomará las credenciales del Rol IAM de la instancia EC2
dynamodb = boto3.resource('dynamodb', region_name='us-east-1') # Ajusta tu región
table = dynamodb.Table('url_shortener_table')

class URLRequest(BaseModel):
    original_url: str

@app.post("/shorten")
def shorten_url(req: URLRequest):
    short_code = str(uuid.uuid4())
    table.put_item(
        Item={
            'short_code': short_code,
            'original_url': req.original_url,
            'created_at': datetime.utcnow().isoformat()
        }
    )
    # Importante: Reemplazar <IP-PUBLICA-EC2> una vez que lances la instancia
    return {
        "short_code": short_code,
        "original_url": req.original_url,
        "short_url": f"http://<IP-PUBLICA-EC2>:8000/{short_code}"
    }

@app.get("/{short_code}")
def redirect_to_original(short_code: str):
    response = table.get_item(Key={'short_code': short_code})
    item = response.get('Item')
    if not item:
        raise HTTPException(status_code=404, detail="URL no encontrada")
    return RedirectResponse(url=item['original_url'], status_code=307)

@app.get("/urls/{short_code}")
def get_url_info(short_code: str):
    response = table.get_item(Key={'short_code': short_code})
    item = response.get('Item')
    if not item:
        raise HTTPException(status_code=404, detail="URL no encontrada")
    return item