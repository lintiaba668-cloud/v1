# -*- coding: utf-8 -*-

"""Mock OCR pipeline tests.

No dependency on real tesseract engine.
"""

from pathlib import Path

from ocr.ocr_engine import OCREngine


def test_tsv_coordinate_parse():
    engine = OCREngine.__new__(OCREngine)

    tsv = """level\tpage_num\tblock_num\tpar_num\tline_num\tleft\ttop\twidth\theight\tconf\ttext
5\t1\t1\t1\t1\t100\t200\t300\t40\t95\t工程名称
5\t1\t1\t1\t2\t100\t250\t120\t40\t90\tABC123
"""

    file = Path("mock_test.tsv")
    try:
        file.write_text(tsv, encoding="utf-8")

        result = engine._parse_tsv(file)

        assert len(result["items"]) == 2
        assert result["items"][0]["text"] == "工程名称"
        assert result["items"][0]["x"] == 100
        assert result["items"][1]["line"] == "2"

    finally:
        if file.exists():
            file.unlink()
