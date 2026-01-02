from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
import os

SCOPES_SEARCHCONSOLE = ["https://www.googleapis.com/auth/webmasters.readonly"]

def load_service_account_credentials(service_account_file=None):
    path = service_account_file or os.environ.get("SERVICE_ACCOUNT_FILE")
    if not path:
        raise RuntimeError("Service account file path not provided. Set SERVICE_ACCOUNT_FILE env var or pass path.")
    credentials = service_account.Credentials.from_service_account_file(
        path, scopes=SCOPES_SEARCHCONSOLE
    )
    return credentials


def get_searchconsole_service(service_account_file=None):
    creds = load_service_account_credentials(service_account_file)
    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    return service


def get_ga4_client(service_account_file=None):
    path = service_account_file or os.environ.get("SERVICE_ACCOUNT_FILE")
    if not path:
        raise RuntimeError("Service account file path not provided. Set SERVICE_ACCOUNT_FILE env var or pass path.")
    credentials = service_account.Credentials.from_service_account_file(path)
    client = BetaAnalyticsDataClient(credentials=credentials)
    return client
