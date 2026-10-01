from app.analysis_service import analyze_source_file


def _analysis(body: str) -> dict:
    source = (
        "from flask import request\nimport subprocess\n\n"
        "def run():\n"
        "    host = request.args.get('host')\n"
        f"    {body}\n"
    )
    return analyze_source_file("route.py", source.encode())


def test_fixed_executable_argument_list_is_not_shell_injection_candidate():
    result = _analysis("subprocess.run(['echo', str(host)], shell=False)")
    assert result["security_analysis"]["candidates"] == []
    item = result["security_analysis"]["non_candidates"][0]
    assert item["assessment"]["status"] == "NON_SHELL_ARGUMENT_FLOW"
    assert item["assessment"]["argument_semantics"] == "UNRESOLVED"


def test_shell_string_remains_candidate():
    result = _analysis("subprocess.run('echo ' + host, shell=True)")
    assert len(result["security_analysis"]["candidates"]) == 1


def test_explicit_shell_executable_remains_candidate():
    result = _analysis("subprocess.run(['sh', '-c', host], shell=False)")
    assert len(result["security_analysis"]["candidates"]) == 1


def test_dynamic_executable_remains_candidate():
    result = _analysis("subprocess.run([host, 'fixed'], shell=False)")
    assert len(result["security_analysis"]["candidates"]) == 1
