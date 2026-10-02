from pydantic import BaseModel, Field
from typing import List, Optional

class ItemPedido(BaseModel):
    codigo: str = Field(..., description="Código do produto no ERP. Ex: P-001")
    quantidade: float = Field(..., description="Quantidade solicitada do produto")

class ClienteInfo(BaseModel):
    id: Optional[int] = Field(None, description="ID interno do cliente no banco (se já existir e for identificado)")
    novo: Optional[bool] = Field(False, description="Sinaliza se é um cliente novo que precisa ser cadastrado")
    nome: Optional[str] = Field(None, description="Nome do cliente (obrigatório se novo=True)")
    cnpj_cpf: Optional[str] = Field(None, description="CNPJ/CPF do cliente (obrigatório se novo=True)")
    email: Optional[str] = Field(None, description="Email do cliente (obrigatório se novo=True)")

class PedidoExtraido(BaseModel):
    ref_id: str = Field(..., description="Referência única (gerada pelo Orquestrador) para controle de duplicidade")
    cliente: ClienteInfo
    data_entrega: str = Field(..., description="Data limite de entrega no formato YYYY-MM-DD")
    observacoes: str = Field("", description="Observações adicionais ou notas de entrega")
    itens: List[ItemPedido] = Field(..., description="Lista de produtos do pedido", min_length=1)
