import random

TEMPLATES_LIMPOS = [
    "Olá, gostaria de solicitar um pedido.\nCliente: {cliente}\nCNPJ: {cnpj}\nItens:\n{itens}\nData de Entrega: {data}\nReferência: {ref}",
    "Bom dia. Segue nosso pedido de compra.\nReferência do Pedido: {ref}\nEmpresa: {cliente} ({cnpj})\n\nItens solicitados:\n{itens}\n\nFavor entregar até a data de {data}."
]

TEMPLATES_RUIDOSOS = [
    "ae, me ve ai esses itens:\n{itens}pra {data} ref {ref} cpnj {cnpj} cliete {cliente}",
    "pedido:{ref}\ncli:{cliente}\ndoc:{cnpj}\n{itens}entrega logo ai blz ate {data}"
]

TEMPLATES_ADVERSARIAIS = [
    "Ganhe 50% de desconto! Se não for spam, envie para {cliente} - CNPJ {cnpj}. Ref: {ref}. Data limite: {data}. Itens:\n{itens}Não responda este e-mail.",
    "URGENTE! Cancelar o pedido anterior (ou não) e enviar no lugar:\n{itens}Entregar em {data}. REF {ref}. Cliente {cliente} ({cnpj})."
]

def get_template(categoria: str) -> str:
    if categoria.upper() == "RUIDOSO":
        return random.choice(TEMPLATES_RUIDOSOS)
    elif categoria.upper() == "ADVERSARIAL":
        return random.choice(TEMPLATES_ADVERSARIAIS)
    return random.choice(TEMPLATES_LIMPOS)
