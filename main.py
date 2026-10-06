from datetime import datetime
from typing import Optional
import requests
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import engine, get_db, SessionLocal
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Conexão Gamer - Conexão Express 100% Automático",
    description="API com estado de repouso: Aguardando Dados (Laranja) -> Pagamento -> Preparação...",
    version="2.7.0"
)

# ----------------------------------------------------
# TOKEN DE PRODUÇÃO DO MELHOR ENVIO CONFIGURADO:
# ----------------------------------------------------
MELHOR_ENVIO_TOKEN = "DptdWwqDDtoyZAjGaPmxpioaklKJbfKED4dn7F87"
MELHOR_ENVIO_URL = "https://www.melhorenvio.com.br/api/v2/me/shipment/tracking"

# Link oficial do caminhãozinho personalizado da Conexão Gamer
CAMINHAO_ICONE_URL = "https://i.postimg.cc/7L9P6BLB/Rastreio-removebg-preview.png"

# Mapeamento oficial de status com o estado "aguardando_dados"
STATUS_CONFIG = {
    "aguardando_dados": {
        "cor": "laranja", 
        "etapa": 0, 
        "rotulo": "AGUARDANDO DADOS", 
        "descricao": "Sistema em repouso - Nenhuma compra ou pagamento no momento"
    },
    "aguardando_pagamento": {
        "cor": "laranja", 
        "etapa": 1, 
        "rotulo": "AGUARDANDO", 
        "descricao": "Aguardando Confirmação de Pagamento"
    },
    "pagamento_aprovado": {
        "cor": "verde", 
        "etapa": 2, 
        "rotulo": "PAGO", 
        "descricao": "Pagamento Aprovado com Sucesso"
    },
    "preparando_envio": {
        "cor": "azul", 
        "etapa": 3, 
        "rotulo": "PREPARAÇÃO", 
        "descricao": "Pagamento Aprovado - Separando o Pedido"
    },
    "objeto_postado": {
        "cor": "azul", 
        "etapa": 4, 
        "rotulo": "POSTADO", 
        "descricao": "Objeto Postado na Transportadora"
    },
    "em_transito": {
        "cor": "azul", 
        "etapa": 5, 
        "rotulo": "EM TRÂNSITO", 
        "descricao": "Pacote em Trânsito rumo à sua cidade"
    },
    "saiu_para_entrega": {
        "cor": "azul", 
        "etapa": 6, 
        "rotulo": "EM ROTA", 
        "descricao": "Saiu para Entrega no seu endereço"
    },
    "entregue": {
        "cor": "verde", 
        "etapa": 7, 
        "rotulo": "ENTREGUE", 
        "descricao": "Entregue com Sucesso"
    },
    "pacote_recusado": {
        "cor": "vermelho", 
        "etapa": -1, 
        "rotulo": "RECUSADO", 
        "descricao": "Pacote Recusado"
    },
    "problema_entrega": {
        "cor": "vermelho", 
        "etapa": -1, 
        "rotulo": "PROBLEMA", 
        "descricao": "Problema na Entrega"
    }
}

class PedidoCreateSchema(BaseModel):
    pedido_id: str
    status: Optional[str] = "aguardando_pagamento"
    codigo_rastreio: Optional[str] = None

class WebhookAutoSchema(BaseModel):
    status: str
    codigo_rastreio: Optional[str] = None
    local_atual: Optional[str] = None

@app.get("/", summary="Status da API e Estado de Aguardando Dados")
def home(db: Session = Depends(get_db)):
    total_pedidos = db.query(models.PedidoRastreioModel).count()
    if total_pedidos == 0:
        # Retorna o modelo exato para a interface exibir o botão laranja "Aguardando Dados"
        return {
            "pedido_id": "geral",
            "servico": "Conexão Express",
            "codigo_rastreio": None,
            "status_atual": "aguardando_dados",
            "rotulo_etapa": STATUS_CONFIG["aguardando_dados"]["rotulo"],
            "descricao_status": STATUS_CONFIG["aguardando_dados"]["descricao"],
            "cor": STATUS_CONFIG["aguardando_dados"]["cor"],
            "progresso_etapa": STATUS_CONFIG["aguardando_dados"]["etapa"],
            "icone_caminhao": CAMINHAO_ICONE_URL,
            "local_atual": "Aguardando dados de novos pedidos",
            "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    return {
        "loja": "Conexão Gamer",
        "servico_envio": "Conexão Express",
        "status_api": "Online e operacional 🚀",
        "pedidos_registrados": total_pedidos
    }

@app.post("/api/pedidos", summary="Registro automático de novo pedido")
def criar_pedido(dados: PedidoCreateSchema, db: Session = Depends(get_db)):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    existente = db.query(models.PedidoRastreioModel).filter_by(pedido_id=dados.pedido_id).first()
    if existente:
        return {"mensagem": "Pedido já cadastrado.", "pedido": existente}

    status_inicial = dados.status if dados.status in STATUS_CONFIG else "aguardando_pagamento"

    novo_pedido = models.PedidoRastreioModel(
        pedido_id=dados.pedido_id,
        status=status_inicial,
        codigo_rastreio=dados.codigo_rastreio,
        local_atual="Aguardando liberação de pagamento real",
        ultima_atualizacao=agora
    )
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    return {"mensagem": "Pedido registrado com sucesso!", "pedido": novo_pedido}

@app.post("/api/webhook/atualizar/{pedido_id}", summary="Webhook Universal para automação total")
def webhook_atualizar(pedido_id: str, dados: WebhookAutoSchema, db: Session = Depends(get_db)):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    pedido = db.query(models.PedidoRastreioModel).filter_by(pedido_id=pedido_id).first()
    
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado para atualização automática.")

    if dados.status not in STATUS_CONFIG:
        raise HTTPException(status_code=400, detail="Status enviado é inválido.")

    pedido.status = dados.status
    if dados.codigo_rastreio:
        pedido.codigo_rastreio = dados.codigo_rastreio
    if dados.local_atual:
        pedido.local_atual = dados.local_atual
        
    pedido.ultima_atualizacao = agora
    db.commit()
    db.refresh(pedido)
    
    return {"mensagem": "Status atualizado 100% automaticamente!", "pedido": pedido}

@app.get("/api/rastreio/{pedido_id}", summary="Consulta de rastreio visual para o cliente")
def consultar_rastreio(pedido_id: str, db: Session = Depends(get_db)):
    pedido = db.query(models.PedidoRastreioModel).filter_by(pedido_id=pedido_id).first()
    
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    if pedido.codigo_rastreio and pedido.status not in ["entregue", "pacote_recusado", "problema_entrega"]:
        try:
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {MELHOR_ENVIO_TOKEN}"
            }
            body = {"orders": [pedido.codigo_rastreio]}
            requests.post(MELHOR_ENVIO_URL, json=body, headers=headers, timeout=5)
        except Exception:
            pass

    config_atual = STATUS_CONFIG.get(pedido.status, STATUS_CONFIG["aguardando_dados"])

    return {
        "pedido_id": pedido.pedido_id,
        "servico": "Conexão Express",
        "codigo_rastreio": pedido.codigo_rastreio,
        "status_atual": pedido.status,
        "rotulo_etapa": config_atual["rotulo"],
        "descricao_status": config_atual["descricao"],
        "cor": config_atual["cor"],
        "progresso_etapa": config_atual["etapa"],
        "icone_caminhao": CAMINHAO_ICONE_URL,
        "local_atual": pedido.local_atual,
        "ultima_atualizacao": pedido.ultima_atualizacao,
        "fluxo_status": list(STATUS_CONFIG.keys())
    }
