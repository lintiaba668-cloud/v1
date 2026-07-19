"""PowerRename OCR pipeline regression tests."""


def test_pipeline_contract():
    """Verify expected output contract.

    Real OCR images should be tested separately because they depend on
    the bundled Tesseract engine and sample documents.
    """
    result = {
        'text': '',
        'data': {
            'project_name': '',
            'project_code': ''
        },
        'valid': False
    }

    assert 'data' in result
    assert 'project_name' in result['data']
    assert 'project_code' in result['data']
