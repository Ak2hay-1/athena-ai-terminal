from app.ai.response_parser import response_parser


def test_response_parser_valid_json():
    payload = '{"signal":"HOLD","confidence":50,"reason":["ok"]}'
    result = response_parser.parse(payload)
    assert result.signal.value == "HOLD"
    assert result.confidence == 50


def test_response_parser_markdown_json():
    payload = '```json\n{"signal":"BUY","confidence":80,"reason":["trend"]}\n```'
    result = response_parser.parse(payload)
    assert result.signal.value == "BUY"
    assert result.confidence == 80


def test_response_parser_invalid_fallback():
    result = response_parser.parse("not-json")
    assert result.signal.value == "HOLD"
    assert result.confidence == 0


def test_response_parser_trailing_comma_repair():
    payload = """{
    "signal":"HOLD",
    "confidence":40,
    "reason":["Sideways market","No clear breakout"],
}"""
    result = response_parser.parse(payload)
    assert result.signal.value == "HOLD"
    assert result.confidence == 40


def test_response_parser_prose_wrapper():
    payload = 'Here you go:\n{"signal":"SELL","confidence":70,"reason":["breakdown"]}\nThanks'
    result = response_parser.parse(payload)
    assert result.signal.value == "SELL"
    assert result.confidence == 70
