from pathlib import Path

_DEFAULT_LOGO_PATH = Path("assets") / "logo" / "logo.png"


def get_logo_path() -> Path:
    """Return the default GPDI logo path."""
    return _DEFAULT_LOGO_PATH


def has_logo() -> bool:
    """Return True if the default GPDI logo exists."""
    return _DEFAULT_LOGO_PATH.exists()


def get_branding_settings() -> dict[str, object]:
    """Return default branding settings for document exports."""
    return {
        "include_logo": True,
        "company_name": "Global Prospectus Development Institute",
    }
