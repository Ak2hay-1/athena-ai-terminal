from fastapi import FastAPI

app = FastAPI(
    title="Athena AI Terminal",
    version="0.1.0"
)


@app.get("/")
def home():
    return {
        "project": "Athena AI Terminal",
        "status": "Running",
        "version": "0.1.0"
    }


@app.get("/health")
def health():
    return {
        "status": "Healthy"
    }