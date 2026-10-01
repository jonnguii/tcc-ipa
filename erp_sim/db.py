from supabase import create_client, Client
from src.ipa.config import settings

supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
