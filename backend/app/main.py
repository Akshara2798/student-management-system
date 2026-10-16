from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import engine, Base

# Importing the model files registers their tables with SQLAlchemy,
# so create_all() below knows about students, admins and revoked_tokens.

from app.routers import admin, students


# Creates the tables in MySQL if they don't exist (existing tables are left untouched)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRUD API")  # creates your FastAPI application and gives it a title.


# CORS is only needed when the browser calls the API from another origin.
# With the Vite proxy (/api -> http://127.0.0.1:8000) requests are same-origin,
# but this keeps working if you point VITE_API_URL straight at the backend.
# allow_credentials=True is required for the login cookie, so origins must be explicit (no "*").
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://student-management-system-learning-code2.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Never let the browser cache admin or student data (stops "back button" showing old data after logout)
@app.middleware("http")
async def no_store_for_private_routes(request: Request, call_next):             # Defines middleware to process HTTP requests and responses
    response = await call_next(request)                                         # Passes the request to the next handler and gets the response

    if request.url.path.startswith(("/admin", "/students")):                    # Checks whether the URL starts with /admin or /students
        response.headers["Cache-Control"] = "no-store"                          # Prevents compliant caches from storing the response

    return response                                                             # Returns the response to the client


# Connect the routers (each router is a department; main.py is the main office)
app.include_router(admin.router)
app.include_router(students.router)


@app.get("/")
def home():
    return {"message": "Student Management API"}
