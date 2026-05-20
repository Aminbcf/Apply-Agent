"""
Demo script to test semantic embeddings with CV examples.
Run this to see the system in action.
"""

import json
import sys
from pathlib import Path

# Add the backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from AI.cv_processor import CVProcessor
from AI.domain_embeddings import get_embedding_manager, DOMAINS


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_embeddings():
    """Demo 1: Basic domain embeddings."""
    print_header("Demo 1: Domain Embeddings")
    
    manager = get_embedding_manager()
    print(f"\nAvailable domains ({len(DOMAINS)} total):")
    for i, domain in enumerate(DOMAINS, 1):
        print(f"  {i:2d}. {domain}")
    
    print("\nDomain embeddings generated (384-dimensional vectors)")
    embeddings = manager.get_all_domain_embeddings()
    print(f"Embedding dimensions: {len(embeddings['HR'])}")


def demo_cv_classification():
    """Demo 2: CV classification."""
    print_header("Demo 2: CV Classification")
    
    processor = CVProcessor()
    manager = get_embedding_manager()
    
    # Load sample CVs
    cv_examples_path = Path(__file__).parent / "CV-Examples" / "cv_examples.json"
    with open(cv_examples_path, 'r') as f:
        data = json.load(f)
    
    print("\nClassifying sample CVs:\n")
    for cv in data['cv_examples'][:3]:
        # Create text summary
        text = cv['summary']
        if cv['skills']:
            text += " " + " ".join(cv['skills'])
        
        # Classify
        domain, score = manager.find_best_matching_domain(text)
        
        print(f"Name: {cv['name']}")
        print(f"  Expected domain: {cv['domain']}")
        print(f"  Predicted domain: {domain}")
        print(f"  Confidence: {score:.4f}")
        print()


def demo_domain_scoring():
    """Demo 3: Full domain scoring."""
    print_header("Demo 3: Domain Similarity Scoring")
    
    processor = CVProcessor()
    
    # Sample CV summary
    text = "Experienced software engineer with 8+ years in cloud infrastructure, Python, AWS, and Kubernetes"
    
    print(f"\nInput text: {text}\n")
    
    scores = processor.get_domain_similarity_scores(text)
    print("Top 10 matching domains:\n")
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for i, (domain, score) in enumerate(sorted_scores[:10], 1):
        bar_length = int(score * 40)
        bar = "█" * bar_length
        print(f"{i:2d}. {domain:25s} {score:.4f}  {bar}")


def demo_cv_processing():
    """Demo 4: Full CV processing."""
    print_header("Demo 4: Complete CV Processing")
    
    processor = CVProcessor()
    
    sample_cv = {
        'name': 'Alice Thompson',
        'summary': 'Data scientist and ML engineer with expertise in deep learning and production deployment',
        'skills': ['Python', 'TensorFlow', 'PyTorch', 'scikit-learn', 'AWS SageMaker', 'SQL'],
        'experience': 'Senior ML Engineer at TechCorp (2019-Present) - Built ML pipelines. Data Scientist at DataCo (2016-2019)',
        'education': 'M.S. Computer Science (ML focus), Stanford University'
    }
    
    print(f"\nProcessing CV for: {sample_cv['name']}\n")
    
    enriched_cv = processor.process_cv(sample_cv)
    
    print(f"Best matching domain: {enriched_cv['embeddings']['best_domain']}")
    print(f"\nTop 5 domain matches:")
    for i, (domain, score) in enumerate(enriched_cv['embeddings']['domain_scores'], 1):
        print(f"  {i}. {domain:25s} {score:.4f}")
    
    print(f"\nEmbedding vector dimensions: {len(enriched_cv['embeddings']['vector'])}")
    print(f"Sample embedding values: {enriched_cv['embeddings']['vector'][:5]}")


def demo_comparison():
    """Demo 5: Compare different job profiles."""
    print_header("Demo 5: Comparing Different Professional Profiles")
    
    manager = get_embedding_manager()
    
    profiles = {
        'Software Engineer': 'Full-stack developer with Python, JavaScript, and cloud expertise using AWS and Docker',
        'Data Scientist': 'Machine learning specialist focusing on statistical analysis, Python, and deep learning models',
        'Product Manager': 'Strategic thinker focused on user needs, market analysis, and cross-functional collaboration',
        'Graphic Designer': 'Creative professional specializing in visual design, branding, and user interface design',
        'Financial Analyst': 'Quantitative analyst with experience in risk management, portfolio analysis, and financial modeling'
    }
    
    print("\nDomain classifications for different profiles:\n")
    
    for profile_name, profile_text in profiles.items():
        domain, score = manager.find_best_matching_domain(profile_text)
        print(f"{profile_name:20s} → {domain:25s} (confidence: {score:.4f})")


def demo_embedding_similarity():
    """Demo 6: Embedding similarity comparison."""
    print_header("Demo 6: Text Similarity via Embeddings")
    
    import numpy as np
    manager = get_embedding_manager()
    
    texts = [
        "Python developer building web applications",
        "JavaScript engineer creating web applications",
        "Accountant managing financial records",
        "Data analyst processing financial data"
    ]
    
    print(f"\nComputing similarity between {len(texts)} text samples:\n")
    
    embeddings = [manager.embed_text(text) for text in texts]
    
    for i, text in enumerate(texts):
        print(f"{i+1}. {text}")
    
    print("\nSimilarity matrix (cosine similarity):\n")
    print("    ", end="")
    for i in range(len(texts)):
        print(f"  {i+1}", end="")
    print()
    
    for i, emb1 in enumerate(embeddings):
        print(f"{i+1}. ", end="")
        for j, emb2 in enumerate(embeddings):
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            print(f" {similarity:.2f}", end="")
        print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  SEMANTIC EMBEDDING SYSTEM FOR CV EXAMPLES".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        demo_basic_embeddings()
        demo_cv_classification()
        demo_domain_scoring()
        demo_cv_processing()
        demo_comparison()
        demo_embedding_similarity()
        
        print_header("Demo Complete!")
        print("\nAll demonstrations completed successfully!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run the API: uvicorn main:app --reload")
        print("  3. Visit http://localhost:8000/docs for interactive API docs")
        
    except Exception as e:
        import logging
        logging.basicConfig(level=logging.ERROR)
        logging.error("Error during demo: %s", e, exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
