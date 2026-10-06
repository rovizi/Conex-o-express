@app.get("/api/rastreio/{pedido_id}", summary="Consulta de rastreio individual do pedido")
def consultar_rastreio(pedido_id: str, db: Session = Depends(get_db)):
    # Busca o pedido específico no banco de dados pelo ID ou código de rastreio
    pedido = db.query(models.PedidoRastreioModel).filter(
        (models.PedidoRastreioModel.pedido_id == pedido_id) | 
        (models.PedidoRastreioModel.codigo_rastreio == pedido_id)
    ).first()
    
    if not pedido:
        raise HTTPException(
            status_code=404, 
            detail=f"Pedido '{pedido_id}' não encontrado na base de dados."
        )

    # Consulta opcional na API do Melhor Envio se houver código de rastreio válido
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
        "local_atual": pedido.local_atual or "Processando na base logística",
        "ultima_atualizacao": pedido.ultima_atualizacao,
        "fluxo_status": list(STATUS_CONFIG.keys())
    }
