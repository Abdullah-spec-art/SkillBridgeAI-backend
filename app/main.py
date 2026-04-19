from fastapi import FastAPI
from routes import auth, resume


app = FastAPI(title="SkillBridge AI")

app.include_router(auth.router)
app.include_router(resume.router)

@app.get("/")
def read_root():
    return {"message": "SkillBridge AI API is up and running!"}