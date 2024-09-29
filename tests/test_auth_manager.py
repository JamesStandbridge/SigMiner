import os
import pytest
from unittest.mock import patch, MagicMock
from sigminer.auth.auth_manager import AuthManager


@pytest.fixture
def auth_manager():
    with patch("sigminer.auth.auth_manager.PublicClientApplication") as MockApp:
        MockApp.return_value.get_accounts.return_value = []
        manager = AuthManager(client_id="dummy_client_id", tenant_id="dummy_tenant_id")
        yield manager


def test_init(auth_manager):
    assert auth_manager.app is not None
    assert auth_manager.token_cache is not None


def test_get_access_token_silent_success(auth_manager):
    mock_account = {"username": "user@example.com"}
    mock_result = {"access_token": "dummy_access_token"}

    auth_manager.app.get_accounts.return_value = [mock_account]
    auth_manager.app.acquire_token_silent.return_value = mock_result

    token = auth_manager.get_access_token(scopes=["User.Read"])
    assert token == "dummy_access_token"
    auth_manager.app.acquire_token_silent.assert_called_once_with(
        scopes=["User.Read"], account=mock_account
    )


def test_get_access_token_silent_fail_interactive_success(auth_manager):
    mock_account = {"username": "user@example.com"}
    mock_result_silent = None
    mock_result_interactive = {"access_token": "dummy_access_token"}

    auth_manager.app.get_accounts.return_value = [mock_account]
    auth_manager.app.acquire_token_silent.return_value = mock_result_silent
    auth_manager.app.acquire_token_interactive.return_value = mock_result_interactive

    token = auth_manager.get_access_token(scopes=["User.Read"])
    assert token == "dummy_access_token"
    auth_manager.app.acquire_token_silent.assert_called_once_with(
        scopes=["User.Read"], account=mock_account
    )
    auth_manager.app.acquire_token_interactive.assert_called_once_with(
        scopes=["User.Read"]
    )


def test_get_access_token_interactive_fail(auth_manager):
    mock_account = {"username": "user@example.com"}
    mock_result_silent = None
    mock_result_interactive = {"error_description": "interaction required"}

    auth_manager.app.get_accounts.return_value = [mock_account]
    auth_manager.app.acquire_token_silent.return_value = mock_result_silent
    auth_manager.app.acquire_token_interactive.return_value = mock_result_interactive

    with pytest.raises(Exception) as excinfo:
        auth_manager.get_access_token(scopes=["User.Read"])
    assert "Unable to obtain a token" in str(excinfo.value)


@patch("builtins.open", new_callable=MagicMock)
@patch("os.path.exists", return_value=True)
def test_save_cache(mock_exists, mock_open, auth_manager):
    auth_manager.token_cache.has_state_changed = True
    auth_manager.token_cache.serialize = MagicMock(return_value="serialized_cache_data")
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    auth_manager.save_cache()
    mock_open.assert_called_once_with(auth_manager.CACHE_PATH, "w")
    auth_manager.token_cache.serialize.assert_called_once()
    mock_file.write.assert_called_once_with("serialized_cache_data")


@patch("os.makedirs")
@patch("builtins.open", new_callable=MagicMock)
@patch("os.path.exists", return_value=True)
def test_save_cache_no_change(mock_exists, mock_open, mock_makedirs, auth_manager):
    auth_manager.token_cache.has_state_changed = False
    auth_manager.save_cache()
    mock_open.assert_not_called()
    mock_makedirs.assert_not_called()
