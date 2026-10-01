from erp_sim.db import supabase
from erp_sim.seed_data import PRODUTOS, CLIENTES

def run_seed():
    print("Inserindo produtos...")
    for p in PRODUTOS:
        supabase.table("erp_produtos").upsert(p, on_conflict="codigo").execute()
    print("Inserindo clientes...")
    for c in CLIENTES:
        try:
            supabase.table("erp_clientes").insert(c).execute()
        except Exception:
            pass # já existe
    print("Seed concluído!")

if __name__ == "__main__":
    run_seed()
