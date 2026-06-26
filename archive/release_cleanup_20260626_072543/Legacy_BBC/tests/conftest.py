# tests/conftest.py
import pytest
import os
import shutil
import tempfile
import json

@pytest.fixture
def temp_project():
    """Creates a temporary project directory with BBC structure for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample files
    with open(os.path.join(temp_dir, "sample.py"), "w", encoding="utf-8") as f:
        f.write("def sample_function():\n    return 'hello'\n\nclass SampleClass:\n    pass\n")
        
    # Create .bbc structure
    bbc_dir = os.path.join(temp_dir, ".bbc")
    os.makedirs(bbc_dir, exist_ok=True)
    os.makedirs(os.path.join(bbc_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(bbc_dir, "cache"), exist_ok=True)
    
    # Create a dummy context
    context = {
        "project_skeleton": {
            "root": temp_dir,
            "file_count": 1
        },
        "code_structure": [
            {
                "file": "sample.py",
                "structure": {
                    "classes": ["SampleClass"],
                    "functions": ["sample_function"],
                    "imports": []
                }
            }
        ],
        "metrics": {
            "files_scanned": 1,
            "unified_tokens_used": 100,
            "unified_tokens_saved": 900,
            "unified_savings_pct": 90.0
        },
        "context_fresh": True,
        "enforcement_level": "strict",
        "fail_policy": "fail_closed"
    }
    
    context_path = os.path.join(bbc_dir, "bbc_context.json")
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)
        
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)
