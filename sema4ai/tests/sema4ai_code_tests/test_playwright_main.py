def test_launch_installs_chromium_on_failure(monkeypatch):
    from unittest import mock

    from sema4ai_code.playwright import __playwright__main as playwright_main
    from sema4ai_code.playwright.robocorp_browser import _engines
    from sema4ai_code.playwright.robocorp_browser._engines import BrowserEngine

    # Fails in the first launch and works after the browser is installed.
    launch_playwright = mock.Mock(
        side_effect=[playwright_main.RecordingError("Failed"), None]
    )
    install_browser = mock.Mock()
    monkeypatch.setattr(playwright_main, "launch_playwright", launch_playwright)
    monkeypatch.setattr(_engines, "install_browser", install_browser)

    playwright_main.launch()

    # The recorder is launched without a channel (so, it must be Chromium, not Chrome).
    install_browser.assert_called_once_with(BrowserEngine.CHROMIUM)
    assert launch_playwright.call_count == 2


def test_launch_does_not_install_browser_on_success(monkeypatch):
    from unittest import mock

    from sema4ai_code.playwright import __playwright__main as playwright_main
    from sema4ai_code.playwright.robocorp_browser import _engines

    launch_playwright = mock.Mock()
    install_browser = mock.Mock()
    monkeypatch.setattr(playwright_main, "launch_playwright", launch_playwright)
    monkeypatch.setattr(_engines, "install_browser", install_browser)

    playwright_main.launch()

    install_browser.assert_not_called()
    launch_playwright.assert_called_once()
