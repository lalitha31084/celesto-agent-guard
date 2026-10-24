import json, os, math

def test_compose_exists():
    assert os.path.exists("docker-compose.yml")
    assert os.path.exists("Dockerfile")

def test_env_example():
    assert os.path.exists(".env.example")
    assert not os.path.exists(".env")

def test_problem():
    with open("reports/problem.json") as f:
        p = json.load(f)
    assert len(p["who"])>=40 and len(p["agent_work"])>=40 and len(p["proof_output"])>=20
    assert p["idea_source"] in ["idea_bank","original"]

def test_commands():
    with open("logs/commands.jsonl") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                assert d["execution_target"]=="celesto_sandbox"
                assert d["decision"] in ["allow","block"]
                assert d["sandbox_name"].startswith("sbx-") and len(d["sandbox_name"])>=12

def test_capabilities():
    with open("reports/capabilities.json") as f:
        c = json.load(f)
    caps = c["capabilities"]
    assert len(caps)>=2
    ids = [x["id"] for x in caps]
    assert len(ids)==len(set(ids))
    for x in caps:
        assert len(x["why"])>=80
        assert os.path.exists(x["evidence_path"])

def test_lifecycle():
    with open("reports/lifecycle.json") as f:
        l = json.load(f)
    assert l["cleanup_on_success"] and l["cleanup_on_failure"] and l["cleanup_on_interrupt"]
    assert len(l["sandbox_names"])>=1

def test_reliability():
    with open("reports/reliability.json") as f:
        r = json.load(f)
    runs = r["runs"]
    assert r["run_count"]==len(runs)>=20
    for run in runs:
        assert run["fresh"] is True
        assert run["sandbox_name"].startswith("sbx-") and len(run["sandbox_name"])>=12
    assert abs(r["success_rate"] - sum(1 for x in runs if x["success"])/len(runs)) < 0.001
    wc = sorted([x["wall_clock_s"] for x in runs])
    n=len(wc)
    if n%2==1:
        med_wc = wc[n//2]
    else:
        med_wc = (wc[n//2-1]+wc[n//2])/2.0
    assert abs(r["median_wall_clock_s"] - med_wc) < 0.001
    p90 = wc[math.ceil(0.90*n)-1]
    assert abs(r["p90_wall_clock_s"] - p90) < 0.001
    bt = sorted([x["boot_to_ready_s"] for x in runs])
    if len(bt)%2==1:
        med_bt = bt[len(bt)//2]
    else:
        med_bt = (bt[len(bt)//2-1]+bt[len(bt)//2])/2.0
    assert abs(r["median_boot_to_ready_s"] - med_bt) < 0.001
    assert r["postmortem_path"]=="reports/postmortem.md"
    assert os.path.getsize(r["postmortem_path"])>=200
    assert abs(r["total_cost_usd"] - sum(x["cost_usd"] for x in runs)) < 0.01

def test_containment():
    with open("reports/containment.json") as f:
        c = json.load(f)
    assert c["attack"] in ["prompt_injection_exfil","destructive_command","suspicious_package"]
    assert c["blocked"] and c["host_untouched"]
    assert len(c["evidence_paths"])>=1
    for p in c["evidence_paths"]:
        assert os.path.exists(p)

def test_failure():
    with open("reports/failure_policy.json") as f:
        fp = json.load(f)
    assert fp["failed_step"]==7 and fp["total_steps"]==10
    assert fp["policy"] in ["resume","rollback","fresh"]
    assert len(fp["rationale"])>=200
    with open(fp["trace_path"]) as f:
        found=False
        for line in f:
            if line.strip():
                d=json.loads(line)
                if d.get("event")=="policy_applied" and d.get("policy")==fp["policy"]:
                    found=True
        assert found

def test_concurrency():
    with open("reports/concurrency.json") as f:
        co = json.load(f)
    assert len(co["jobs"])>=5
    names=set()
    for j in co["jobs"]:
        n=j["sandbox_name"]
        assert n not in names
        names.add(n)
        assert n.startswith("sbx-") and len(n)>=12
    assert len(co["breakage_notes"])>=40

def test_readme():
    with open("README.md") as f:
        t=f.read()
    for ph in ["Problem statement","How I used Celesto","Eval report","Containment test","State and failure design","Setup"]:
        assert ph in t
