"""File naming and source-preservation tests."""

from core.rename import build_filename, rename_file


def test_start_report_filename():
    assert build_filename('福建莆田某台区治理工程', '', '.jpg') == (
        '福建莆田某台区治理工程.jpg'
    )


def test_finish_report_filename_uses_separator():
    assert build_filename(
        '福建莆田某台区治理工程',
        '1813202400YP04',
        '.JPG'
    ) == '福建莆田某台区治理工程_1813202400YP04.jpg'


def test_rename_copies_and_preserves_source(tmp_path):
    source = tmp_path / 'input.jpg'
    source.write_bytes(b'image-data')
    output = tmp_path / 'output'

    first = rename_file(
        source,
        output,
        '测试工程',
        'ABC123456'
    )
    second = rename_file(
        source,
        output,
        '测试工程',
        'ABC123456'
    )

    assert source.exists()
    assert first.name == '测试工程_ABC123456.jpg'
    assert second.name == '测试工程_ABC123456_2.jpg'
    assert first.read_bytes() == b'image-data'
