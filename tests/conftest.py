import pytest
from unittest.mock import MagicMock, PropertyMock


@pytest.fixture
def mock_streamlit(mocker):
    mocker.patch("app.st.set_page_config")
    mocker.patch("app.st.title")
    mocker.patch("app.st.subheader")
    mocker.patch("app.st.markdown")
    mocker.patch("app.st.write")
    mocker.patch("app.st.info")
    mocker.patch("app.st.warning")
    mocker.patch("app.st.error")
    mocker.patch("app.st.write_stream")
    mocker.patch("app.st.stop")
    mocker.patch("app.st.rerun")
    mocker.patch("app.st.caption")

    mock_sidebar = MagicMock()
    mock_sidebar.header = MagicMock()
    mock_sidebar.text_input = MagicMock(return_value="")
    mocker.patch("app.st.sidebar", mock_sidebar)

    mock_button = MagicMock(return_value=False)
    mocker.patch("app.st.button", mock_button)

    mock_text_input = MagicMock(return_value="")
    mocker.patch("app.st.text_input", mock_text_input)

    mock_download_button = MagicMock()
    mocker.patch("app.st.download_button", mock_download_button)

    return {
        "sidebar": mock_sidebar,
        "button": mock_button,
        "text_input": mock_text_input,
        "download_button": mock_download_button,
    }


@pytest.fixture
def mock_openai_client(mocker):
    mock_client = MagicMock()
    mocker.patch("app.OpenAI", return_value=mock_client)
    return mock_client
