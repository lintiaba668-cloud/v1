# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw

from ocr.document_rectifier import deskew_document


def test_pillow_deskew_levels_horizontal_form_rows():
    source = Image.new('L', (700, 500), 'white')
    draw = ImageDraw.Draw(source)

    for y in (90, 150, 210, 270):
        draw.line((60, y, 640, y), fill=0, width=4)

    tilted = source.rotate(
        3.0,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        fillcolor='white',
    )
    corrected, angle = deskew_document(tilted, max_angle=5.0, step=0.5)

    assert corrected is not tilted
    assert -4.0 <= angle <= -2.0


def test_pillow_deskew_ignores_minor_rotation():
    source = Image.new('L', (700, 500), 'white')
    draw = ImageDraw.Draw(source)

    for y in (90, 150, 210, 270):
        draw.line((60, y, 640, y), fill=0, width=4)

    tilted = source.rotate(
        1.0,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        fillcolor='white',
    )
    corrected, angle = deskew_document(tilted)

    assert corrected is tilted
    assert angle == 0.0
