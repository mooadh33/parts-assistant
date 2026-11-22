import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

UI = Path(__file__).resolve().parent.parent / "ui" / "streamlit_app.py"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_login_page_renders_in_both_themes(theme):
    at = AppTest.from_file(str(UI), default_timeout=30)
    at.query_params["theme"] = theme
    at.run()
    assert not at.exception
    assert at.session_state["ui_theme"] == theme


def test_theme_toggle_flips():
    at = AppTest.from_file(str(UI), default_timeout=30).run()
    at.button(key="themelogin").click().run()
    assert at.session_state["ui_theme"] == "dark" and not at.exception
