# Code Repair with LLMs

A backend-focused project for automated code repair and analysis using Large Language Models (LLMs). The repository combines FastAPI-based services, session-driven workflows, and LLM integration patterns to support code understanding, repair, and project interaction through a configurable pipeline.

## Overview

This project is designed to:
- accept uploaded source files or archives,
- organize them into per-session working directories,
- run a selected pipeline of repair/analysis steps,
- manage real-time communication through WebSockets,
- and expose a lightweight API for orchestrating the process.

The repository has evolved across several branches, with the current main branch centered on a FastAPI backend and the newer `pv2.2` work showing stronger ML/LLM integration patterns.

## Repository at a Glance

- Primary language: Python
- Backend: FastAPI + Uvicorn
- Real-time communication: WebSockets
- ML tooling: Transformers, Sentence Transformers, Hugging Face Hub
- Workflow model: modular pipeline with session-based execution

## Tech Stack

### Backend
- FastAPI
- Uvicorn
- Python-Multipart
- WebSockets
- Python-Jose (JWT support)

### ML / LLM Support
- Hugging Face Hub
- sentence-transformers
- transformers
- langchain_text_splitters
- NumPy

### Development / Testing
- pytest
- Docker
- Python 3.10+

## Main Branch Structure

```text
code-repair-with-llms/
├── main.py
├── requirements.txt
├── setup.py
├── .docker/
│   └── Dockerfile
├── app/
│   ├── api/
│   │   ├── router.py
│   │   ├── rest/
│   │   │   └── initiate_pipeline.py
│   │   └── websocket/
│   │       └── websocket_handler.py
│   ├── core/
│   │   ├── file_handler.py
│   │   └── session_manager.py
│   └── utils/
│       └── decode_pipeline_steps.py
├── uploads/
└── README.md
```

## Key Components

### 1. Application Entrypoint
`main.py` creates the FastAPI app and wires up:
- CORS middleware,
- a session manager,
- the API router,
- and a WebSocket endpoint at `/start-llm-session`.

This is the app bootstrap point for local dev and deployment.

### 2. API Router
`app/api/router.py` aggregates the backend routes and includes the pipeline endpoint under the `/api` prefix.

### 3. Pipeline Initiation
`app/api/rest/initiate_pipeline.py` defines the `POST /api/initiate_pipeline` endpoint.

This endpoint:
- validates the selected pipeline steps,
- creates a session token,
- verifies the session,
- processes uploaded files,
- and returns session metadata and file names.

The selected pipeline is encoded as a binary integer. For example, a value like `21` represents the enabled steps encoded in binary.

### 4. Session Manager
`app/core/session_manager.py` provides JWT-based session creation and validation.

It is responsible for:
- issuing a signed token with a `sub` session ID,
- creating a session directory under `./uploads`,
- validating the token and retrieving session paths,
- and exposing methods for step selection and cleanup.

### 5. File Handling
The project includes file utilities to process uploaded content. File uploads are associated with session directories and stored for later pipeline steps.

### 6. WebSocket Support
The backend exposes a WebSocket endpoint for ongoing LLM interaction. This allows the system to maintain an active connection while the user or pipeline continues interacting with the server.

## API Behavior

### Endpoint: Initiate Pipeline
`POST /api/initiate_pipeline`

Request body:
- `files`: one or more uploaded files
- `pipeline_steps`: integer representing selected steps

Validation rules:
- `pipeline_steps` must be non-zero
- `pipeline_steps` must be less than or equal to `63`
- at least one file must be uploaded

Response includes:
- `message`
- `session_token`
- `files`
- `session_id` (included for testing/prototyping)

## Session Workflow

The session workflow is straightforward:
1. Client uploads files.
2. Server validates the pipeline selection.
3. Server creates a JWT-backed session.
4. A session folder is created under `./uploads/<session_id>`.
5. Files are stored and prepared for the chosen pipeline.
6. The client receives a token to continue interaction.

## Running the Project

### Prerequisites
- Python 3.10 or newer
- pip
- optionally Docker

### Install dependencies

```bash
git clone https://github.com/vlazo1214/code-repair-with-llms.git
cd code-repair-with-llms
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The app will be available at:
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Run with Docker

```bash
docker build -f .docker/Dockerfile -t code-repair-llms .
docker run -p 8000:8000 code-repair-llms
```

## Configuration Notes

`main.py` contains a few key configuration points:
- `SECRET_KEY` - JWT signing key
- `ALGORITHM` - defaults to `HS256`
- `UPLOAD_DIR` - default is `./uploads`
- `token_expiration_minutes` - default is `60`

The current CORS setup allows all origins for testing convenience:

```python
allow_origins=["*"]
```

This is suitable for local development, but should be restricted in production.

## Branch Survey Summary

The repository contains several feature branches, each representing different experimental directions:

- `main` - backend-focused project entry point
- `Backend-Server` - server/application backend work
- `New-Apis` - API evolution and endpoint experimentation
- `Training-Data` - data and model pipeline work
- `chatgpt-llm-test` - LLM/testing experimentation around ChatGPT
- `experimental-implementation` - exploratory implementation work
- `pv2` - ML-oriented project progression
- `pv2.1` - earlier ML/integration variant
- `pv2.2` - more advanced branch with ML and LLM dependencies
- `v0-interface` - original interface design work
- `pv2-prior` - prior version before later iteration

The main branch and `pv2.2` branch together suggest the project is moving toward a richer LLM-centric repair architecture, while the backend branch contains the live service and API layer.

## Dependencies and Notes

The repository currently contains a merge-state artifact in `requirements.txt` between earlier backend dependencies and newer ML dependencies. This indicates the project has been in active development across multiple branch ideas, and dependency cleanup may be necessary before a production-ready release.

The newer ML-related requirements include:
- `huggingface_hub`
- `langchain_text_splitters`
- `numpy`
- `sentence_transformers`
- `transformers`

The backend-oriented requirements include:
- `fastapi`
- `uvicorn[standard]`
- `python-multipart`
- `pytest`
- `httpx`
- `websockets`
- `python-jose`

## Testing

The project uses `pytest` and can be run with:

```bash
pytest
```

## Security Considerations

This repository is a prototype and should be hardened before production use:
- rotate or externalize the JWT secret,
- restrict CORS origins,
- validate uploaded file types and sizes,
- enforce secure session expiration and cleanup,
- and consider a dedicated storage model for real deployments.

## License

No explicit license file was visible in the repository snapshot reviewed here. If you plan to publish or share this project publicly, adding a license is recommended.

## Contribution

Contributions are welcome through pull requests. The project is still evolving and has multiple branches that explore different implementation directions, so contributions should be aligned with the active base branch and intended architecture.

---

Repository: https://github.com/vlazo1214/code-repair-with-llms
