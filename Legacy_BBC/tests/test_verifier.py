# tests/test_verifier.py
import os
import pytest
from bbc_core.verifier import BBCVerifier

def test_verifier_load(temp_project):
    recipe_path = os.path.join(temp_project, ".bbc", "bbc_context.json")
    verifier = BBCVerifier(recipe_path)
    assert verifier.project_root == temp_project

def test_verifier_syntax_clean(temp_project):
    recipe_path = os.path.join(temp_project, ".bbc", "bbc_context.json")
    verifier = BBCVerifier(recipe_path)
    errors = verifier.verify_syntax_only()
    assert len(errors) == 0

def test_verifier_syntax_error(temp_project):
    # Introduce syntax error
    with open(os.path.join(temp_project, "sample.py"), "a", encoding="utf-8") as f:
        f.write("\nthis is a syntax error { \n")
        
    recipe_path = os.path.join(temp_project, ".bbc", "bbc_context.json")
    verifier = BBCVerifier(recipe_path)
    errors = verifier.verify_syntax_only()
    assert len(errors) > 0
    assert any("sample.py" in err["file"] for err in errors)

def test_verifier_full_report(temp_project):
    recipe_path = os.path.join(temp_project, ".bbc", "bbc_context.json")
    verifier = BBCVerifier(recipe_path)
    report = verifier.verify_full()
    
    assert "aura_field" in report
    assert report["syntax_error_count"] == 0
    assert report["freshness"]["context_fresh"] is True
