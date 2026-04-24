from pydantic import BaseModel

class GoogleAuthRequest(BaseModel):
    google_token: str