# -*- coding: utf-8 -*-

"""Template-field OCR helper tests without invoking Tesseract."""

from PIL import Image

from ocr.template_field_recognizer import TemplateFieldRecognizer


def build_recognizer():
    return TemplateFieldRecognizer(executor=None)


def test_recognizer_creates_debug_directory(tmp_path):
    debug_dir = tmp_path / 'logs' / 'template_ocr'

    TemplateFieldRecognizer(executor=None, debug_dir=debug_dir)

    assert debug_dir.is_dir()


def test_tsv_quote_glyph_does_not_swallow_following_rows(tmp_path):
    tsv = tmp_path / 'quote.tsv'
    tsv.write_text(
        'level\tpage_num\tblock_num\tpar_num\tline_num\t'
        'word_num\tleft\ttop\twidth\theight\tconf\ttext\n'
        '5\t1\t1\t1\t1\t1\t10\t20\t10\t10\t80\t"\n'
        '5\t1\t1\t1\t1\t2\t30\t20\t40\t10\t95\t工程名称\n'
        '5\t1\t1\t1\t1\t3\t80\t20\t40\t10\t95\t项目甲\n',
        encoding='utf-8',
    )

    parsed = build_recognizer()._parse_tsv(tsv)

    assert [item['text'] for item in parsed['items']] == [
        '"',
        '工程名称',
        '项目甲',
    ]


def test_completion_title_is_classified():
    score, report_type = build_recognizer()._score_title(
        '配 网 工程 竣工 验收 报告'
    )

    assert report_type == 'finish'
    assert score >= 20


def test_completion_start_date_label_is_not_a_start_report_signal():
    score, report_type = build_recognizer()._score_title(
        '配网工程竣工验收报告 工程名称 工程编号 '
        '开工日期 实际竣工日期'
    )

    assert report_type == 'finish'
    assert score >= 20


def test_isolated_start_date_label_does_not_classify_as_start():
    score, report_type = build_recognizer()._score_title(
        '收报告 设计单位 施工单位 开工日期'
    )

    assert report_type != 'start'


def test_start_title_is_classified_from_body_anchor():
    score, report_type = build_recognizer()._score_title(
        '配网工程开工报告 我方完成 某工程 项目开工前'
    )

    assert report_type == 'start'
    assert score >= 20


def test_explicit_start_title_outweighs_background_table_labels():
    score, report_type = build_recognizer()._score_title(
        '工程名称 建设单位 设计单位 施工单位 配网工程开工报告'
    )

    assert report_type == 'start'
    assert score >= 24


def test_completion_fields_with_approval_anchor_request_start_retry():
    recognizer = build_recognizer()

    assert recognizer._looks_like_start_fields({
        'project_code_candidates': [],
        'project_name_candidates': [
            '项目开工前各项准备工作开工请审批',
        ],
        'field_texts': [],
    })
    assert not recognizer._looks_like_start_fields({
        'project_code_candidates': ['C5132026Z00M'],
        'project_name_candidates': ['工程名称'],
        'field_texts': [],
    })


def test_orientation_stops_after_strong_upright_title(monkeypatch):
    recognizer = build_recognizer()
    image = Image.new('RGB', (1000, 1600), 'white')
    calls = []

    def analyze(candidate, angle):
        calls.append(angle)
        return {
            'angle': angle,
            'image': candidate,
            'score': 22,
            'report_type': 'start',
        }

    monkeypatch.setattr(recognizer, '_analyze_orientation', analyze)

    result = recognizer._select_orientation(image)

    assert result['angle'] == 0
    assert calls == [0]


def test_orientation_checks_all_angles_when_upright_title_is_weak(
    monkeypatch,
):
    recognizer = build_recognizer()
    image = Image.new('RGB', (1000, 1600), 'white')
    calls = []

    def analyze(candidate, angle):
        calls.append(angle)
        return {
            'angle': angle,
            'image': candidate,
            'score': 3 if angle == 0 else 0,
            'report_type': '',
        }

    monkeypatch.setattr(recognizer, '_analyze_orientation', analyze)

    recognizer._select_orientation(image)

    assert calls == [0, 90, 180, 270]


def test_body_quantity_is_not_accepted_as_project_name():
    recognizer = build_recognizer()
    candidates = recognizer._rank_names([
        '拆除工程量拆除原线路8M水泥杆1根低压电缆20米',
    ])

    assert candidates == []


def test_project_name_field_candidate_is_kept():
    recognizer = build_recognizer()
    candidates = recognizer._rank_names([
        '莆田荔城黄石变10kV黄甲线东埭村#5变分线'
        '#003杆003分界开关新装业扩配套工程',
    ])

    assert candidates
    assert candidates[0].endswith('配套工程')


def test_code_candidates_prefer_full_engineering_number():
    recognizer = build_recognizer()
    candidates = recognizer._code_candidates([
        '工程编号 18132024015F-28',
        '5028225',
    ])

    assert candidates[0] == '18132024015F-28'


def test_lettered_migration_code_is_a_strong_domain_code():
    recognizer = build_recognizer()

    assert recognizer._code_format_score('C5132026Z00M') == 3
    assert recognizer._code_format_score('C5132026Z00Z') == 3


def test_completion_boxes_follow_detected_labels():
    recognizer = build_recognizer()
    image = Image.new('RGB', (1440, 1920), 'white')
    orientation = {
        'items': [
            {
                'text': '工程名称',
                'x': 120,
                'y': 105,
                'w': 115,
                'h': 30,
                'page': '1',
                'block': '1',
                'paragraph': '1',
                'line': '1',
            },
            {
                'text': '工程编号',
                'x': 910,
                'y': 108,
                'w': 120,
                'h': 30,
                'page': '1',
                'block': '1',
                'paragraph': '1',
                'line': '1',
            },
        ],
        'scale': 1.0,
        'title_crop_left': 28,
        'prepared_width': 1382,
        'title_crop_height': 460,
        'prepared_height': 460,
        'image': image,
    }

    name_box, code_box = recognizer._completion_boxes(
        image,
        orientation,
    )

    assert name_box[0] < 280
    assert name_box[2] > 900
    assert code_box[0] < 1080
    assert code_box[2] > 1400
    assert name_box[3] - name_box[1] >= 80


def test_completion_fallback_code_crop_is_wide():
    recognizer = build_recognizer()
    image = Image.new('RGB', (1000, 1600), 'white')
    orientation = {
        'items': [],
        'scale': 1.0,
        'prepared_width': 960,
        'title_crop_height': 384,
        'prepared_height': 384,
        'image': image,
    }

    _, code_box = recognizer._completion_boxes(image, orientation)

    assert code_box[0] <= 660
    assert code_box[2] >= 980


def test_abnormally_wide_code_label_uses_safe_cell_boundary():
    recognizer = build_recognizer()
    image = Image.new('RGB', (1279, 1706), 'white')
    orientation = {
        'items': [],
        'scale': 1.79,
        'title_crop_left': 25,
        'prepared_width': 2200,
        'prepared_height': 733,
        'title_crop_height': 409,
        'image': image,
    }
    code_label = {
        'text': '工程编号',
        'left': 1216,
        'top': 282,
        'width': 581,
        'height': 121,
    }

    recognizer._find_field_label = lambda data, field: (
        code_label if field == 'project_code' else None
    )

    _, code_box = recognizer._completion_boxes(image, orientation)

    assert code_box[0] <= int(image.width * 0.70)


def test_completion_code_failure_retries_tight_upper_cell(
    tmp_path,
    monkeypatch,
):
    recognizer = TemplateFieldRecognizer(
        executor=None,
        debug_dir=tmp_path,
    )
    image = Image.new('RGB', (1000, 500), 'white')
    orientation = {'image': image}
    code_heights = []

    monkeypatch.setattr(
        recognizer,
        '_completion_boxes',
        lambda candidate, data: (
            (100, 50, 650, 150),
            (650, 50, 990, 150),
        ),
    )
    monkeypatch.setattr(
        recognizer,
        '_jpeg_normalize',
        lambda candidate: candidate,
    )

    def run_variants(candidate, psms, languages, **kwargs):
        if languages == 'eng':
            code_heights.append(candidate.height)
            if candidate.height == 50:
                return ['C5132025Z13E']
            return ['noise']
        return ['莆田荔城区某迁改工程']

    monkeypatch.setattr(
        recognizer,
        '_run_field_variants',
        run_variants,
    )

    fields = recognizer._recognize_completion(
        image,
        orientation,
        'sample',
    )

    assert fields['project_code'] == 'C5132025Z13E'
    assert code_heights == [100, 58, 50]


def test_completion_code_retries_extra_tight_upper_cell(
    tmp_path,
    monkeypatch,
):
    recognizer = TemplateFieldRecognizer(
        executor=None,
        debug_dir=tmp_path,
    )
    image = Image.new('RGB', (1000, 500), 'white')
    code_heights = []

    monkeypatch.setattr(
        recognizer,
        '_completion_boxes',
        lambda candidate, data: (
            (100, 50, 650, 150),
            (650, 50, 990, 150),
        ),
    )
    monkeypatch.setattr(
        recognizer,
        '_jpeg_normalize',
        lambda candidate: candidate,
    )

    def run_variants(candidate, psms, languages, **kwargs):
        if languages == 'eng':
            code_heights.append(candidate.height)
            if candidate.height == 30:
                return ['051320252038']
            return ['noise']
        return ['莆田荔城区某迁改工程']

    monkeypatch.setattr(
        recognizer,
        '_run_field_variants',
        run_variants,
    )

    fields = recognizer._recognize_completion(
        image,
        {'image': image},
        'sample',
    )

    assert '051320252038' in fields['project_code_candidates']
    assert code_heights[:4] == [100, 58, 50, 30]


def test_start_body_crop_stops_just_below_approval_row():
    recognizer = build_recognizer()
    image = Image.new('RGB', (1000, 1600), 'white')
    orientation = {
        'items': [],
        'prepared_height': 384,
        'title_crop_height': 384,
        'image': image,
    }

    box = recognizer._start_body_box(image, orientation)

    assert box[0] == 40
    assert box[2] == 970
    assert box[1] <= int(1600 * 0.06)
    assert box[3] == int(1600 * 0.20)


def test_unknown_template_probe_includes_lower_first_row():
    recognizer = build_recognizer()
    image = Image.new('RGB', (1080, 1920), 'white')

    boxes = recognizer._completion_probe_code_boxes(image)

    assert len(boxes) >= 2
    assert any(
        left <= 800 and top <= 250 and right >= 1050 and bottom >= 340
        for left, top, right, bottom in boxes
    )


def test_completion_probe_retries_inside_code_value_cell(monkeypatch):
    recognizer = build_recognizer()
    image = Image.new('RGB', (1000, 1600), 'white')
    widths = []

    def run_variants(candidate, **kwargs):
        widths.append(candidate.width)
        if len(widths) == 1:
            return ['工程编号']
        if len(widths) == 2:
            return ['181320260006-8']
        return ['莆田荔城城厢变某工程']

    monkeypatch.setattr(
        recognizer,
        '_run_field_variants',
        run_variants,
    )

    fields = recognizer._recognize_completion_probe(
        image,
        'sample',
    )

    assert fields['project_code'] == '181320260006-8'
    assert widths[1] < widths[0]


def test_instruction_text_is_not_accepted_as_project_name():
    recognizer = build_recognizer()

    assert recognizer._rank_names([
        '套工程项目开工前的各项',
    ]) == []


def test_long_latin_ocr_noise_is_not_a_strong_project_name():
    recognizer = build_recognizer()
    noisy = (
        'onEEEZIRX220VFEAFI0KVIRSEBR10KVERs1igsns'
        '江边线栏山好变分线直杆迁改工程VIETBE356104'
    )

    assert recognizer._name_score(noisy) < 60


def test_code_candidates_strip_ocr_prefix_noise():
    recognizer = build_recognizer()

    candidates = recognizer._code_candidates([
        'R518132024013H02 BB1132025Z2495',
    ])

    assert '18132024013H02' in candidates
    assert 'B1132025Z2495' in candidates
    assert candidates[0] == '18132024013H02'


def test_code_candidates_prefer_standard_suffix_length():
    candidates = build_recognizer()._code_candidates([
        'BB1132025Z2495 B1132025Z495',
    ])

    assert candidates[0] == 'B1132025Z495'


def test_code_candidates_restore_missing_numeric_hyphen():
    candidates = build_recognizer()._code_candidates([
        '1813202600011',
    ])

    assert candidates[0] == '181320260001-1'


def test_code_candidates_restore_truncated_fixed_domain_prefix():
    candidates = build_recognizer()._code_candidates([
        '32026000N-1',
    ])

    assert '18132026000N-1' in candidates


def test_code_candidates_restore_migration_marker_confusions():
    candidates = build_recognizer()._code_candidates([
        '51320262007',
    ])

    assert 'C5132026Z00Z' in candidates


def test_completion_table_structure_classifies_washed_out_title():
    score, report_type = build_recognizer()._score_title(
        '工程名称 莆田某工程 建设单位 莆田供电公司 '
        '设计单位 某设计公司 施工单位 某工程公司'
    )

    assert report_type == 'finish'
    assert score >= 12


def test_ocr_working_copy_downscales_high_resolution_photo():
    recognizer = build_recognizer()
    image = Image.new('RGB', (3072, 4096), 'white')

    working = recognizer._ocr_working_copy(image)

    assert working.size == (2200, 2933)
    assert image.size == (3072, 4096)


def test_ocr_working_copy_keeps_small_photo():
    recognizer = build_recognizer()
    image = Image.new('RGB', (1080, 1920), 'white')

    working = recognizer._ocr_working_copy(image)

    assert working is image


def test_prepare_image_supports_accuracy_retry_width():
    recognizer = build_recognizer()
    image = Image.new('RGB', (2800, 600), 'white')

    prepared, scale = recognizer._prepare_image(
        image,
        max_width=3200,
    )

    assert prepared.size == (3200, 686)
    assert scale > 1.0


def test_fast_start_mode_skips_high_resolution_retry(monkeypatch):
    recognizer = build_recognizer()
    image = Image.new('RGB', (1000, 1600), 'white')
    retry_calls = []

    monkeypatch.setattr(
        recognizer,
        '_run_field_variants',
        lambda *args, **kwargs: ['无法提取工程名称'],
    )
    monkeypatch.setattr(
        recognizer,
        '_recognize_start_high_resolution',
        lambda *args, **kwargs: retry_calls.append(True),
    )

    fields = recognizer._recognize_start(
        image,
        {
            'text': '配网工程开工报告',
            'items': [],
            'prepared_height': 384,
            'title_crop_height': 384,
            'image': image,
        },
        'sample',
        retry_image=image,
        accuracy_mode=False,
    )

    assert not retry_calls
    assert not fields['project_name_candidates']


def test_deep_start_retry_does_not_accept_only_second_wrapped_line(
    monkeypatch,
    tmp_path,
):
    recognizer = TemplateFieldRecognizer(
        executor=None,
        debug_dir=tmp_path,
    )
    image = Image.new('RGB', (3000, 4000), 'white')
    full_name = (
        '莆田荔城区220kV上庄变10kV埕宝I路'
        '(10kV中宝I路)#35杆、10kV江边线栏山'
        '#7变分线#3杆迁改工程'
    )
    results = iter([
        [
            '我方完成江边线栏山#7变分线#3杆迁改工程\n'
            '项目开工前的各项准备工作'
        ],
        [
            '莆田荔城区220kV上庄变10kV埕宝Ⅰ路'
            '（10kV中宝Ⅰ路）#35杆、10kV\n'
            '江边线栏山#7变分线#3杆迁改工程'
        ],
    ])

    monkeypatch.setattr(
        recognizer,
        '_run_field_variants',
        lambda *args, **kwargs: next(results),
    )

    fields = recognizer._recognize_start_high_resolution(
        image,
        'wrapped',
    )

    assert full_name in fields['project_name_candidates']


def test_completion_accuracy_retry_reads_original_top_rows(
    monkeypatch,
    tmp_path,
):
    recognizer = TemplateFieldRecognizer(
        executor=None,
        debug_dir=tmp_path,
    )
    image = Image.new('RGB', (3000, 4000), 'white')
    widths = []

    def run_variants(candidate, languages, **kwargs):
        widths.append(kwargs.get('max_width'))
        if languages == 'eng':
            return ['18132026000N-1']
        return [
            '工程名称\n莆田荔城中心变10kV金桥线'
            '擢英中学环网柜新建业扩配套工程\n工程编号'
        ]

    monkeypatch.setattr(
        recognizer,
        '_run_field_variants',
        run_variants,
    )

    fields = recognizer._recognize_completion_high_resolution(
        image,
        'sample',
    )

    assert fields['project_code'] == '18132026000N-1'
    assert '擢英中学' in fields['project_name']
    assert widths == [3600, 3600]


def test_field_variants_stop_after_reliable_first_result(monkeypatch):
    recognizer = build_recognizer()
    image = Image.new('RGB', (800, 200), 'white')
    calls = []

    monkeypatch.setattr(
        recognizer,
        '_prepare_image',
        lambda candidate, binary=False: (candidate, 1.0),
    )

    def ocr_image(candidate, psm, languages, whitelist=''):
        calls.append((psm, languages, whitelist))
        return {'text': 'complete project name', 'items': []}

    monkeypatch.setattr(recognizer, '_ocr_image', ocr_image)

    texts = recognizer._run_field_variants(
        image,
        psms=(6, 11),
        languages='chi_sim+eng',
        include_binary=True,
        stop_when=lambda values: 'complete project name' in values,
    )

    assert texts == ['complete project name']
    assert len(calls) == 1


def test_field_variants_retry_all_variants_when_result_is_uncertain(
    monkeypatch,
):
    recognizer = build_recognizer()
    image = Image.new('RGB', (800, 200), 'white')
    calls = []

    monkeypatch.setattr(
        recognizer,
        '_prepare_image',
        lambda candidate, binary=False: (candidate, 1.0),
    )

    def ocr_image(candidate, psm, languages, whitelist=''):
        calls.append((psm, languages, whitelist))
        return {'text': 'uncertain', 'items': []}

    monkeypatch.setattr(recognizer, '_ocr_image', ocr_image)

    recognizer._run_field_variants(
        image,
        psms=(6, 11),
        languages='chi_sim+eng',
        include_binary=True,
        stop_when=lambda values: False,
    )

    assert len(calls) == 4
