import zipfile
from pathlib import Path

from unstuk_ml.figures.size_waterfall import (
    MODEL_ENTRY,
    RUNTIME_ENTRY,
    ApkParts,
    apk_parts,
    steps,
)


def test_the_apk_is_split_into_model_runtime_dex_and_the_rest(tmp_path: Path) -> None:
    apk = tmp_path / "app.apk"
    with zipfile.ZipFile(apk, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr(MODEL_ENTRY, b"m" * 3000)
        archive.writestr(RUNTIME_ENTRY, b"r" * 2000)
        archive.writestr("classes.dex", b"d" * 500)
        archive.writestr("classes2.dex", b"d" * 100)
        archive.writestr("res/icon.png", b"i" * 50)

    parts = apk_parts(apk)

    assert (parts.model, parts.runtime, parts.dex) == (3000, 2000, 600)
    assert parts.rest == apk.stat().st_size - 5600


def test_the_changes_add_up_to_the_apk() -> None:
    parts = ApkParts(model=35_000_000, runtime=33_000_000, dex=3_000_000, total=71_500_000)

    chart = steps(134_000_000, parts)

    assert [s.end for s in chart if s.is_total] == [134.0, 35.0, 71.5]
    assert chart[1].start - chart[1].end == 99.0
    assert chart[-2].end == chart[-1].end
