from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
import os
from typing import List, Optional

app = FastAPI()

class RunCreate(BaseModel):
    run_id: str
    sandbox_name: str
    problem_id: Optional[str] = None
    state: str
    execution_target: str

@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/runs")
async def get_runs():
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch("SELECT run_id, sandbox_name, problem_id, state, execution_target FROM runs ORDER BY id")
    return [dict(r) for r in rows]

@app.post("/api/runs", status_code=201)
async def create_run(run: RunCreate):
    valid_states = {"created", "ready", "running", "succeeded", "failed", "deleted"}
    if run.execution_target != "celesto_sandbox":
        raise HTTPException(status_code=400, detail="invalid execution_target")
    if run.state not in valid_states:
        raise HTTPException(status_code=400, detail="invalid state")
    if not (run.sandbox_name.startswith("sbx-") and len(run.sandbox_name) >= 12):
        raise HTTPException(status_code=400, detail="invalid sandbox_name")
    async with app.state.pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO runs(run_id,sandbox_name,problem_id,state,execution_target) VALUES($1,$2,$3,$4,$5)",
                run.run_id, run.sandbox_name, run.problem_id, run.state, run.execution_target
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return run.dict()
