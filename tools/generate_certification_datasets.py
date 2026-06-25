import os
import json

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRATCH_DIR, "../archive/certification_data"))

def create_directory_structure():
    os.makedirs(os.path.join(DATA_DIR, "oda_math"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "wikipedia"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "django_repo"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "mixed_polyglot"), exist_ok=True)
    print(f"[*] Directories created under: {DATA_DIR}")

def generate_oda_math():
    # 1. Scalar edge cases and formula testing
    scalar_content = """# ODA-MATH: Scalar Edge Cases and Mathematical Operations
def evaluate_scalars():
    val1 = 5.0
    val2 = -0.0
    val3 = 1e-15
    val4 = float('nan')
    val5 = float('inf')
    
    # Division by zero boundary
    div_zero = val1 / 0.0
    
    # Multiplications
    mult_neg_zero = val1 * val2
    
    # Underflow/overflow
    underflow = val3 * 1e-320
    overflow = 1e308 * 10.0
    
    return div_zero, mult_neg_zero, underflow, overflow
"""
    with open(os.path.join(DATA_DIR, "oda_math", "scalar_ops.py"), "w", encoding="utf-8") as f:
        f.write(scalar_content)

    # 2. Matrix operations and Singular matrix cases
    matrix_content = """# ODA-MATH: Matrix Operations and Singularities
def matrix_calculations():
    # Full rank matrix A
    A = [
        [1.0, 0.0, 0.0],
        [0.75, 0.15, 0.10],
        [0.70, 0.10, 0.20]
    ]
    
    # Singular matrix B
    B = [
        [1.0, 2.0, 3.0],
        [2.0, 4.0, 6.0],
        [3.0, 6.0, 9.0]
    ]
    
    # Near-singular matrix C (high condition number)
    C = [
        [1.0, 1.0],
        [1.0, 1.0000000001]
    ]
    
    return A, B, C
"""
    with open(os.path.join(DATA_DIR, "oda_math", "matrix_ops.py"), "w", encoding="utf-8") as f:
        f.write(matrix_content)
        
    print("[+] Generated ODA-MATH dataset.")

def generate_wikipedia():
    # 1. Wiki page with backlink references
    wiki_page = """# Wikipedia: Artificial Intelligence
Artificial intelligence (AI) is intelligence demonstrated by machines, unlike natural intelligence.
See also: [[MachineLearning]], [[NeuralNetworks]], and [[DeepLearning]].

## History
The field of AI research was founded at a workshop held on the campus of Dartmouth College during the summer of 1556.

| Year | Event | Details |
|---|---|---|
| 1956 | Dartmouth Workshop | Birth of AI field |
| 1997 | Deep Blue | Beats Kasparov in chess |
| 2016 | AlphaGo | Beats Lee Sedol in Go |

### Future
Ethical guidelines and alignment research are critical.
"""
    with open(os.path.join(DATA_DIR, "wikipedia", "ai_article.md"), "w", encoding="utf-8") as f:
        f.write(wiki_page)

    # 2. Secondary page to form backlink structure
    ml_page = """# Wikipedia: Machine Learning
Machine Learning (ML) is the study of computer algorithms that improve automatically through experience.
It is a subset of [[ArtificialIntelligence]].

## Methods
* Supervised learning
* Unsupervised learning
* Reinforcement learning
"""
    with open(os.path.join(DATA_DIR, "wikipedia", "ml_article.md"), "w", encoding="utf-8") as f:
        f.write(ml_page)
        
    print("[+] Generated Wikipedia dataset.")

def generate_django_repo():
    # 1. Mock views.py containing circular dependency traps
    views_content = """# Django View Controllers
import os
from django.http import JsonResponse
# Traps circular import dynamically
from django_repo.models import UserProfile

def user_view(request):
    users = UserProfile.objects.all()
    data = [{"username": u.username, "is_active": u.is_active} for u in users]
    return JsonResponse({"status": "SUCCESS", "users": data})
"""
    with open(os.path.join(DATA_DIR, "django_repo", "views.py"), "w", encoding="utf-8") as f:
        f.write(views_content)

    # 2. Mock models.py
    models_content = """# Django Models
from django.db import models

class UserProfile(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
"""
    with open(os.path.join(DATA_DIR, "django_repo", "models.py"), "w", encoding="utf-8") as f:
        f.write(models_content)
        
    print("[+] Generated Django dataset.")

def generate_mixed_polyglot():
    # 1. Python runner script
    runner_content = """#!/usr/bin/env python
import os
import sys
import json

def load_settings():
    path = os.path.join(os.path.dirname(__file__), "settings.json")
    if not os.path.exists(path):
        return {"env": "development", "debug": True}
    with open(path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    settings = load_settings()
    print(f"MIXED POLYGLOT RUNNER INITIALIZED. ENV={settings.get('env')}")
"""
    with open(os.path.join(DATA_DIR, "mixed_polyglot", "runner.py"), "w", encoding="utf-8") as f:
        f.write(runner_content)

    # 2. JSON configuration file
    json_settings = {
        "env": "production",
        "debug": False,
        "token_limit": 8192,
        "allowed_hosts": ["localhost", "127.0.0.1", "aos.bbc.local"]
    }
    with open(os.path.join(DATA_DIR, "mixed_polyglot", "settings.json"), "w", encoding="utf-8") as f:
        json.dump(json_settings, f, indent=4)

    # 3. Text log mock file
    log_content = """[2026-06-24T18:00:00Z] [INFO] Sidecar server initialized.
[2026-06-24T18:01:00Z] [DEBUG] Sync process triggered.
[2026-06-24T18:02:00Z] [INFO] Database status check completed. Result=OK.
"""
    with open(os.path.join(DATA_DIR, "mixed_polyglot", "app.log"), "w", encoding="utf-8") as f:
        f.write(log_content)

    # 4. Markdown readme file
    readme_content = """# Mixed Polyglot Mock Repository
This directory simulates a multi-language repo containing Python scripts, json configurations, text logs, and markdown files to test the parser's quantization limits and SimHash indexing correctness.
"""
    with open(os.path.join(DATA_DIR, "mixed_polyglot", "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    print("[+] Generated Mixed Polyglot dataset.")

if __name__ == "__main__":
    print("[*] Generating all Phase 6 Certification Datasets...")
    create_directory_structure()
    generate_oda_math()
    generate_wikipedia()
    generate_django_repo()
    generate_mixed_polyglot()
    print("[*] All datasets generated successfully!")
