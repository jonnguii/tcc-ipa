import json
import hashlib
from pathlib import Path
from src.ipa.schemas import PedidoExtraido

CACHE_FILE = Path(".ai_cache.json")

def _get_file_hash(caminho_arquivo: Path) -> str:
    """Gera um hash MD5 do conteúdo do arquivo para sabermos se ele já foi visto."""
    with open(caminho_arquivo, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def _load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_cache(cache_data: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)

def check_cache(caminho_arquivo: str) -> PedidoExtraido | None:
    """Verifica se este exato arquivo já foi processado antes. Retorna o objeto se sim."""
    path = Path(caminho_arquivo)
    file_hash = _get_file_hash(path)
    
    cache_data = _load_cache()
    if file_hash in cache_data:
        print(f"⚡ [CACHE HIT] Arquivo {path.name} já extraído antes! Lendo do cache... (0 custo)")
        return PedidoExtraido.model_validate(cache_data[file_hash])
    
    return None

def save_to_cache(caminho_arquivo: str, resultado: PedidoExtraido):
    """Salva o resultado da extração no cache."""
    path = Path(caminho_arquivo)
    file_hash = _get_file_hash(path)
    
    cache_data = _load_cache()
    cache_data[file_hash] = resultado.model_dump()
    _save_cache(cache_data)
