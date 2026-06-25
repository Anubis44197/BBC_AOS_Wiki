import os
import json

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRATCH_DIR, "certification_data")

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

def generate_django():
    # 1. Models file
    models_content = """from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    content = models.TextField()

    def __str__(self) -> str:
        return self.title

    def is_recently_published(self) -> bool:
        from django.utils import timezone
        import datetime
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
"""
    with open(os.path.join(DATA_DIR, "django_repo", "models.py"), "w", encoding="utf-8") as f:
        f.write(models_content)

    # 2. Views file with imports and decorators
    views_content = """from django.shortcuts import render, get_object_split
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from .models import Article

@login_required
def article_detail(request, article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        raise Http404("Article does not exist")
    return render(request, 'articles/detail.html', {'article': article})

def homepage(request):
    latest_articles = Article.objects.order_by('-pub_date')[:5]
    output = ', '.join([q.title for q in latest_articles])
    return HttpResponse(output)
"""
    with open(os.path.join(DATA_DIR, "django_repo", "views.py"), "w", encoding="utf-8") as f:
        f.write(views_content)
        
    print("[+] Generated Django dataset.")

def generate_mixed_polyglot():
    # 1. Python core runner
    runner = """# Mixed Polyglot runner script
import os
import sys
import json

def load_settings(path):
    with open(path, "r") as f:
        return json.load(f)

def run():
    print("Initializing engine...")
    config = load_settings("settings.json")
    print(f"Engine mode: {config.get('mode')}")
    
if __name__ == '__main__':
    run()
"""
    with open(os.path.join(DATA_DIR, "mixed_polyglot", "runner.py"), "w", encoding="utf-8") as f:
        f.write(runner)

    # 2. JSON configuration
    config = {
        "mode": "production",
        "version": "1.0.0",
        "enable_aura": True,
        "max_tokens": 4096,
        "features": ["caching", "indexing", "quantization"]
    }
    with open(os.path.join(DATA_DIR, "mixed_polyglot", "settings.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    # 3. Documentation file
    readme = """# Mixed Polyglot Repository
This repository contains a mix of Python code, JSON settings, and markdown documents.

## Usage
Run the following script to boot:
```bash
python runner.py
```
"""
    with open(os.path.join(DATA_DIR, "mixed_polyglot", "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    # 4. Log telemetry file
    telemetry_log = """2026-06-24 14:10:00 [INFO] Starting mixed polyglot application
2026-06-24 14:10:01 [DEBUG] Reading settings.json config file
2026-06-24 14:10:02 [INFO] Engine initialized in production mode with enable_aura=True
2026-06-24 14:10:03 [WARNING] High memory consumption detected in indexes/hmpu_indexer
2026-06-24 14:10:05 [INFO] Execution completed successfully
"""
    with open(os.path.join(DATA_DIR, "mixed_polyglot", "app.log"), "w", encoding="utf-8") as f:
        f.write(telemetry_log)
        
    print("[+] Generated Mixed Polyglot dataset.")

if __name__ == "__main__":
    create_directory_structure()
    generate_oda_math()
    generate_wikipedia()
    generate_django()
    generate_mixed_polyglot()
    print("[*] Certification dataset generation finished successfully.")
