"""
Name:         assets.py
Description:  Discovers css assets

"""
# ______________________________________________________________________________________________________________________
# Imports
from pathlib import Path

# ______________________________________________________________________________________________________________________

STATIC_DIRECTORY = Path(__file__).resolve().parent / 'static'
CSS_DIRECTORY = STATIC_DIRECTORY / 'css'


def discover_stylesheets() -> tuple[str, ...]:
    core_stylesheets = (
        (CSS_DIRECTORY / 'core').glob('*.css')
    )

    component_stylesheets = sorted(
        (
            *(
                CSS_DIRECTORY / 'layouts'
            ).rglob('*.css'),
            *(
                CSS_DIRECTORY / 'widgets'
            ).rglob('*.css'),
        ),
        key=lambda path: path.as_posix(),
    )

    stylesheets = (
        *core_stylesheets,
        *component_stylesheets,
    )

    for stylesheet in stylesheets:
        if not stylesheet.is_file():
            raise FileNotFoundError(
                f'Treeze stylesheet does not exist: '
                f'{stylesheet}'
            )

    return tuple(
        _static_url(stylesheet)
        for stylesheet in stylesheets
    )


def _static_url(path: Path) -> str:
    relative_path = path.relative_to(
        STATIC_DIRECTORY,
    )

    return f'/static/{relative_path.as_posix()}'