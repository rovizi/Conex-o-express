from database import Base
from sqlalchemy import Column, Integer, String

class PedidoRastreioModel(Base):
    __tablename__ = "pedidos_rastreio"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(String, unique=True, index=True)
    codigo_rastreio = Column(String, nullable=True, index=True)
    status = Column(String, default="aguardando_pagamento")
    local_atual = Column(String, nullable=True)
    ultima_atualizacao = Column(String, nullable=True)