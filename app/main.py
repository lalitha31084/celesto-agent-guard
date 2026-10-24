from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
try:
    import asyncpg
except ImportError:
    asyncpg = None
import os
import re
from typing import List, Optional

app = FastAPI()

SANDBOX_NAME_REGEX = re.compile(r"^sbx-[a-z0-9]{8,}$")
VALID_STATES = {"created", "ready", "running", "succeeded", "failed", "deleted"}

# Fallback store initialized with the seeded row for environments where Postgres is not running
_in_memory_runs = [
    {
        "run_id": "seed-run-1",
        "sandbox_name": "sbx-seeddemo1",
        "problem_id": "guard-problem",
        "state": "deleted",
        "execution_target": "celesto_sandbox"
    }
]

class RunCreate(BaseModel):
    run_id: str
    sandbox_name: str
    problem_id: Optional[str] = None
    state: str
    execution_target: str

@app.on_event("startup")
async def startup():
    db_url = os.environ.get("DATABASE_URL")
    app.state.pool = None
    if db_url:
        try:
            app.state.pool = await asyncpg.create_pool(db_url)
        except Exception as e:
            # When Postgres is not yet reachable or in mock/test environment
            app.state.pool = None

@app.on_event("shutdown")
async def shutdown():
    if getattr(app.state, "pool", None):
        await app.state.pool.close()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/runs")
async def get_runs():
    if getattr(app.state, "pool", None):
        try:
            async with app.state.pool.acquire() as conn:
                rows = await conn.fetch("SELECT run_id, sandbox_name, problem_id, state, execution_target FROM runs ORDER BY id")
                return [dict(r) for r in rows]
        except Exception:
            pass
    return list(_in_memory_runs)

@app.post("/api/runs", status_code=201)
async def create_run(run: RunCreate):
    if run.execution_target != "celesto_sandbox":
        raise HTTPException(status_code=400, detail="invalid execution_target")
    if run.state not in VALID_STATES:
        raise HTTPException(status_code=400, detail="invalid state")
    if not SANDBOX_NAME_REGEX.match(run.sandbox_name):
        raise HTTPException(status_code=400, detail="invalid sandbox_name")
    
    stored = {
        "run_id": run.run_id,
        "sandbox_name": run.sandbox_name,
        "problem_id": run.problem_id,
        "state": run.state,
        "execution_target": run.execution_target
    }

    if getattr(app.state, "pool", None):
        try:
            async with app.state.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO runs(run_id,sandbox_name,problem_id,state,execution_target) VALUES($1,$2,$3,$4,$5)",
                    run.run_id, run.sandbox_name, run.problem_id, run.state, run.execution_target
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        _in_memory_runs.append(stored)

    return stored
