from app.analysis_service import analyze_source_file


def test_user_path_reaching_open_creates_path_traversal_candidate():
    result = analyze_source_file(
        "download.py",
        b'''from flask import request

def download():
    name = request.args.get("name")
    path = "/srv/data/" + name
    return open(path).read()
''',
    )

    finding = result["security_analysis"]["candidates"][0]
    assert finding["sink"]["category"] == "filesystem_path_operation"
    assert finding["pack_assessment"]["pack"] == "PATH_TRAVERSAL"
    assert finding["pack_assessment"]["status"] == "PATH_INFLUENCE_CANDIDATE"
    assert finding["standards"]["cwe"] == "CWE-22"
    assert finding["exploitability"]["status"] == "UNVERIFIED"


def test_pathlib_read_is_traced_as_filesystem_sink():
    result = analyze_source_file(
        "download.py",
        b'''from flask import request
from pathlib import Path

def download():
    name = request.args.get("name")
    target = Path("/srv/data") / name
    return target.read_bytes()
''',
    )
    finding = result["security_analysis"]["candidates"][0]
    assert finding["sink"]["target"] == "target.read_bytes"


def test_normalization_and_containment_are_recorded_but_not_runtime_proven():
    result = analyze_source_file(
        "download.py",
        b'''from flask import request
from pathlib import Path

def download():
    name = request.args.get("name")
    target = (Path("/srv/data") / name).resolve()
    if target.is_relative_to(Path("/srv/data")):
        return target.read_bytes()
    return b""
''',
    )
    assert result["security_analysis"]["candidates"] == []
    observation = result["security_analysis"]["non_candidates"][0]
    categories = {
        item["category"] for item in observation["trace"]
        if item["kind"] == "SECURITY_CONTROL"
    }
    assert categories == {"path_normalization", "path_containment_check"}
    assert observation["assessment"]["status"] == (
        "PATH_CONTROL_OBSERVED_UNVERIFIED"
    )
    assert observation["assessment"]["runtime_effectiveness_verified"] is False


def test_flask_path_parameter_reaches_filesystem_sink():
    result = analyze_source_file(
        "download.py",
        b'''from flask import Flask
app = Flask(__name__)
@app.get("/files/<path:name>")
def download(name):
    return open(name).read()
''',
    )
    finding = result["security_analysis"]["candidates"][0]
    assert finding["source"]["category"] == "http_path_input"
    assert finding["sink"]["target"] == "open"
