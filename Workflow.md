Build a desktop application focused on AI-assisted job applications and interview preparation.

Architecture requirements:

* Frontend: React + TypeScript
* Desktop wrapper: Tauri
* Styling: TailwindCSS
* Icons: Bootstrap Icons only
* Backend / AI services: Python
* Design style: extremely minimalist, clean, modern, and professional
* No gradients
* No emojis
* Avoid visual clutter
* Focus on smooth UX and lightweight performance

Core features:

1. Initial User Onboarding Pipeline

* Add a complete onboarding pipeline when the user launches the application for the first time.
* The onboarding flow should allow the user to:

  * Upload an existing CV/resume
  * Or manually describe their:

    * work experience
    * education
    * projects
    * technical skills
    * certifications
    * languages
    * achievements
    * career goals
* The system should parse and structure this information automatically.
* Store all extracted and generated information as persistent long-term context for future generations and RAG retrieval.
* If the user does not have a CV, the application should generate an initial professional CV automatically based on the provided information.
* The generated CV must be editable by the user before saving.
* The onboarding process should feel guided, clean, and intelligent rather than form-heavy.

2. Persistent User Context System

* Create a persistent user profile/context layer.
* The system must continuously maintain structured user context including:

  * experience
  * previous CV versions
  * generated cover letters
  * job preferences
  * skills
  * interview history
  * generated applications
  * AI conversation history
* This context should power:

  * CV generation
  * cover letter generation
  * job matching
  * interview preparation
  * application customization
* Design the architecture so future fine-tuned models can leverage this persistent context efficiently.

3. LLM Integration

* The project must support LLM integration.
* I am currently fine-tuning my own model, but since training is still ongoing, use a placeholder LLM service/interface for now.
* The architecture must be modular so the placeholder can later be replaced easily with the fine-tuned model.
* Continue implementing the Python-side LLM infrastructure and inference pipeline.

4. Embedding + Retrieval System

* Create a complete embedding strategy using:

  * CVs
  * Cover letters
  * User profile data
  * Previous applications
  * Extra uploaded documents
  * Job descriptions
  * Interview conversations
* Design the system with RAG support in mind.
* Use vector search for contextual retrieval.
* The embedding pipeline should be reusable across:

  * job application generation
  * cover letter generation
  * interview preparation
  * personalized recommendations

5. LaTeX Template System

* Create a dedicated templates folder.
* Store both CV and cover letter templates as LaTeX files.
* The LLM should dynamically fill template variables/content.
* The backend should compile LaTeX into PDF automatically after generation.
* The architecture must support multiple template styles later.

6. Dashboard
   Create a dashboard with:

* Total generated applications
* Total submitted applications
* Interview preparation sessions
* Recent activity/history
* Generation timestamps
* Application tracking status
* Statistics overview
* Previously generated CVs and cover letters
* Job application history

If a generated application was submitted to a job offer, it must appear in the dashboard and history system.

7. Interview Preparation Module

* Add an interview preparation section.
* Use RAG-based contextual interview preparation.
* The system should leverage:

  * previous conversations with the AI
  * past interview sessions
  * CV data
  * job descriptions
  * previous applications
* The assistant should adapt interview questions and responses dynamically based on stored context.

8. Application Architecture

* Keep the application lightweight and performant.
* Since this is a desktop app, optimize memory usage carefully.
* Use a modular architecture:

  * frontend
  * backend
  * AI services
  * embedding services
  * template engine
  * persistence/database layer
* The codebase should be production-ready and scalable.

9. UI/UX Requirements

* Extremely minimalist UI
* Dark/light theme support
* Clean spacing and typography
* Tailwind-based design system
* Responsive desktop layout
* Sidebar navigation
* Dashboard-centric workflow
* Smooth transitions but minimal animations
* Professional aesthetic similar to modern developer tools

10. Suggested Technical Stack
    Frontend:

* React
* TypeScript
* TailwindCSS
* Bootstrap Icons
* Zustand or Redux Toolkit
* React Query

Desktop:

* Tauri

Backend:

* Python
* FastAPI

AI / RAG:

* Sentence Transformers
* FAISS or ChromaDB
* LangChain or LlamaIndex (optional modular integration)

Persistence:

* SQLite for local-first architecture

PDF Generation:

* LaTeX engine execution pipeline

The final structure should feel like a modern AI-powered career assistant desktop application optimized for local usage and future integration with a fine-tuned LLM.

11. Job Application Workflow

Add a complete “New Job Application” workflow.

When the user presses “Add New Job”:

* The user can:

  * paste a job description
  * optionally paste the company description
  * optionally add notes about the role

The system should then:

1. Analyze the Job Description

* Extract:

  * required skills
  * technologies
  * responsibilities
  * seniority level
  * keywords
  * soft skills
  * ATS-relevant terms

2. Match Against User Context
   Using the persistent user profile/context:

* compare the job requirements against:

  * user experience
  * projects
  * skills
  * previous roles
  * certifications
  * previous generated CVs
* generate a compatibility score out of 100%
* create a modular scoring system
* the scoring logic must live inside a separate Python file/module because I will later implement the final LLM-based scoring logic myself

Example structure:

* `job_matcher.py`
* `llm_scorer.py`
* `scoring_pipeline.py`

3. Generate Tailored CV

* Automatically generate a tailored CV specifically optimized for the pasted job description
* Use the LaTeX template system
* The generated CV must:

  * emphasize matching skills
  * adapt wording for ATS optimization
  * prioritize relevant projects and experience
* The user must be able to:

  * edit the generated CV
  * regenerate sections
  * save versions
  * export as PDF

4. Generate Tailored Cover Letter
   At the same time as CV generation:

* generate a personalized cover letter in parallel using threads/background tasks
* use the same contextual retrieval pipeline
* tailor the letter specifically to:

  * the company
  * the role
  * the user profile
* allow user modifications before export

5. Parallel Processing

* CV generation and cover letter generation should run concurrently using threads/background workers to improve responsiveness
* The UI must show generation progress/loading states cleanly

6. Job Session Persistence
   After generation:

* save the entire job session into the dashboard/history system including:

  * job description
  * generated CV versions
  * generated cover letters
  * ATS/job match score
  * timestamps
  * user edits
  * application status
  * AI conversation history
* Each job application becomes its own persistent workspace/session

The user must be able to:

* reopen old sessions
* edit them later
* duplicate them
* delete them
* archive them
* continue conversations with the AI

7. Interview Preparation Integration
   If the user gets an interview:

* the saved application session should feed directly into the interview preparation module
* create a dedicated interview preparation RAG pipeline using:

  * job description
  * generated CV
  * generated cover letter
  * previous conversations
  * company information
  * interview history
* generate:

  * mock interview questions
  * technical questions
  * HR questions
  * behavioral questions
  * personalized coaching

The interview RAG system must live inside separate Python modules/files.

Example structure:

* `interview_rag.py`
* `interview_context_builder.py`
* `mock_interviewer.py`

8. Dashboard Integration
   The dashboard should display:

* active applications
* archived applications
* interview-stage applications
* generated documents
* match percentages
* recent AI conversations
* interview preparation sessions
* application timeline/history

The application should feel like a persistent AI-powered career workspace rather than a simple CV generator.

9. Performance & Architecture Notes

* Keep memory usage optimized
* Avoid blocking the UI during AI generation
* Use asynchronous/background processing where possible
* Design for future local LLM inference integration
* Keep all AI modules isolated and modular for future fine-tuned model replacement

The final application should resemble a professional local-first AI career assistant with persistent memory, contextual RAG workflows, and intelligent document generation.
