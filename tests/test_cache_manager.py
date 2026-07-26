# -*- coding: utf-8 -*-

from core.cache_manager import clear_runtime_cache


def test_cache_cleanup_removes_only_generated_cache(tmp_path):
    crop = tmp_path / 'logs' / 'template_ocr' / 'crop.jpg'
    extracted = tmp_path / 'temp' / 'imported' / 'zip_1' / 'page.jpg'
    log = tmp_path / 'logs' / 'PowerRename.log'
    output = tmp_path / 'output' / 'result.jpg'

    for path in (crop, extracted, log, output):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'1234')

    summary = clear_runtime_cache(base_path=tmp_path)

    assert summary['files_removed'] == 2
    assert summary['bytes_removed'] == 8
    assert not crop.exists()
    assert not extracted.exists()
    assert log.exists()
    assert output.exists()


def test_cache_cleanup_preserves_active_zip_import(tmp_path):
    active = tmp_path / 'temp' / 'imported' / 'zip_1' / 'page.jpg'
    active.parent.mkdir(parents=True)
    active.write_bytes(b'image')

    summary = clear_runtime_cache(
        base_path=tmp_path,
        protected_paths=[active],
    )

    assert active.exists()
    assert summary['files_removed'] == 0
    assert summary['skipped'] == [
        str((tmp_path / 'temp' / 'imported').resolve())
    ]
