CREATE TABLE IF NOT EXISTS runs (
  id SERIAL PRIMARY KEY,
  run_id TEXT UNIQUE NOT NULL,
  sandbox_name TEXT NOT NULL,
  problem_id TEXT,
  state TEXT NOT NULL,
  execution_target TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO runs (run_id, sandbox_name, problem_id, state, execution_target)
VALUES ('seed-run-1', 'sbx-seeddemo1', 'guard-problem', 'deleted', 'celesto_sandbox')
ON CONFLICT (run_id) DO NOTHING;
