from server.auth.sheets_client import GoogleSheetsClient

from wren.app_server.utils.logger import wren_logger


def test_import():
    assert wren_logger is not None
    assert GoogleSheetsClient is not None
