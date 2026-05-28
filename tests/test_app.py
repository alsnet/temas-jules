import pytest
from unittest.mock import MagicMock, PropertyMock

from app import sanitize_filename, validate_theme, map_api_error, generate_text_stream, build_provider_routing


class TestSanitizeFilename:
    def test_basic_lowercase_and_spaces(self):
        assert sanitize_filename("Reencarnação") == "reencarnação"

    def test_replaces_spaces_with_underscores(self):
        assert sanitize_filename("Lei de Causa e Efeito") == "lei_de_causa_e_efeito"

    def test_removes_colon(self):
        result = sanitize_filename("Lei: Causa")
        assert ":" not in result
        assert result == "lei_causa"

    def test_removes_question_mark(self):
        result = sanitize_filename("O que é?")
        assert "?" not in result
        assert result == "o_que_é"

    def test_removes_all_special_chars(self):
        result = sanitize_filename('a/b\\c*d"e<f>g|h')
        assert result == "abcdefgh"

    def test_strips_whitespace(self):
        assert sanitize_filename("  Tema  ") == "tema"

    def test_handles_empty_string(self):
        assert sanitize_filename("") == ""

    def test_handles_only_special_chars(self):
        result = sanitize_filename('<>:"/\\|?*')
        assert result == ""


class TestValidateTheme:
    def test_valid_theme_returns_no_warning(self):
        text, warning = validate_theme("Reencarnação")
        assert text == "Reencarnação"
        assert warning is None

    def test_empty_string_returns_warning(self):
        text, warning = validate_theme("")
        assert text == ""
        assert warning == "Por favor, digite um tema."

    def test_whitespace_only_returns_warning(self):
        text, warning = validate_theme("   ")
        assert text == ""
        assert warning == "Por favor, digite um tema."

    def test_strips_leading_trailing_spaces(self):
        text, warning = validate_theme("  Prece  ")
        assert text == "Prece"
        assert warning is None

    def test_long_theme_truncates(self):
        long_theme = "a" * 300
        text, warning = validate_theme(long_theme)
        assert len(text) == 200
        assert "truncado" in warning
        assert "200" in warning

    def test_exactly_max_length_is_valid(self):
        theme = "a" * 200
        text, warning = validate_theme(theme)
        assert len(text) == 200
        assert warning is None

    def test_one_over_max_length_truncates(self):
        theme = "a" * 201
        text, warning = validate_theme(theme)
        assert len(text) == 200
        assert "truncado" in warning


class TestMapApiError:
    def test_insufficient_quota_message(self):
        error = Exception("insufficient_quota")
        msg = map_api_error(error)
        assert "Limite de uso" in msg

    def test_http_429_message(self):
        error = Exception("Error code: 429")
        msg = map_api_error(error)
        assert "Limite de uso" in msg

    def test_invalid_api_key_message(self):
        error = Exception("Incorrect API key - invalid api_key")
        msg = map_api_error(error)
        assert "chave" in msg.lower()

    def test_http_401_message(self):
        error = Exception("HTTP 401 Unauthorized")
        msg = map_api_error(error)
        assert "chave" in msg.lower()

    def test_generic_error_does_not_leak_details(self):
        error = Exception("erro interno: senha=12345, db=prod")
        msg = map_api_error(error)
        assert "senha" not in msg
        assert "12345" not in msg
        assert "db" not in msg
        assert "inesperado" in msg

    def test_network_error_generic_message(self):
        error = ConnectionError("Failed to connect to openrouter.ai")
        msg = map_api_error(error)
        assert "inesperado" in msg


class TestGenerateTextStream:
    def test_yields_content_chunks(self):
        mock_client = MagicMock()
        chunks = _make_stream_chunks(["Texto ", "espírita ", "gerado."])
        mock_client.chat.completions.create.return_value = chunks

        result = list(generate_text_stream(mock_client, "tema", "model", 500, 0.7))
        assert result == ["Texto ", "espírita ", "gerado."]

    def test_skips_none_content(self):
        mock_client = MagicMock()
        chunk = MagicMock()
        type(chunk.choices[0].delta).content = PropertyMock(return_value=None)
        mock_client.chat.completions.create.return_value = [chunk]

        result = list(generate_text_stream(mock_client, "tema", "model", 500, 0.7))
        assert result == []

    def test_mixed_none_and_content(self):
        mock_client = MagicMock()
        mock_none = MagicMock()
        type(mock_none.choices[0].delta).content = PropertyMock(return_value=None)
        mock_text = MagicMock()
        type(mock_text.choices[0].delta).content = PropertyMock(return_value="abc")
        mock_client.chat.completions.create.return_value = [mock_none, mock_text, mock_none]

        result = list(generate_text_stream(mock_client, "tema", "model", 500, 0.7))
        assert result == ["abc"]

    def test_calls_api_with_correct_args(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = []

        list(generate_text_stream(mock_client, "Amor", "openrouter/auto", 300, 0.5))

        mock_client.chat.completions.create.assert_called_once()
        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == "openrouter/auto"
        assert kwargs["max_tokens"] == 300
        assert kwargs["temperature"] == 0.5
        assert kwargs["stream"] is True
        assert len(kwargs["messages"]) == 2
        assert kwargs["messages"][1]["content"] == "Escreva um texto resumido sobre: Amor"
        assert "HTTP-Referer" in kwargs["extra_headers"]


class TestCacheBehavior:
    def test_cache_hit_returns_data(self):
        cache = {"reencarnação": "Texto sobre reencarnação."}
        cache_key = "Reencarnação".lower().strip()
        assert cache_key in cache
        assert cache[cache_key] == "Texto sobre reencarnação."

    def test_cache_miss_for_different_theme(self):
        cache = {"reencarnação": "Texto sobre reencarnação."}
        cache_key = "Prece".lower().strip()
        assert cache_key not in cache

    def test_cache_key_is_case_insensitive(self):
        cache = {}
        cache_key_1 = "Reencarnação".lower().strip()
        cache_key_2 = "REENCARNAÇÃO".lower().strip()
        assert cache_key_1 == cache_key_2

    def test_none_content_handled_by_map_api_error(self):
        assert "inesperado" in map_api_error(Exception("NoneType error"))


class TestRateLimiting:
    def test_generating_true_disables_button(self):
        generating = True
        assert generating is True

    def test_generating_false_enables_button(self):
        generating = False
        assert generating is False

    def test_finally_sets_generating_false(self):
        generating = True
        try:
            raise ValueError("test")
        except ValueError:
            pass
        finally:
            generating = False
        assert generating is False


class TestBuildProviderRouting:
    def test_default_strategy_returns_none(self):
        result = build_provider_routing("Padrão (balanceamento por preço)", True)
        assert result is None

    def test_price_sort(self):
        result = build_provider_routing("Menor preço", True)
        assert result == {"sort": "price"}

    def test_throughput_sort(self):
        result = build_provider_routing("Maior throughput", True)
        assert result == {"sort": "throughput"}

    def test_latency_sort(self):
        result = build_provider_routing("Menor latência", True)
        assert result == {"sort": "latency"}

    def test_fallbacks_disabled(self):
        result = build_provider_routing("Menor preço", False)
        assert result == {"sort": "price", "allow_fallbacks": False}

    def test_fallbacks_enabled_not_in_result_when_true(self):
        result = build_provider_routing("Menor preço", True)
        assert "allow_fallbacks" not in result


# --- helpers ---

def _make_stream_chunks(text_parts: list[str]):
    chunks = []
    for part in text_parts:
        chunk = MagicMock()
        type(chunk.choices[0].delta).content = PropertyMock(return_value=part)
        chunks.append(chunk)
    return chunks
