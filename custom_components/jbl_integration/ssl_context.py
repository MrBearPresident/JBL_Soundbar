"""SSL context helpers for JBL integration."""
import certifi
import ssl

CERT_PATH = "custom_components/jbl_integration/Cert.pem"
KEY_PATH = "custom_components/jbl_integration/Key.pem"


def _create_ssl_context(cert_path, key_path):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    return ssl_context


async def async_create_ssl_context(hass):
    cert_path = hass.config.path(CERT_PATH)
    key_path = hass.config.path(KEY_PATH)
    return await hass.async_add_executor_job(_create_ssl_context, cert_path, key_path)