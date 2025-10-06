"""
Supabase client configuration for Agora Analyst.
"""

import os
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance.

    Returns:
        Client: Configured Supabase client

    Raises:
        ValueError: If required environment variables are missing
    """
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")

    options = SyncClientOptions(schema='agora')
    return create_client(url, key, options=options)

def get_supabase_admin_client() -> Client:
    """
    Create and return a Supabase client with admin privileges for data operations.

    Returns:
        Client: Configured Supabase admin client

    Raises:
        ValueError: If required environment variables are missing
    """
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")

    options = SyncClientOptions(schema='agora')
    return create_client(url, key, options=options)