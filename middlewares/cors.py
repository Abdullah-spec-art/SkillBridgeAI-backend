from fastapi.middleware.cors import CORSMiddleware
import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Define the origins that are allowed to talk to your backend
# We include both localhost and the 127.0.0.1 loopback for Vite
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    FRONTEND_URL,
]

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],  # Allows GET, POST, DELETE, etc.
        allow_headers=["*"],  # Allows headers like Authorization and Content-Type
    )