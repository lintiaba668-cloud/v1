# -*- coding: utf-8 -*-

from ui import main_window_v3


def test_open_output_directory_uses_existing_folder(tmp_path):
    opened = []
    output = tmp_path / '输出文件夹'
    output.mkdir()

    result = main_window_v3.open_directory_in_explorer(
        output,
        opener=opened.append,
    )

    assert result == str(output.resolve())
    assert opened == [str(output.resolve())]


def test_open_output_directory_rejects_missing_folder(tmp_path):
    missing = tmp_path / '输出文件夹'

    try:
        main_window_v3.open_directory_in_explorer(
            missing,
            opener=lambda value: None,
        )
    except FileNotFoundError as exc:
        assert str(missing.resolve()) in str(exc)
    else:
        raise AssertionError('missing output directory should be rejected')


def test_default_output_is_named_folder_next_to_source(tmp_path):
    image = tmp_path / 'reports' / 'page.jpg'
    image.parent.mkdir()
    image.write_bytes(b'image')

    output = (
        main_window_v3.MainWindowV3
        ._default_output_dir_for_source(image)
    )

    assert output == (image.parent / '输出文件夹').resolve()


def test_selected_folder_uses_its_own_output_folder(tmp_path):
    source = tmp_path / 'reports'
    source.mkdir()

    output = (
        main_window_v3.MainWindowV3
        ._default_output_dir_for_source(source)
    )

    assert output == (source / '输出文件夹').resolve()


def test_folder_import_excludes_previous_default_outputs(tmp_path):
    source = tmp_path / 'reports'
    original = source / 'input.jpg'
    generated = source / '输出文件夹' / 'renamed.jpg'
    original.parent.mkdir()
    generated.parent.mkdir()
    original.write_bytes(b'input')
    generated.write_bytes(b'output')

    class FakeWindow:
        output_dir = (tmp_path / 'elsewhere').resolve()
        _path_is_inside = staticmethod(
            main_window_v3.MainWindowV3._path_is_inside
        )

    collected = main_window_v3.MainWindowV3._collect_path(
        FakeWindow(),
        source,
    )

    assert collected == [original]
