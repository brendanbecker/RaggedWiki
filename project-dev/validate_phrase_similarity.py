#!/usr/bin/env python3
"""
Validate phrase similarity for documentation examples.
Compares phrase pairs to determine if they're true paraphrases vs. related-but-distinct concepts.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine

def compute_similarity(model, phrase1, phrase2):
    """Compute cosine similarity between two phrases."""
    embeddings = model.encode([phrase1, phrase2])
    # cosine from scipy returns distance, so we convert to similarity
    similarity = 1 - cosine(embeddings[0], embeddings[1])
    return similarity

def categorize_similarity(score):
    """Categorize similarity score."""
    if score >= 0.85:
        return "TRUE PARAPHRASE"
    elif score >= 0.70:
        return "RELATED CONCEPT"
    else:
        return "DISTINCT CONCEPT"

def explain_score(phrase1, phrase2, score, category):
    """Generate explanation for the similarity score."""
    explanations = {
        "TRUE PARAPHRASE": f"Score {score:.3f} indicates these phrases express the same problem with different wording. They would likely retrieve the same documents.",
        "RELATED CONCEPT": f"Score {score:.3f} indicates semantic relatedness but not identical meaning. These represent related but potentially distinct troubleshooting paths.",
        "DISTINCT CONCEPT": f"Score {score:.3f} indicates these are separate concepts. They describe different problems requiring different solutions."
    }
    return explanations.get(category, "Unknown category")

def main():
    # Load pre-trained sentence embedding model
    # Using 'all-MiniLM-L6-v2' - fast, good quality, commonly used
    print("Loading sentence embedding model (all-MiniLM-L6-v2)...\n")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Define phrase pairs to test
    pairs = [
        # Pair 1: OLD example - should be related but distinct
        ("database timeout", "connection pool exhaustion"),

        # Pair 2: NEW example - should be true paraphrases
        ("Database connection failed", "Unable to reach database"),

        # Additional validation pairs
        ("database connection failed", "cannot connect to database"),
        ("database timeout", "database connection failed"),
        ("connection pool exhausted", "too many database connections"),
    ]

    print("=" * 80)
    print("PHRASE SIMILARITY VALIDATION RESULTS")
    print("=" * 80)
    print()

    for i, (phrase1, phrase2) in enumerate(pairs, 1):
        similarity = compute_similarity(model, phrase1, phrase2)
        category = categorize_similarity(similarity)
        explanation = explain_score(phrase1, phrase2, similarity, category)

        print(f"PAIR {i}:")
        print(f"  Phrase 1: \"{phrase1}\"")
        print(f"  Phrase 2: \"{phrase2}\"")
        print(f"  Cosine Similarity: {similarity:.4f}")
        print(f"  Category: {category}")
        print(f"  Explanation: {explanation}")
        print()

    print("=" * 80)
    print("THRESHOLDS")
    print("=" * 80)
    print("  ≥ 0.85: TRUE PARAPHRASE (same problem, different wording)")
    print("  0.70-0.85: RELATED CONCEPT (semantically related, potentially distinct)")
    print("  < 0.70: DISTINCT CONCEPT (different problems)")
    print()

if __name__ == "__main__":
    main()
