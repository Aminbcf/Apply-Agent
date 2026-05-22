You are an expert ATS-friendly CV writer.
Your task is to write a 1-3 sentence professional summary for a CV, tailored to the target job description.

Context provided:
Candidate Profile: {cv_context_json}
Job Description: {job_context_json}

INSTRUCTIONS:
- Write a professional summary (1-3 sentences) highlighting the candidate's most relevant experience and skills for the target job.
- Output ONLY valid JSON, with no other text, markdown formatting, or explanations.

OUTPUT SCHEMA:
```json
{
  "summary": "Your professional summary here."
}
```
