from fastapi import FastAPI, Depends, Request
from api_pedidos.esquema import Item, HealthCheckResponse, ErrorResponse
from uuid import UUID
from api_pedidos.excecao import PedidoNaoEncontradoError, FalhaDeComunicacaoError
from fastapi.responses import JSONResponse
from http import HTTPStatus
import os
# ...
url = 'http://127.0.0.1:8080'
import httpx

# tenant e apikey fixos somente para demonstrações
APIKEY = os.environ.get("APIKEY", "5734143a-595d-405d-9c97-6c198537108f")
TENANT_ID = os.environ.get("TENANT_ID", "21fea73c-e244-497a-8540-be0d3c583596")
MAGALU_API_URL = 'http://127.0.0.1:8080' #"http://localhost:8080/" #http://127.0.0.1:8080
MAESTRO_SERVICE_URL = f"{MAGALU_API_URL}/maestro/v1"

def _recupera_itens_por_pacote(uuid_do_pedido, uuid_do_pacote):
    response = httpx.get(
        f"{MAESTRO_SERVICE_URL}/orders/{uuid_do_pedido}/packages/{uuid_do_pacote}/items",
        headers={"X-Api-Key": APIKEY, "X-Tenant-Id": TENANT_ID},
    )
    response.raise_for_status()
    return [
        Item(
            sku=item["product"]["code"],
            # campos que utilizam a função get são opicionais
            description=item["product"].get("description", ""),
            image_url=item["product"].get("image_url", ""),
            reference=item["product"].get("reference", ""),
            quantity=item["quantity"],
        )
        for item in response.json()
    ]
def recuperar_itens_por_pedido(identificacao_do_pedido: UUID) -> list[Item]:
    try:
        response = httpx.get(
            f"{MAESTRO_SERVICE_URL}/orders/{identificacao_do_pedido}",
            headers={"X-Api-Key": APIKEY, "X-Tenant-Id": TENANT_ID},
        )
        response.raise_for_status()
        pacotes = response.json()["packages"]
        itens = []
        for pacote in pacotes:
            itens.extend(
                _recupera_itens_por_pacote(identificacao_do_pedido, pacote["uuid"])
            )
        return itens
    except httpx.HTTPStatusError as exc:
        # aqui poderiam ser tratados outros erros como autenticação
        if exc.response.status_code == HTTPStatus.NOT_FOUND:
            raise PedidoNaoEncontradoError() from exc
        raise exc
    except httpx.HTTPError as exc:
        raise FalhaDeComunicacaoError() from exc

app = FastAPI()

@app.get("/healthcheck", tags=["healthcheck"], summary="Integridade do sistema", description="Checa se o servidor está online")
async def healthcheck():
    return HealthCheckResponse(status= "ok")

@app.get("/orders/{identificacao_do_pedido}/items", responses={
    HTTPStatus.NOT_FOUND.value: {
        "description": "Pedido não encontrado",
        "model": ErrorResponse,
    },
    HTTPStatus.BAD_GATEWAY.value: {
        "description": "Falha de comunicação com o servidor remoto",
        "model": ErrorResponse,
    }}, tags=["pedidos"], summary="Itens de um pedido", description="Retorna todos os itens de um determinado pedido", response_model=list[Item])
def listar_itens(itens: list[Item] = Depends(recuperar_itens_por_pedido)):
    return itens


# ...

@app.exception_handler(PedidoNaoEncontradoError)
def tratar_erro_pedido_nao_encontrado(request: Request, exc: PedidoNaoEncontradoError):
    return JSONResponse(status_code=HTTPStatus.NOT_FOUND, content={"message": "Pedido não encontrado"})


@app.exception_handler(FalhaDeComunicacaoError)
def tratar_erro_falha_de_comunicacao(request: Request, exc: FalhaDeComunicacaoError):
    return JSONResponse(status_code=HTTPStatus.BAD_GATEWAY, content={"message": "Falha de comunicação com o servidor remoto"})
    