from fastapi import FastAPI
from middlewares.cors import setup_cors
from routes import analysis, auth


app = FastAPI(title="SkillBridge AI")

setup_cors(app)
app.include_router(auth.router)
app.include_router(analysis.router)


@app.get("/")
def read_root():
    return {"message": "SkillBridge AI API is up and running!"}