"""
CV processing module for handling semantic embeddings and domain classification.
"""

from typing import Dict, List, Optional
from .domain_embeddings import get_embedding_manager
from .raw_cv_parser import parse_raw_cv
import json


class CVProcessor:
    """Process and enrich CV data with semantic embeddings."""
    
    def __init__(self):
        """Initialize CV processor with embedding manager."""
        self.embedding_manager = get_embedding_manager()
    
    def process_cv(self, cv_data: Dict) -> Dict:
        """
        Process CV data and add semantic embeddings.
        
        Args:
            cv_data: Dictionary containing CV information
            
        Returns:
            Enriched CV data with embeddings and domain classification
        """
        enriched_cv = self.embedding_manager.embed_cv(cv_data)
        return enriched_cv
    
    def batch_process_cvs(self, cv_list: List[Dict]) -> List[Dict]:
        """
        Process multiple CVs at once.
        
        Args:
            cv_list: List of CV data dictionaries
            
        Returns:
            List of enriched CV data
        """
        return [self.process_cv(cv) for cv in cv_list]
    
    def classify_cv_domain(self, cv_summary: str) -> str:
        """
        Classify a CV to its most likely domain.
        
        Args:
            cv_summary: Text summary or description of CV
            
        Returns:
            Predicted domain name
        """
        best_domain, _ = self.embedding_manager.find_best_matching_domain(cv_summary)
        return best_domain
    
    def get_domain_similarity_scores(self, cv_summary: str) -> Dict[str, float]:
        """
        Get similarity scores for all domains.
        
        Args:
            cv_summary: Text summary or description of CV
            
        Returns:
            Dictionary mapping domain names to similarity scores
        """
        scores = self.embedding_manager.find_top_matching_domains(cv_summary, top_k=len(self.embedding_manager.domains))
        return {domain: score for domain, score in scores}
    
    def find_similar_cvs(self, query_cv: Dict, cv_database: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Find CVs similar to a query CV using embeddings.
        
        Args:
            query_cv: Query CV data
            cv_database: List of CV data to search through
            top_k: Number of similar CVs to return
            
        Returns:
            List of similar CVs sorted by similarity
        """
        import numpy as np
        
        if 'embeddings' not in query_cv:
            query_cv = self.process_cv(query_cv)
        
        query_vector = np.array(query_cv['embeddings']['vector'])
        similarities = []
        
        for cv in cv_database:
            if 'embeddings' not in cv:
                cv = self.process_cv(cv)
            
            cv_vector = np.array(cv['embeddings']['vector'])
            
            # Cosine similarity
            similarity = np.dot(query_vector, cv_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(cv_vector)
            )
            
            similarities.append((cv, float(similarity)))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [cv for cv, _ in similarities[:top_k]]
    
    def parse_and_process_raw_cv(self, raw_cv_text: str) -> Dict:
        """
        Parse raw CV text and add semantic embeddings.
        
        Args:
            raw_cv_text: Raw CV text in common format
            
        Returns:
            Enriched CV data with embeddings and domain classification
        """
        # Parse raw CV into structured format
        parsed_cv = parse_raw_cv(raw_cv_text)
        
        # Convert to standard format for embedding
        standard_cv = self._convert_parsed_to_standard(parsed_cv)
        
        # Process with embeddings
        enriched_cv = self.process_cv(standard_cv)
        
        return enriched_cv
    
    def _convert_parsed_to_standard(self, parsed_cv: Dict) -> Dict:
        """
        Convert parsed CV to standard format for embedding.
        
        Args:
            parsed_cv: Parsed CV dictionary from raw_cv_parser
            
        Returns:
            Standard CV dictionary format
        """
        standard_cv = {}
        
        # Add name from title if available
        if 'title' in parsed_cv:
            standard_cv['position'] = parsed_cv['title']
        
        # Add summary
        if 'summary' in parsed_cv:
            standard_cv['summary'] = parsed_cv['summary']
        
        # Extract skills from multiple sources
        all_skills = []
        
        # From highlights section
        if 'highlights' in parsed_cv and isinstance(parsed_cv['highlights'], dict):
            for category, items in parsed_cv['highlights'].items():
                if isinstance(items, list):
                    all_skills.extend(items)
                else:
                    all_skills.append(str(items))
        
        # From skills section
        if 'skills' in parsed_cv:
            if isinstance(parsed_cv['skills'], list):
                all_skills.extend(parsed_cv['skills'])
            else:
                all_skills.append(str(parsed_cv['skills']))
        
        if all_skills:
            standard_cv['skills'] = list(set(all_skills))  # Remove duplicates
        
        # Build experience summary
        experience_parts = []
        if 'experience' in parsed_cv and isinstance(parsed_cv['experience'], list):
            for exp in parsed_cv['experience']:
                if isinstance(exp, dict):
                    if exp.get('title'):
                        experience_parts.append(f"{exp['title']} at {exp.get('company', 'Company')}")
                    if exp.get('description'):
                        experience_parts.append(exp['description'])
                    if exp.get('accomplishments'):
                        experience_parts.append('. '.join(exp['accomplishments'][:3]))
        
        if experience_parts:
            standard_cv['experience'] = ' '.join(experience_parts)
        
        # Build education summary
        education_parts = []
        if 'education' in parsed_cv and isinstance(parsed_cv['education'], list):
            for edu in parsed_cv['education']:
                if isinstance(edu, dict):
                    parts = []
                    if edu.get('degree'):
                        parts.append(edu['degree'])
                    if edu.get('field'):
                        parts.append(f"in {edu['field']}")
                    if edu.get('year'):
                        parts.append(f"({edu['year']})")
                    if edu.get('institution'):
                        parts.append(f"from {edu['institution']}")
                    if parts:
                        education_parts.append(' '.join(parts))
        
        if education_parts:
            standard_cv['education'] = '; '.join(education_parts)
        
        return standard_cv


# Example usage function
def example_usage():
    """Example of how to use the CV processor."""
    processor = CVProcessor()
    
    # Example CV data
    sample_cv = {
        'name': 'John Doe',
        'summary': 'Experienced software engineer with expertise in Python and cloud technologies',
        'skills': ['Python', 'AWS', 'Docker', 'FastAPI', 'Machine Learning'],
        'experience': 'Senior Software Engineer at Tech Company, 5 years experience in backend development'
    }
    
    # Process the CV
    enriched_cv = processor.process_cv(sample_cv)
    
    # Get domain classification
    domain = processor.classify_cv_domain(sample_cv['summary'])
    print(f"Predicted domain: {domain}")
    
    # Get all domain scores
    scores = processor.get_domain_similarity_scores(sample_cv['summary'])
    print("\nTop 5 domain matches:")
    for domain, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {domain}: {score:.4f}")


if __name__ == "__main__":
    example_usage()
