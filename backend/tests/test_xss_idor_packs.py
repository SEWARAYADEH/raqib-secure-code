from app.analysis_service import analyze_source_file


def test_javascript_input_reaching_html_sink_creates_xss_candidate():
    result = analyze_source_file(
        "route.js",
        b'''function render(req, res) {
  const name = req.query.name;
  res.send(name);
}
''',
    )
    finding = result["security_analysis"]["candidates"][0]
    assert finding["sink"]["category"] == "html_dom_rendering"
    assert finding["pack_assessment"]["pack"] == "XSS"
    assert finding["pack_assessment"]["status"] == "UNENCODED_HTML_OUTPUT_CANDIDATE"
    assert finding["standards"]["cwe"] == "CWE-79"
    assert finding["exploitability"]["status"] == "UNVERIFIED"


def test_dom_purify_path_is_retained_as_unverified_non_candidate():
    result = analyze_source_file(
        "route.js",
        b'''function render(req, res) {
  const name = req.query.name;
  const safe = DOMPurify.sanitize(name);
  res.send(safe);
}
''',
    )
    assert result["security_analysis"]["candidates"] == []
    observation = result["security_analysis"]["non_candidates"][0]
    assert observation["assessment"]["status"] == "OUTPUT_CONTROL_OBSERVED_UNVERIFIED"


def test_python_raw_template_string_creates_xss_candidate():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request, render_template_string
def render():
    name = request.args.get("name")
    return render_template_string(name)
''',
    )
    finding = result["security_analysis"]["candidates"][0]
    assert finding["pack_assessment"]["pack"] == "XSS"


def test_resource_identifier_lookup_without_guard_creates_idor_candidate():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request
def detail():
    object_id = request.args.get("id")
    return Document.query.get(object_id)
''',
    )
    finding = result["security_analysis"]["candidates"][0]
    assert finding["sink"]["category"] == "authorization_sensitive_object_access"
    assert finding["pack_assessment"]["pack"] == "BROKEN_AUTHORIZATION_IDOR"
    assert finding["pack_assessment"]["status"] == (
        "OBJECT_ACCESS_WITHOUT_OBSERVED_AUTHORIZATION_CONTROL"
    )
    assert finding["standards"]["cwe"] == "CWE-639"
    assert finding["exploitability"]["status"] == "UNVERIFIED"


def test_ownership_guard_keeps_idor_flow_as_unverified_non_candidate():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request, abort
def detail(user_id):
    object_id = request.args.get("id")
    if user_id != current_user.id:
        abort(403)
    return Document.query.get(object_id)
''',
    )
    assert result["security_analysis"]["candidates"] == []
    observation = result["security_analysis"]["non_candidates"][0]
    assert observation["assessment"]["status"] == (
        "AUTHORIZATION_CONTROL_OBSERVED_UNVERIFIED"
    )
