# Raw CV Integration Guide

This guide shows how to add raw CVs from your Kaggle dataset to the Apply-Agent system and generate semantic embeddings automatically.

## Quick Start

### 1. Load Raw CVs from File

```python
import json
from pathlib import Path
from AI.cv_processor import CVProcessor

# Initialize processor
processor = CVProcessor()

# Load raw CVs (e.g., from Kaggle CSV/JSON)
raw_cvs = [
    "DIRECTOR OF INFORMATION TECHNOLOGY...",
    "SENIOR DATA SCIENTIST...",
    # ... more raw CV texts
]

# Process all CVs
enriched_cvs = []
for raw_cv in raw_cvs:
    enriched = processor.parse_and_process_raw_cv(raw_cv)
    enriched_cvs.append(enriched)

# Save processed CVs with embeddings
with open('processed_cvs.json', 'w') as f:
    json.dump(enriched_cvs, f, indent=2)
```

### 2. Process Kaggle CSV

If your Kaggle dataset has CVs in a CSV column:

```python
import pandas as pd
from AI.cv_processor import CVProcessor

# Load Kaggle dataset
df = pd.read_csv('kaggle_cv_data.csv')

processor = CVProcessor()

# Process each CV
df['embedding_domain'] = df['cv_text'].apply(
    lambda x: processor.parse_and_process_raw_cv(x)['embeddings']['best_domain']
)

df['embedding_confidence'] = df['cv_text'].apply(
    lambda x: processor.parse_and_process_raw_cv(x)['embeddings']['domain_scores'][0][1]
)

# Save with domain classifications
df.to_csv('kaggle_cv_with_embeddings.csv', index=False)
```

### 3. Batch Processing with Progress

```python
from tqdm import tqdm
from AI.cv_processor import CVProcessor
import json

processor = CVProcessor()

# Read raw CVs
with open('raw_cvs.txt', 'r') as f:
    raw_cvs = f.read().split('\n\n')  # Assuming CVs are separated by double newlines

# Process with progress bar
results = []
for raw_cv in tqdm(raw_cvs, desc="Processing CVs"):
    try:
        enriched = processor.parse_and_process_raw_cv(raw_cv)
        results.append({
            'domain': enriched['embeddings']['best_domain'],
            'confidence': enriched['embeddings']['domain_scores'][0][1],
            'scores': dict(enriched['embeddings']['domain_scores']),
            'raw_cv': raw_cv[:200],  # Store snippet for reference
        })
    except Exception as e:
        print(f"Error processing CV: {e}")

# Save results
with open('batch_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

### 4. Via API

```bash
# Using curl for a single CV
curl -X POST http://localhost:8000/parse-raw-cv \
  -H "Content-Type: application/json" \
  -d '{"raw_cv_text": "DIRECTOR OF INFORMATION TECHNOLOGY..."}'

# Using Python requests
import requests

raw_cv = """
DIRECTOR OF INFORMATION TECHNOLOGY

Summary
Experienced IT manager with 15+ years...
"""

response = requests.post(
    'http://localhost:8000/parse-raw-cv',
    json={'raw_cv_text': raw_cv}
)

result = response.json()
print(f"Domain: {result['embeddings']['best_domain']}")
print(f"Confidence: {result['embeddings']['domain_scores'][0][1]:.4f}")
```

## Data Preparation

### Expected CV Format

The parser handles CVs with sections like:

```
[JOB TITLE]

Summary
[Professional overview]

Highlights
[Category]: [Skill items]
[Category]: [Skill items]

Experience
[Job Title]
[Dates]
[Company]
[Location]
[Description]
Selected Accomplishments
[Accomplishment 1]
[Accomplishment 2]

Education
[Degree]: [Field], [Year]
[Institution]
[Location]

Skills
[Comma or newline separated skills]
```

### Common Issues & Fixes

**Issue: Summary not extracted**
- Ensure section header is "Summary" or similar (case-insensitive)
- Verify text follows immediately after header

**Issue: Experience not parsed correctly**
- Check date format matches: "Month Year to Month Year" or "Current"
- Ensure job title is on its own line

**Issue: Skills not extracted**
- Verify skills are in a dedicated "Skills" section
- Check they're comma or newline separated

## Storage Options

### Option 1: JSON File

```python
# Save all processed CVs
with open('processed_cvs.json', 'w') as f:
    json.dump(enriched_cvs, f)

# Load and use
with open('processed_cvs.json', 'r') as f:
    cvs = json.load(f)
```

### Option 2: Database

```python
# Example with MongoDB
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['cv_database']
collection = db['processed_cvs']

# Insert processed CVs
for cv in enriched_cvs:
    collection.insert_one({
        'domain': cv['embeddings']['best_domain'],
        'confidence': cv['embeddings']['domain_scores'][0][1],
        'embedding_vector': cv['embeddings']['vector'],
        'processed_cv': cv
    })

# Query by domain
it_cvs = collection.find({'domain': 'INFORMATION-TECHNOLOGY'})
```

### Option 3: Vector Database

For semantic similarity search:

```python
# Example with Pinecone
import pinecone

# Initialize Pinecone
pinecone.init(api_key="your-api-key", environment="us-west1-gcp")
index = pinecone.Index("cv-embeddings")

# Upsert CV embeddings
for i, cv in enumerate(enriched_cvs):
    vector = cv['embeddings']['vector']
    metadata = {
        'domain': cv['embeddings']['best_domain'],
        'confidence': cv['embeddings']['domain_scores'][0][1],
        'position': cv.get('position', 'Unknown'),
    }
    index.upsert(vectors=[(str(i), vector, metadata)])

# Search for similar CVs
query_vector = enriched_cvs[0]['embeddings']['vector']
results = index.query(query_vector, top_k=5)
```

## Analysis Examples

### Domain Distribution

```python
import json
from collections import Counter

# Load processed CVs
with open('processed_cvs.json', 'r') as f:
    cvs = json.load(f)

# Count domains
domains = [cv['embeddings']['best_domain'] for cv in cvs]
distribution = Counter(domains)

print("Domain Distribution:")
for domain, count in distribution.most_common():
    percentage = (count / len(cvs)) * 100
    print(f"  {domain}: {count} ({percentage:.1f}%)")
```

### Confidence Analysis

```python
import statistics

# Extract confidence scores
confidences = [cv['embeddings']['domain_scores'][0][1] for cv in cvs]

print(f"Confidence Statistics:")
print(f"  Mean: {statistics.mean(confidences):.4f}")
print(f"  Median: {statistics.median(confidences):.4f}")
print(f"  Stdev: {statistics.stdev(confidences):.4f}")
print(f"  Min: {min(confidences):.4f}")
print(f"  Max: {max(confidences):.4f}")

# CVs with low confidence (harder to classify)
low_confidence = [cv for cv in cvs if cv['embeddings']['domain_scores'][0][1] < 0.5]
print(f"\nCVs with confidence < 0.5: {len(low_confidence)}")
```

### Find Similar CVs

```python
import numpy as np

def find_similar_cvs(target_cv, all_cvs, top_k=5):
    """Find CVs similar to target."""
    target_vector = np.array(target_cv['embeddings']['vector'])
    
    similarities = []
    for cv in all_cvs:
        if cv == target_cv:
            continue
        
        cv_vector = np.array(cv['embeddings']['vector'])
        
        # Cosine similarity
        similarity = np.dot(target_vector, cv_vector) / (
            np.linalg.norm(target_vector) * np.linalg.norm(cv_vector)
        )
        
        similarities.append((cv, similarity))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

# Find similar CVs
target = cvs[0]
similar = find_similar_cvs(target, cvs)

print(f"CVs similar to {target['embeddings']['best_domain']}:")
for cv, score in similar:
    print(f"  - {cv['embeddings']['best_domain']}: {score:.4f}")
```

## Performance Tips

1. **Batch Processing**: Process multiple CVs together for better performance
2. **Caching**: Cache embeddings for frequently accessed CVs
3. **Parallel Processing**: Use multiprocessing for large datasets

```python
from multiprocessing import Pool
from AI.cv_processor import CVProcessor

def process_single_cv(raw_cv):
    processor = CVProcessor()
    return processor.parse_and_process_raw_cv(raw_cv)

# Parallel processing
if __name__ == '__main__':
    with Pool(4) as p:
        results = p.map(process_single_cv, raw_cvs)
```

## Testing Your Integration

```python
from AI.test_raw_cv_parser import test_raw_cv_parser, test_section_extraction

# Run tests
test_section_extraction()
test_raw_cv_parser()

print("✓ All tests passed!")
```

## Troubleshooting

- See `/memories/repo/embedding-system.md` for common issues
- Check logs in `parse_raw_cv_example.py` for detailed parsing output
- Run `test_raw_cv_parser.py` to validate parser functionality
