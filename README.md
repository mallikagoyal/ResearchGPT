# ResearchGPT

AI-powered research document assistant. Upload PDFs, and chat with them using
Retrieval-Augmented Generation (RAG) with inline source citations.

> **Status:** All 6 planned phases are complete. ResearchGPT is now
> functionally whole: register, upload a PDF, wait for it to process, and
> chat with it — grounded, streamed answers with inline citations and
> persisted conversation history.
>
> **Note on ChromaDB version:** the spec didn't pin a version, and testing
> surfaced a real, reproducible bug in `chromadb==0.5.23` (client/server
> request serialization breaks during its v1→v2 API transition — see
> [chroma-core/chroma#4156](https://github.com/chroma-core/chroma/issues/4156)
> for the same failure mode). This project pins **`chromadb==1.5.9`**
> instead (client and server, matched), verified working end-to-end.
>
> **Note on Next.js version:** the spec called for Next.js 15, but 15.1.x
> (and its first two patch rounds) were affected by a critical RCE chain
> (CVE-2025-66478 and the Dec 11, 2025 follow-ups, CVSS 10.0). Rather than
> ship a version with known critical vulnerabilities, this project pins
> **Next.js 16.3.0** — the current stable release with `npm audit` reporting
> zero vulnerabilities. The App Router API used here is unchanged between
> 15 and 16, so this doesn't affect any of the patterns described below.

## Tech Stack

| Layer      | Technology                                                        |
|------------|--------------------------------------------------------------------|
| Frontend   | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui-style components, TanStack Query, Axios |
| Backend    | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database   | PostgreSQL                                                         |
| Vector DB  | ChromaDB                                                            |
| AI         | LangChain, HuggingFace sentence-transformers, OpenAI-compatible LLM |
| Auth       | JWT + bcrypt                                                        |
| Deployment | Docker + Docker Compose                                             |

## Folder Structure

```
researchgpt/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers: health, auth, users, documents, chat
│   │   ├── core/           # config, logging, exceptions — no framework/DB imports
│   │   ├── database/       # SQLAlchemy engine, session, declarative base
│   │   ├── models/         # SQLAlchemy ORM models (User, Document, DocumentChunk, Conversation, Message)
│   │   ├── repositories/   # DB access: UserRepository, DocumentRepository, DocumentChunkRepository, ConversationRepository, MessageRepository
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # business logic: AuthService, DocumentService, ChatService (streaming RAG), ConversationService (history)
│   │   ├── rag/             # chunking.py, embeddings.py, vector_store.py, retrieval.py, context_builder.py, llm_client.py
│   │   ├── auth/            # security.py (hashing/JWT), dependencies.py (DI, get_current_user)
│   │   ├── utils/           # pdf_extractor.py (PyMuPDF), text_cleaner.py
│   │   └── main.py         # FastAPI app, middleware, exception handlers
│   ├── alembic/             # DB migrations (users, documents, document_chunks, conversations, messages)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── frontend/
    ├── app/                  # Next.js App Router pages
    │   ├── layout.tsx        # Root layout — wraps app in QueryProvider + AuthProvider
    │   ├── page.tsx           # "/" — redirects to /dashboard or /login based on session
    │   ├── login/page.tsx
    │   ├── register/page.tsx
    │   └── dashboard/
    │       ├── layout.tsx    # Protected shell: Navbar + Sidebar
    │       ├── page.tsx      # Overview: live stats + recent documents
    │       ├── upload/page.tsx      # Dropzone + document list
    │       ├── documents/page.tsx   # Full document list with search
    │       └── chat/page.tsx        # Conversation sidebar + streaming chat thread
    ├── components/
    │   ├── ui/                # shadcn/ui-style primitives (Button, Input, Card, Alert, Skeleton, Badge, Progress)
    │   ├── auth/               # LoginForm, RegisterForm, ProtectedRoute
    │   ├── documents/          # DocumentDropzone, DocumentList, DocumentStatusBadge
    │   ├── chat/                # ChatMessageBubble (markdown + citations), ChatInput, ConversationSidebar, DocumentScopeSelector
    │   ├── providers/          # AuthProvider (session state), QueryProvider (TanStack Query)
    │   ├── navbar.tsx
    │   └── sidebar.tsx
    ├── hooks/                 # useAuth(), useDocuments(), useChat() (SSE streaming state), useConversations()
    ├── lib/                   # axios instance (JWT interceptor), cn()/formatFileSize() helpers
    ├── services/               # auth-service.ts, document-service.ts, chat-service.ts (hand-rolled SSE parsing over fetch)
    ├── types/                  # TypeScript types mirroring backend Pydantic schemas
    ├── Dockerfile
    └── .env.local.example
```

**Frontend layering mirrors the backend:** components call hooks (`useAuth`), hooks call services (`authService`), services call the shared `apiClient`. No component talks to Axios directly, so swapping an endpoint shape only touches `services/`.

**Why this structure:** each layer only depends on the layer(s) beneath it.
`api/` depends on `services/`, `services/` depends on `repositories/` and
`rag/`, and `core/`/`database/`/`models/`/`schemas/` are shared foundations
with no business logic. This keeps business logic testable without spinning
up FastAPI or a real database.

## Running (Full app — Phases 1–6)

Postgres, ChromaDB, the backend, and the frontend are wired up end-to-end.
The app is now functionally complete: register, upload, process, and chat.

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set a real JWT_SECRET_KEY (e.g. `openssl rand -hex 32`)
# and your LLM_API_KEY.

docker compose up --build
```

Apply the database migrations (creates `users`, `documents`,
`document_chunks`, `conversations`, and `messages` tables):

```bash
docker compose exec backend alembic upgrade head
```

Then verify:

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","database":"ok"}
```

- Backend interactive API docs: http://localhost:8000/docs
- **Frontend app: http://localhost:3000**

### Try it via the UI

1. Register, then go to **Upload** and drag in a PDF.
2. Watch the status go `Pending → Processing → Processed`. On first run,
   the embedding model (~90MB) downloads from HuggingFace — this can take
   a minute or two the first time only; it's cached in the container
   afterward, so later uploads process in seconds.
3. Go to **Chat**. Ask a question — the response streams in token by
   token, rendered as Markdown, with a **Sources** panel underneath citing
   the exact excerpts used (matching the `[1]`, `[2]` markers in the
   answer text).
4. Use the document-scope dropdown (top-right of the chat page) to narrow
   a conversation to one specific document, or leave it on "All documents"
   to search your whole library.
5. Past conversations appear in the left sidebar — click to resume one, or
   **New chat** to start fresh. Hover a conversation to delete it.
6. Ask something unrelated to your uploads (e.g. before uploading
   anything) — the app responds with a plain "I don't have that
   information" message instead of guessing; it never calls the LLM with
   no grounding context at all.

### Try it via curl (backend only)

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"supersecret123","full_name":"Jane Doe"}'
# -> {"access_token": "...", "token_type": "bearer", "user": {...}}

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"supersecret123"}'

# Call a protected route (replace $TOKEN with the access_token above)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Chat (after uploading + processing at least one document) — streams SSE
curl -N -X POST http://localhost:8000/api/v1/chat/query \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "What is this document about?"}'
```

### Creating future migrations

Whenever you add/change a model under `backend/app/models/`, generate a
migration and apply it:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe your change"
docker compose exec backend alembic upgrade head
```

### How chat (RAG) works

`POST /chat/query` streams a response via Server-Sent-Events rather than
returning a single JSON blob. The frontend consumes this with a hand-rolled
`fetch` + `ReadableStream` reader (`services/chat-service.ts`) — the
browser's native `EventSource` only supports GET requests, and this
endpoint needs a POST body plus an `Authorization` header.

Per query:
1. The conversation is resolved or created, and the user's message is persisted.
2. The message is embedded and used to query the user's ChromaDB
   collection (optionally filtered to one document via a metadata `where`
   clause) for the top `RAG_TOP_K` most similar chunks.
3. **If nothing relevant is found** (no processed documents, or nothing
   similar enough), the app returns a fixed "I don't have that
   information" message and **skips the LLM call entirely** — a stronger
   grounding guarantee than prompt instructions alone.
4. Otherwise, retrieved chunks are formatted into a numbered context block
   and embedded in a system prompt instructing the model to answer only
   from that context and cite excerpts inline (e.g. `[1]`).
5. The LLM response streams back token-by-token over SSE, then is
   persisted as an assistant message with its source citations attached.

**Note for contributors:** like the background document-processing task,
the chat streaming generator (`services/chat_service.py`) opens its own
database session rather than reusing the request's. A FastAPI endpoint
returns its `StreamingResponse` object as soon as the generator is
created — before the stream actually finishes — so the request-scoped
session's dependency lifecycle can begin tearing down well before the
generator needs to write the final assistant message. A self-contained
session avoids depending on a session that may already be closing.

### How document processing works

Uploads don't block on processing. `POST /documents/upload` validates and
stores the file, creates a `documents` row in `pending` status, and
schedules the full pipeline via FastAPI's `BackgroundTasks` — no
Celery/Redis needed. The response returns immediately; the frontend polls
`GET /documents` every 2s while any document is `pending`/`processing`.

The background pipeline, in order:
1. **Extract** — PyMuPDF pulls text, title, and page count (`utils/pdf_extractor.py`).
2. **Chunk** — LangChain's `RecursiveCharacterTextSplitter` splits the
   cleaned text into overlapping chunks, using each document's own
   `chunk_size`/`chunk_overlap` (configurable per upload, defaults from
   `DEFAULT_CHUNK_SIZE`/`DEFAULT_CHUNK_OVERLAP`) (`rag/chunking.py`).
3. **Embed** — each chunk is embedded with a HuggingFace sentence-transformer
   model (`EMBEDDING_MODEL_NAME`, default `all-MiniLM-L6-v2`), loaded once
   per process (`rag/embeddings.py`).
4. **Store** — vectors are written to a **per-user** ChromaDB collection
   (`rag/vector_store.py`); chunk metadata (text, index, char count) is
   written to the `document_chunks` table in Postgres.
5. Only after all of that succeeds is the document marked `processed`.

**Per-user Chroma collections, not one shared collection filtered by
user_id:** similarity search is structurally scoped to a single user's
documents. A bug in query-building elsewhere can't leak another user's
chunks, because they simply aren't in the collection being queried.

**Write order on success:** vectors are written to Chroma *before* chunk
metadata is written to Postgres. If the Chroma write fails, nothing is
left behind in Postgres to go stale.

**Note for contributors:** the background task opens its own database
session rather than reusing the request's. This matters because FastAPI
runs `BackgroundTasks` *before* the request-scoped session's implicit
commit-after-response — so the upload service explicitly commits after
creating the document rows, before returning. Without that explicit
commit, the background task's separate session wouldn't yet see the
just-created rows. See `DocumentService.upload_documents` and
`DocumentRepository.commit()` for the fix.

## Environment Variables

See `backend/.env.example` for the full list with inline descriptions. Key
ones you must set yourself before running in any real environment:

| Variable         | Required | Description                                      |
|------------------|----------|---------------------------------------------------|
| `JWT_SECRET_KEY` | Yes      | Signing key for JWTs. Generate with `openssl rand -hex 32`. |
| `LLM_API_KEY`    | Yes (for chat) | API key for your OpenAI-compatible LLM provider. |
| `LLM_BASE_URL`   | No       | Point at any OpenAI-compatible endpoint (OpenAI, local vLLM, etc). |
| `LLM_MODEL_NAME` | No       | Model to request, e.g. `gpt-4o-mini`. |
| `LLM_TEMPERATURE` / `LLM_MAX_TOKENS` | No | Generation parameters passed to the chat completions call. |
| `RAG_TOP_K`      | No       | How many chunks to retrieve per query. Defaults to 5. |
| `DATABASE_URL`   | No       | Defaults to the `postgres` service in docker-compose. |
| `UPLOAD_DIR`     | No       | Where uploaded PDFs are stored inside the backend container. Defaults to `/app/uploads` (a named Docker volume). |
| `MAX_UPLOAD_SIZE_MB` | No   | Per-file upload size limit. Defaults to 25MB. |
| `DEFAULT_CHUNK_SIZE` / `DEFAULT_CHUNK_OVERLAP` | No | Default chunking config recorded on each document; overridable per-upload. |
| `CHROMA_HOST` / `CHROMA_PORT` | No | ChromaDB connection. Defaults to the `chromadb` service in docker-compose. |
| `CHROMA_COLLECTION_PREFIX` | No | Prefix for per-user Chroma collection names. Defaults to `researchgpt_user_`. |
| `EMBEDDING_MODEL_NAME` | No | HuggingFace sentence-transformer model. Defaults to `sentence-transformers/all-MiniLM-L6-v2` (~90MB, downloaded on first use and cached). |
| `EMBEDDING_DEVICE` | No | `cpu` or `cuda`. Defaults to `cpu` — fine for MVP scale. |

**Frontend** (`frontend/.env.local.example`):

| Variable               | Required | Description                                      |
|------------------------|----------|---------------------------------------------------|
| `NEXT_PUBLIC_API_URL`  | No       | Backend base URL, reachable from the **browser** (so `localhost`, not the Docker service name). Defaults to `http://localhost:8000/api/v1`. Baked into the client bundle at build time — set it via `NEXT_PUBLIC_API_URL` build arg if deploying the backend elsewhere. |

## Roadmap

- [x] Phase 1 — Project foundation (Docker Compose, config, DB session, logging, `/health`)
- [x] Phase 2 — User model, Alembic migrations, auth (register/login/JWT, `/users/me`)
- [x] Phase 3 — Frontend scaffold: Login, Register, protected Dashboard shell (Navbar + Sidebar)
- [x] Phase 4 — Document upload: drag-and-drop, PyMuPDF extraction, background processing, document management
- [x] Phase 5 — Chunking + embeddings + ChromaDB storage (per-user collections, full processing pipeline)
- [x] Phase 6 — RAG retrieval + chat: streaming SSE responses, inline citations, conversation history, grounding enforced structurally (no LLM call without retrieved context)

All phases from the original spec are now complete.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Service + DB liveness |
| POST | `/api/v1/auth/register` | Create account, returns JWT |
| POST | `/api/v1/auth/login` | Authenticate, returns JWT |
| GET | `/api/v1/users/me` | Current user profile (protected) |
| POST | `/api/v1/documents/upload` | Upload PDF(s), returns immediately with `pending` status |
| GET | `/api/v1/documents` | List documents, optional `?search=` |
| GET | `/api/v1/documents/{id}` | Document detail, including extracted text and `chunk_count` |
| DELETE | `/api/v1/documents/{id}` | Delete document, its chunks, its file, and its vectors |
| POST | `/api/v1/chat/query` | Send a message, streams a grounded response via SSE |
| GET | `/api/v1/chat/conversations` | List conversation history |
| GET | `/api/v1/chat/conversations/{id}` | Full message history for one conversation |
| DELETE | `/api/v1/chat/conversations/{id}` | Delete a conversation |

Full interactive docs (request/response schemas, try-it-out): `/docs` on the running backend.
