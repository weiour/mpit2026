from gigachat import GigaChat

from app.core.config import settings


def make_client() -> GigaChat:
    creds = settings.GIGACHAT_CREDENTIALS
    if not creds:
        raise RuntimeError("Не задан GIGACHAT_CREDENTIALS")

    verify_ssl = True
    if settings.GIGACHAT_VERIFY_SSL_CERTS is not None:
        if settings.GIGACHAT_VERIFY_SSL_CERTS.lower() in ("0", "false", "no"):
            verify_ssl = False

    ca_bundle = settings.GIGACHAT_CA_BUNDLE_FILE or None

    return GigaChat(
        credentials=creds,
        verify_ssl_certs=verify_ssl,
        ca_bundle_file=ca_bundle,
    )
