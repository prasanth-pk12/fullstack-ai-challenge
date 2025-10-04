## AI Tools Used

* ChatGPT
* Claude
* GitHub Copilot

I have included the prompts I used, along with the minimal AI-generated code for each feature and several iteration examples in this document.

---

## Initial Prompt
```
You are an AI software engineer assistant. Your job is to build a production-ready fullstack Task Manager app with the following requirements:
```
---

## 🔹 Backend (Fast API)

### Feature: `Auth`
**Prompt:** 
```
Build a FastAPI authentication module with JWT-based login and role management.

Requirements:

Endpoints:
* POST /auth/register — create user (use SQLite or in-memory DB)
* POST /auth/login — return JWT token

Roles: admin, user (include in JWT claims)
* Passwords hashed with passlib[bcrypt]
* Use python-jose for JWT signing/verification

Dependencies:
* get_current_user() — decode and return current user
* role_required(role) — restrict endpoint by role

Modular structure: main.py, routers/auth.py, models/auth_models.py, schemas/auth_schemas.py, database/connection.py

Add tests (pytest, httpx.AsyncClient) for register, login, and role-based access

```

**AI Response Used:**
```python
@router.post("/register", response_model=UserSchema)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with JSON data
    """
    # Check if username already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role or UserRole.USER
    )
    
    return db_user



@router.post("/login", response_model=Token)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login user with JSON data and return JWT token
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
```

**Edits / Iterations:**
```
Don’t use form data — all requests and responses must be JSON. Clearly define both folder and file structure since the app will run and be tested from the backend/ folder only. Avoid having multiple auth modules; instead, place all authentication-related logic and services inside a single folder to prevent confusion.
```
---

### Feature: `Task API`
**Prompt:** 
```
Build a FastAPI Task API with JSON-only requests and responses.

Requirements:

Endpoints:

* GET /tasks — list all tasks
* POST /tasks — create a new task
* GET /tasks/{id} — get task by ID
* PUT /tasks/{id} — update task by ID
* DELETE /tasks/{id} — delete task by ID

Task Model:
{ id, title, description, owner, status: [todo, in-progress, done], due_date, attachments: [] }

RBAC:
* Only the task owner or `admin` can edit or delete tasks

Add tests: (pytest, httpx.AsyncClient) for all CRUD endpoints and RBAC enforcement.
```

**AI Response Used:**
```python
@router.put("/{task_id}", response_model=Task)
async def update_existing_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a specific task by ID.
    
    - **Admins**: Can update any task
    - **Users**: Can only update their own tasks
    """
    task = update_task(db, task_id, task_data, current_user)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific task by ID.
    
    - **Admins**: Can delete any task
    - **Users**: Can only delete their own tasks
    """
    success = delete_task(db, task_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return None
```

**Edits / Iterations:**
```
Add cors with allow origin localhost port 3000
```
---


### Feature: `File Upload`
**Prompt:** 
```
Build a FastAPI endpoint to upload attachments for tasks and make relationship with Task via attachment.

Requirements:

Endpoint:
* POST /tasks/{id}/upload — upload a file for a task, store on-disk and return the file URL

Other Requirements:
* Validate that the task exists before upload
* Include proper error handling
* Add tests (pytest, httpx.AsyncClient) for uploading files and handling errors
```

**AI Response Used:**
```python
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files for uploaded attachments
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
```

**Edits / Iterations:**
```
Update the Task Manager app to support one attachment per task. In the task list view, display the attachment (file name or download link) clearly below each task. Modify the backend to allow only a single attachment per task — new uploads should replace the existing file.

In the task edit page, show the existing attachment with a remove option. Once removed, allow the user to upload a new file; no separate “existing” upload option is needed. Ensure the API, models, and validation enforce this one-file rule. Use TailwindCSS for a clean, consistent layout.
```

---


### Feature: `External API Integration`
**Prompt:** 
```
Build a FastAPI endpoint to fetch external data.

Requirements:

Endpoint:
* GET /external/quote — fetch a random motivational quote from a public API

Other Requirements:
* Include proper error handling for API failures
* In tests, mock the external API
* Add tests (pytest, httpx.AsyncClient) for success and failure cases
```

**AI Response Used:**
```python
@router.get("/quote", response_model=QuoteResponse)
async def get_random_quote(
    use_fallback: bool = Query(
        True, 
        description="Whether to use fallback quotes if external API fails"
    )
):
    request_id = str(uuid.uuid4())
    logger.info(f"Quote request started [ID: {request_id}]")
    
    try:
        if use_fallback:
            # Use service with fallback capability
            quote_data = await fetch_quote_with_fallback()
            logger.info(f"Quote fetched successfully [ID: {request_id}] from {quote_data.get('source')}")
        else:
            # Use service without fallback - will raise exception on failure
            quote_data = await fetch_random_quote()
            logger.info(f"Quote fetched successfully [ID: {request_id}] from external API")
        
        return QuoteResponse(**quote_data)
        
    except ExternalAPIError as e:
        logger.error(f"External API error [ID: {request_id}]: {e.message}")
        raise convert_external_api_error_to_http_exception(e)
    
    except Exception as e:
        logger.error(f"Unexpected error [ID: {request_id}]: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "An unexpected error occurred while fetching quote",
                "error_type": "internal_server_error",
                "request_id": request_id
            }
        )

```

---


### Feature: `Real-time-ish`
**Prompt:** 
```
Build a FastAPI endpoint to provide real-time task updates.

Requirements:

Endpoint:
* /ws/tasks — WebSocket endpoint that sends events when tasks are created or updated

Other Requirements:
JSON messages for events
Include proper error handling and connection management
Add tests (pytest, AsyncClient or WebSocket test client) for connection and event delivery
```

**Edits / Iterations:**
```
The pytest test tests/test_websockets.py::TestWebSocketConnection::test_websocket_connection_without_token hangs when connecting to /ws/tasks without a token.
```
---


### Feature: `Test`
**Prompt:** 
```
Build pytest-based integration tests for the FastAPI Task Manager app.

Requirements:

Test Coverage:

Auth workflows: register, login, JWT validation, role-based access

RBAC enforcement for tasks and file uploads

File upload endpoint: success and error cases

External API: mock the API for /external/quote

Real-time updates: basic connection and event delivery

Performance / Load Test:

* Include at least one simple benchmark (e.g., looped requests to /tasks)

Other Requirements:

* Ensure all test cases pass; if anything fails, fix the implementation
* Use pytest, httpx.AsyncClient, and WebSocket test client as needed


```

**AI Response Used:**
```python
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

**Edits / Iterations:**
```
None
```
---


### Feature: `API Docs`
**Prompt**
```
Generate clean, professional API documentation for the Task Manager backend using FastAPI’s OpenAPI.
Include all endpoints: authentication, task CRUD, file upload, external API, real-time updates
Provide summary, description, request/response schemas, path/query parameters, and response codes for each endpoint
Include example requests and responses (JSON-only)
Document JWT authentication and role-based access
Ensure docs are fully compatible with FastAPI’s /docs (Swagger UI) and /redoc
```

## Frontend (React)

### Feature: `Auth flow`
**Prompt:** 
```
Build a React frontend for the Task Manager app.

Requirements:

Auth Flows:
* Login page that accepts credentials and persists JWT
* Logout functionality that clears JWT and resets auth state

Other Requirements:
* JSON-only communication with the backend
* Proper error handling and validation

UI/UX Requirements:
* World-class, modern, and visually appealing design
* Clean, intuitive, responsive, and accessible layout
* Use TailwindCSS libraries
* Smooth interactions and polished look

Include basic tests (Jest + React Testing Library) for login and logout flows

```

**Edits / Iterations:**
```
Improve the Register page UI for the Task Manager frontend using TailwindCSS. Fix the password field overflow so it fits properly on all screen sizes, align labels and inputs neatly with proper spacing, and ensure text fields, buttons, and error messages are consistent and visually appealing. Make the form responsive, modern-looking.
```
```
Update the Register page UI to fix the button and input label issues. Ensure the submit button is clearly visible with proper background color and contrast. Align all input labels to the left with readable font color, spacing, and size
```
```
After successful sign-in, redirect the user automatically to the Tasks page. Ensure the JWT token is stored securely (in localStorage or HttpOnly cookie) and used for authenticated API requests. Use React Router for navigation, handle invalid tokens gracefully by redirecting to the login page, and display a short loading state during redirection. Maintain clean, responsive TailwindCSS styling and include Jest + React Testing Library tests to verify the redirect flow and token handling. Suggest a descriptive commit message after implementation.
```
---

### Feature: `Task UI`
**Prompt:** 
```
Requirements:

Task Features:
* Task list view showing all tasks
* Create Task form and Edit Task form
* Display task attachments and enable uploading

Role-specific UI:
* Admin sees delete buttons for all tasks
* User sees delete buttons only for their own tasks

UI/UX Requirements:

* World-class, modern, and visually appealing design
* Clean, intuitive, responsive, and accessible layout
* Use TailwindCSS, shadcn/ui, or similar modern component libraries
* Smooth interactions and polished look


```

**Edits / Iterations:**
```
Create task API fails. Find the error below and fix it
Payload:
{
    "title": "complete test",
    "description": "test",
    "status": "TODO",
    "due_date": "2025-10-10T11:17:00.000Z"
}
Error response:
[
    {
        "type": "enum",
        "loc": [
            "body",
            "status"
        ],
        "msg": "Input should be 'todo', 'in-progress' or 'done'",
        "input": "TODO",
        "ctx": {
            "expected": "'todo', 'in-progress' or 'done'"
        },
        "url": "https://errors.pydantic.dev/2.8/v/enum"
    }
]
```
```
Update the top header UI to display the logged-in username and role below the app name in a clean, minimal style
```
```
On the frontend, display the creator’s name below each task title or in a small label (e.g., “Created by: username”). Ensure admins can view all creators clearly
```
---



### Feature: `Real-time Update`
**Prompt:** 
```
Build real-time task updates in the React frontend.

Requirements:

Features:
* Connect to backend SSE or WebSocket endpoint (/ws/tasks)
* Receive task events for created or updated tasks
* Automatically update the task list in the UI upon receiving events

Other Requirements:
* Handle connection errors and reconnections gracefully
* Ensure smooth, modern UI/UX with live updates


### Feature: `External Quote`
**Prompt:** 
```
Build a React frontend component to display external quotes.

Requirements:

Features:
* Fetch a random motivational quote from backend endpoint /external/quote
* Display the quote in a visually appealing way on the UI
* Handle loading and error states gracefully

Other Requirements:
* Ensure modern, clean, and responsive design
* Include basic tests (Jest + React Testing Library) for fetch and display

```

**Edits / Iterations:**
```
Refine the Task page UI by reducing the height of the query container for a more compact layout. Remove the full-page blur effect that appears when the Refresh button is clicked
```
---



### Feature: `E2E tests`
**Prompt:** 
```
Build end-to-end (E2E) tests for the React frontend of the Task Manager app.

Requirements:

Test Coverage:

Basic E2E tests for auth flows: login and logout

Task workflows: create, edit, delete tasks, upload attachments

Real-time updates: verify task list updates on backend events

External quote: verify fetching and displaying a quote

Other Requirements:
* Use Cypress 

Include proper setup and teardown
```



### Feature: `CI`
**Prompt:** 
```
Build a robust CI/CD pipeline configuration for the Task Manager app.

Requirements:

Pipeline Tasks:
* Run backend tests using pytest, covering unit, integration, performance, and WebSocket tests
* Run frontend tests, including unit, integration, and E2E tests
* Build and bundle the frontend for production

Other Requirements:
* Use GitHub Actions
* Fail the pipeline if any test or build step fails
* Include caching for dependencies and optimization to speed up pipeline runs
* Ensure clear logs for debugging failed steps
```

---

### Feature: `Containerize`
**Prompt:** 
```
Build Dockerfiles and a docker-compose.yml to run the Task Manager app (backend + frontend).

Requirements:

Dockerfiles:

Backend Dockerfile:
Use an official Python base image
Install dependencies from requirements.txt
Copy backend source code
Run migrations (if any) and start FastAPI with Uvicorn

Frontend Dockerfile:
Use an official Node.js base image
Install dependencies from package.json
Build React app for production
Serve via a lightweight HTTP server (e.g., nginx or serve)

docker-compose.yml:
Services for backend, frontend, and PostgreSQL database
Proper network configuration and environment variables
Volumes for database persistence
Ensure backend depends on database and frontend depends on backend
Expose necessary ports for local development

Other Requirements:
Images should be optimized for size and build speed
Include instructions to build and run the stack locally
```
---