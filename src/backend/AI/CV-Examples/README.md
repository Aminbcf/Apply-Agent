# Semantic Embedding System for CV Examples

This system provides semantic embeddings for CV examples based on 24 professional domains from a Kaggle dataset.

## Features

- **Domain Classification**: Automatically classify CVs to their best matching professional domain
- **Semantic Embeddings**: Generate dense vector embeddings for CV content
- **Domain Similarity Scoring**: Get similarity scores for all domains
- **CV Similarity Search**: Find similar CVs based on semantic embeddings

## Supported Domains

```
HR, DESIGNER, INFORMATION-TECHNOLOGY, TEACHER, ADVOCATE,
BUSINESS-DEVELOPMENT, HEALTHCARE, FITNESS, AGRICULTURE,
BPO, SALES, CONSULTANT, DIGITAL-MEDIA, AUTOMOBILE,
CHEF, FINANCE, APPAREL, ENGINEERING, ACCOUNTANT,
CONSTRUCTION, PUBLIC-RELATIONS, BANKING, ARTS, AVIATION
```

## Architecture

### Components

1. **domain_embeddings.py** - Core embedding generation
   - `DomainEmbeddingManager`: Manages embeddings for all domains
   - Generates embeddings using sentence-transformers
   - Provides similarity computation

2. **cv_processor.py** - CV processing and classification
   - `CVProcessor`: High-level API for CV processing
   - Batch processing capabilities
   - Domain classification and similarity scoring

### Embedding Model

Uses `all-MiniLM-L6-v2` model from sentence-transformers:
- Lightweight (~22MB)
- Fast inference
- Good semantic understanding
- Can be swapped for `all-mpnet-base-v2` for better accuracy

## API Endpoints

### GET `/health`
Health check endpoint

### GET `/domains`
Get all available job domains
```json
{
  "domains": ["HR", "DESIGNER", "INFORMATION-TECHNOLOGY", ...]
}
```

### GET `/domain-embeddings`
Get semantic embeddings for all domains
```json
{
  "HR": [0.1234, -0.5678, ...],
  "DESIGNER": [0.9012, -0.3456, ...],
  ...
}
```

### POST `/process-cv`
Process a CV and add semantic embeddings
```json
{
  "name": "John Doe",
  "summary": "Software engineer with AI expertise",
  "skills": ["Python", "TensorFlow", "PyTorch"],
  "experience": "Senior ML Engineer",
  "education": "BS Computer Science"
}
```

Response includes:
- Original CV data
- Embedding vector
- Best matching domain
- Top 5 domain scores with similarity values

### POST `/classify-cv-domain`
Classify CV to its best matching domain
```json
{
  "summary": "Experienced cloud architect...",
  "skills": ["AWS", "Kubernetes", "Docker"],
  ...
}
```

Response:
```json
{
  "domain": "INFORMATION-TECHNOLOGY",
  "confidence": 0.8234
}
```

### POST `/cv-domain-scores`
Get similarity scores for all domains
```json
{
  "domain_scores": [
    ["INFORMATION-TECHNOLOGY", 0.8234],
    ["BUSINESS-DEVELOPMENT", 0.6123],
    ...
  ]
}
```

### POST `/parse-raw-cv`
Parse raw CV text and convert to structured format with embeddings

Raw CVs can be in common formats with sections like:
- Summary/Overview
- Highlights/Key Skills
- Experience/Work History
- Education
- Skills

Input:
```json
{
  "raw_cv_text": "DIRECTOR OF INFORMATION TECHNOLOGY\n\nSummary\n... (raw CV text) ..."
}
```

Response:
```json
{
  "position": "DIRECTOR OF INFORMATION TECHNOLOGY",
  "summary": "...",
  "skills": [...],
  "experience": "...",
  "education": "...",
  "embeddings": {
    "vector": [...],
    "best_domain": "INFORMATION-TECHNOLOGY",
    "domain_scores": [["INFORMATION-TECHNOLOGY", 0.8234], ...]
  }
}
```

## Raw CV Support

The system includes a powerful parser for converting raw CVs in common formats into structured data with semantic embeddings.

### Supported Sections

The parser automatically identifies and extracts:

1. **Position/Title** - Job title or professional headline
2. **Summary** - Professional overview and key attributes
3. **Highlights** - Categorized technical skills (e.g., OS/Platforms, Networking, Tools)
4. **Experience** - Job positions with dates, companies, descriptions, and accomplishments
5. **Education** - Degrees, fields of study, institutions, and graduation years
6. **Skills** - Comma or newline-separated list of skills and competencies

### Example Usage

#### Python

```python
from AI.raw_cv_parser import parse_raw_cv
from AI.cv_processor import CVProcessor

# Read raw CV text
with open('resume.txt', 'r') as f:
    raw_cv = f.read()

# Parse and enrich with embeddings
processor = CVProcessor()
enriched_cv = processor.parse_and_process_raw_cv(raw_cv)

print(f"Detected domain: {enriched_cv['embeddings']['best_domain']}")
print(f"Domain confidence: {enriched_cv['embeddings']['domain_scores'][0][1]:.4f}")
```

#### API

```bash
# With curl
curl -X POST http://localhost:8000/parse-raw-cv \
  -H "Content-Type: application/json" \
  -d '{
    "raw_cv_text": "DIRECTOR OF INFORMATION TECHNOLOGY\n\nSummary\n..."
  }'
```

#### Example Raw CV Format

```
DIRECTOR OF INFORMATION TECHNOLOGY AND ANALYTICS

Summary
Accomplished senior manager with 15+ years leading enterprise technology initiatives...

Highlights
OS/Platforms:
Windows Server 2008/2012, Exchange 2010, Active Directory

Networking:
Cisco LAN/WAN, TCP/IP, VPN, VoIP

Experience
Director of Information Technology
January 2005 to Current
Global Asset Management Firm
New York, NY

Directed world-wide IT strategy and managed team of 6...

Selected Accomplishments
- Led deployment of virtual computing environment
- Established disaster recovery strategy
- Spearheaded VOIP conversion

Education
Bachelor of Science: Computer Science, 1998
Rutgers University
New Jersey

Skills
Active Directory, Cisco, Windows Server, Project Management, Leadership
```

## Usage Examples

### Python Usage

```python
from AI.cv_processor import CVProcessor
from AI.domain_embeddings import get_embedding_manager

# Initialize
processor = CVProcessor()
embedding_manager = get_embedding_manager()

# Process a CV
cv_data = {
    'summary': 'Software engineer with ML expertise',
    'skills': ['Python', 'TensorFlow', 'AWS'],
    'experience': 'Senior ML Engineer at Tech Corp'
}

enriched_cv = processor.process_cv(cv_data)
print(f"Best domain: {enriched_cv['embeddings']['best_domain']}")

# Classify CV
domain = processor.classify_cv_domain(cv_data['summary'])
print(f"Classified as: {domain}")

# Get domain scores
scores = processor.get_domain_similarity_scores(cv_data['summary'])
print("Top domains:")
for domain, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {domain}: {score:.4f}")

# Find similar CVs
similar_cvs = processor.find_similar_cvs(cv_data, cv_database, top_k=5)
```

### API Usage

```bash
# Get all domains
curl http://localhost:8000/domains

# Get domain embeddings
curl http://localhost:8000/domain-embeddings

# Process CV
curl -X POST http://localhost:8000/process-cv \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "summary": "Software engineer",
    "skills": ["Python", "AWS"],
    "experience": "5 years in backend development"
  }'

# Classify CV domain
curl -X POST http://localhost:8000/classify-cv-domain \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Full-stack developer with React expertise",
    "skills": ["JavaScript", "React", "Node.js"]
  }'

# Get domain scores
curl -X POST http://localhost:8000/cv-domain-scores \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Experienced data scientist",
    "skills": ["Python", "Machine Learning", "Statistics"]
  }'
```

## Performance Considerations

- **First load**: ~500ms (loads sentence-transformers model)
- **Per CV embedding**: ~50-100ms
- **Domain embedding lookup**: <1ms (pre-computed)
- **Similarity computation**: Very fast (vector operations)

## Customization

### Changing Embedding Model

Edit `domain_embeddings.py`:
```python
DomainEmbeddingManager(model_name="all-mpnet-base-v2")  # More accurate, slower
```

Available models:
- `all-MiniLM-L6-v2` - Fast, lightweight (default)
- `all-mpnet-base-v2` - High accuracy, slower
- `distiluse-base-multilingual-cased-v2` - Multilingual support
- See [sentence-transformers](https://www.sbert.net/docs/pretrained_models.html) for more

### Adding New Domains

Edit `domain_embeddings.py`:
```python
DOMAINS = [
    'HR', 'DESIGNER', ...,
    'YOUR_NEW_DOMAIN'  # Add here
]
```

The embeddings will be automatically regenerated when the manager is reinitialized.

## Dependencies

- `sentence-transformers` - Semantic embeddings
- `numpy` - Vector operations
- `torch` - Deep learning framework
- `fastapi` - API framework
- `pandas` - Data processing (optional)

## Future Enhancements

- [ ] Caching of embeddings to database
- [ ] Fine-tuning embedding model on domain-specific data
- [ ] Multi-language support
- [ ] Hybrid search combining keyword and semantic search
- [ ] Visualization of CV similarity space
- [ ] Real-time streaming processing
- [ ] Support for PDF and DOCX file formats
- [ ] Enhanced OCR for scanned CV documents
