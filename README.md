# Job Search Automation V1

## Scope
Automatically collect remote jobs from:
1. LinkedIn public job listings
2. EU Remote Jobs

Then:
- classify each job into one of four role families;
- accept title variations (for example `Product Manager`, `AI-Native Product Manager`, `GenAI Engineer`);
- remove duplicates;
- append only new relevant jobs to `Job_Search_Tracker.xlsx`;
- preserve `Found Date` for date-wise filtering.

## Target role families
- Senior Software Engineer
- Senior AI Software Engineer
- Technical Product Manager
- AI Product Manager

Search terms and classification terms are controlled entirely by `config.json`.

## Install
Open Command Prompt in this folder:

    pip install -r requirements.txt

## Run

    python main.py

or double-click:

    run_job_search.bat

The first run will create/use:

    Job_Search_Tracker.xlsx

## Excel columns
ID | Found Date | Posted Date | Role Category | Job Title | Company | Location | Source | Job URL | Status

`Fingerprint` is an internal duplicate-detection field and can be hidden in Excel.

## Important design decision
The tool does NOT require exact title matches.

Example:
- `AI-Native Product Manager` -> AI Product Manager
- `Product Manager` + AI/LLM/RAG context -> AI Product Manager
- `Product Manager` + platform/API/SaaS context -> Technical Product Manager
- `GenAI Engineer` -> Senior AI Software Engineer
- `Backend Engineer` -> Senior Software Engineer

## LinkedIn note
The LinkedIn module uses publicly accessible guest job-listing endpoints and does not log into an account.
These endpoints are unofficial, can be rate-limited, and may change. Keep request volume low.
If LinkedIn returns 429, the collector stops LinkedIn processing for that run rather than retrying aggressively.

## EU Remote Jobs note
EU Remote Jobs is crawled from its newest job-listing pages and jobs are classified locally.
This avoids depending on exact search titles and helps discover unusual role names.

## Next step after V1 works
Use Windows Task Scheduler to run `main.py` once per day automatically.
