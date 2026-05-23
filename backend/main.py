from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update, delete
from typing import Optional
from decimal import Decimal

from database import get_db
from models import Pillar, Team, KPI, ReportPeriod, StatusLookup, TaskTypeLookup, Task
from schemas import (
    PillarOut, PillarCreate, PillarUpdate,
    TeamOut, TeamCreate, TeamUpdate,
    KPIOut, KPICreate, KPIUpdate,
    ReportPeriodOut, ReportPeriodCreate, ReportPeriodUpdate,
    LookupItem,
    TaskOut, TaskCreate, TaskUpdate,
    VPSummary, RAGItem, KPIProgress, PillarViewItem, TaskDrillItem, BlockedAtRisk,
)

app = FastAPI(title="KPI Portal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helpers ────────────────────────────────────────────────────────────────

def rag(pct: float) -> str:
    if pct >= 0.75:
        return "Green"
    if pct >= 0.40:
        return "Amber"
    return "Red"


async def kpi_pct(kpi_id: int, db: AsyncSession) -> float:
    result = await db.execute(
        select(func.avg(Task.pct_complete)).where(Task.kpi_id == kpi_id)
    )
    val = result.scalar()
    return float(val) if val is not None else 0.0


async def enrich_task(t: Task) -> dict:
    d = {
        "id": t.id,
        "kpi_id": t.kpi_id,
        "report_period_id": t.report_period_id,
        "task_code": t.task_code,
        "task_name": t.task_name,
        "task_type_id": t.task_type_id,
        "start_date": t.start_date,
        "due_date": t.due_date,
        "status_id": t.status_id,
        "pct_complete": t.pct_complete,
        "effort_days": t.effort_days,
        "actual_days": t.actual_days,
        "blockers": t.blockers,
        "notes": t.notes,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "status_value": t.status.value if t.status else None,
        "task_type_value": t.task_type.value if t.task_type else None,
        "kpi_code": t.kpi.kpi_code if t.kpi else None,
        "kpi_name": t.kpi.kpi_name if t.kpi else None,
        "pillar_code": t.kpi.pillar.code if t.kpi and t.kpi.pillar else None,
        "team_name": t.kpi.team.name if t.kpi and t.kpi.team else None,
        "period_label": t.report_period.label if t.report_period else None,
    }
    return d


# ─── Pillars ────────────────────────────────────────────────────────────────

@app.get("/pillars", response_model=list[PillarOut])
async def list_pillars(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pillar).order_by(Pillar.code))
    return result.scalars().all()


@app.post("/pillars", response_model=PillarOut)
async def create_pillar(body: PillarCreate, db: AsyncSession = Depends(get_db)):
    p = Pillar(**body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@app.put("/pillars/{pillar_id}", response_model=PillarOut)
async def update_pillar(pillar_id: int, body: PillarUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pillar).where(Pillar.id == pillar_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Pillar not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return p


@app.delete("/pillars/{pillar_id}")
async def delete_pillar(pillar_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pillar).where(Pillar.id == pillar_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Pillar not found")
    await db.delete(p)
    await db.commit()
    return {"ok": True}


# ─── Teams ──────────────────────────────────────────────────────────────────

@app.get("/teams", response_model=list[TeamOut])
async def list_teams(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).order_by(Team.name))
    return result.scalars().all()


@app.post("/teams", response_model=TeamOut)
async def create_team(body: TeamCreate, db: AsyncSession = Depends(get_db)):
    t = Team(**body.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@app.put("/teams/{team_id}", response_model=TeamOut)
async def update_team(team_id: int, body: TeamUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Team not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return t


@app.delete("/teams/{team_id}")
async def delete_team(team_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Team not found")
    await db.delete(t)
    await db.commit()
    return {"ok": True}


# ─── KPIs ───────────────────────────────────────────────────────────────────

@app.get("/kpis", response_model=list[KPIOut])
async def list_kpis(
    team_id: Optional[int] = None,
    pillar_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(KPI)
    if team_id:
        q = q.where(KPI.team_id == team_id)
    if pillar_id:
        q = q.where(KPI.pillar_id == pillar_id)
    q = q.order_by(KPI.kpi_code)
    result = await db.execute(q)
    kpis = result.scalars().all()
    out = []
    for k in kpis:
        # eagerly load relations
        await db.refresh(k, ["pillar", "team"])
        out.append(KPIOut(
            id=k.id, kpi_code=k.kpi_code, pillar_id=k.pillar_id, team_id=k.team_id,
            header_code=k.header_code, header_name=k.header_name, kpi_name=k.kpi_name,
            pillar_name=k.pillar.name if k.pillar else None,
            team_name=k.team.name if k.team else None,
        ))
    return out


@app.post("/kpis", response_model=KPIOut)
async def create_kpi(body: KPICreate, db: AsyncSession = Depends(get_db)):
    k = KPI(**body.model_dump())
    db.add(k)
    await db.commit()
    await db.refresh(k, ["pillar", "team"])
    return KPIOut(
        id=k.id, kpi_code=k.kpi_code, pillar_id=k.pillar_id, team_id=k.team_id,
        header_code=k.header_code, header_name=k.header_name, kpi_name=k.kpi_name,
        pillar_name=k.pillar.name if k.pillar else None,
        team_name=k.team.name if k.team else None,
    )


@app.put("/kpis/{kpi_id}", response_model=KPIOut)
async def update_kpi(kpi_id: int, body: KPIUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KPI).where(KPI.id == kpi_id))
    k = result.scalar_one_or_none()
    if not k:
        raise HTTPException(404, "KPI not found")
    for kk, v in body.model_dump(exclude_none=True).items():
        setattr(k, kk, v)
    await db.commit()
    await db.refresh(k, ["pillar", "team"])
    return KPIOut(
        id=k.id, kpi_code=k.kpi_code, pillar_id=k.pillar_id, team_id=k.team_id,
        header_code=k.header_code, header_name=k.header_name, kpi_name=k.kpi_name,
        pillar_name=k.pillar.name if k.pillar else None,
        team_name=k.team.name if k.team else None,
    )


@app.delete("/kpis/{kpi_id}")
async def delete_kpi(kpi_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KPI).where(KPI.id == kpi_id))
    k = result.scalar_one_or_none()
    if not k:
        raise HTTPException(404, "KPI not found")
    await db.delete(k)
    await db.commit()
    return {"ok": True}


# ─── Tasks ──────────────────────────────────────────────────────────────────

@app.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    team_id: Optional[int] = None,
    kpi_id: Optional[int] = None,
    report_period_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Task).order_by(Task.id)
    if kpi_id:
        q = q.where(Task.kpi_id == kpi_id)
    if report_period_id:
        q = q.where(Task.report_period_id == report_period_id)
    result = await db.execute(q)
    tasks = result.scalars().all()

    out = []
    for t in tasks:
        await db.refresh(t, ["kpi", "status", "task_type", "report_period"])
        if t.kpi:
            await db.refresh(t.kpi, ["pillar", "team"])
        if team_id and (not t.kpi or t.kpi.team_id != team_id):
            continue
        out.append(TaskOut(**await enrich_task(t)))
    return out


@app.post("/tasks", response_model=TaskOut)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    t = Task(**body.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t, ["kpi", "status", "task_type", "report_period"])
    if t.kpi:
        await db.refresh(t.kpi, ["pillar", "team"])
    return TaskOut(**await enrich_task(t))


@app.put("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, body: TaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Task not found")
    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(t, k, v)
    # manually set updated_at
    t.updated_at = func.now()
    await db.commit()
    await db.refresh(t, ["kpi", "status", "task_type", "report_period"])
    if t.kpi:
        await db.refresh(t.kpi, ["pillar", "team"])
    return TaskOut(**await enrich_task(t))


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Task not found")
    await db.delete(t)
    await db.commit()
    return {"ok": True}


# ─── Lookup tables ──────────────────────────────────────────────────────────

@app.get("/status-lookup", response_model=list[LookupItem])
async def list_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StatusLookup).order_by(StatusLookup.id))
    return result.scalars().all()


@app.post("/status-lookup", response_model=LookupItem)
async def create_status(body: dict, db: AsyncSession = Depends(get_db)):
    s = StatusLookup(value=body["value"])
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@app.put("/status-lookup/{sid}", response_model=LookupItem)
async def update_status(sid: int, body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StatusLookup).where(StatusLookup.id == sid))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(404)
    s.value = body["value"]
    await db.commit()
    await db.refresh(s)
    return s


@app.delete("/status-lookup/{sid}")
async def delete_status(sid: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StatusLookup).where(StatusLookup.id == sid))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(404)
    await db.delete(s)
    await db.commit()
    return {"ok": True}


@app.get("/task-type-lookup", response_model=list[LookupItem])
async def list_task_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskTypeLookup).order_by(TaskTypeLookup.id))
    return result.scalars().all()


@app.post("/task-type-lookup", response_model=LookupItem)
async def create_task_type(body: dict, db: AsyncSession = Depends(get_db)):
    t = TaskTypeLookup(value=body["value"])
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@app.put("/task-type-lookup/{tid}", response_model=LookupItem)
async def update_task_type(tid: int, body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskTypeLookup).where(TaskTypeLookup.id == tid))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404)
    t.value = body["value"]
    await db.commit()
    await db.refresh(t)
    return t


@app.delete("/task-type-lookup/{tid}")
async def delete_task_type(tid: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskTypeLookup).where(TaskTypeLookup.id == tid))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404)
    await db.delete(t)
    await db.commit()
    return {"ok": True}


@app.get("/report-periods", response_model=list[ReportPeriodOut])
async def list_periods(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReportPeriod).order_by(ReportPeriod.period_date))
    return result.scalars().all()


@app.post("/report-periods", response_model=ReportPeriodOut)
async def create_period(body: ReportPeriodCreate, db: AsyncSession = Depends(get_db)):
    rp = ReportPeriod(**body.model_dump())
    db.add(rp)
    await db.commit()
    await db.refresh(rp)
    return rp


@app.put("/report-periods/{period_id}", response_model=ReportPeriodOut)
async def update_period(period_id: int, body: ReportPeriodUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ReportPeriod).where(ReportPeriod.id == period_id))
    rp = result.scalar_one_or_none()
    if not rp:
        raise HTTPException(404, "Report period not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(rp, k, v)
    await db.commit()
    await db.refresh(rp)
    return rp


# ─── Dashboard: VP Summary ──────────────────────────────────────────────────

@app.get("/dashboard/vp-summary", response_model=VPSummary)
async def vp_summary(db: AsyncSession = Depends(get_db)):
    # Pillar averages: avg of all tasks in pillar via kpi join
    pillars_res = await db.execute(select(Pillar).order_by(Pillar.code))
    pillars = pillars_res.scalars().all()

    pillar_items = []
    for p in pillars:
        res = await db.execute(
            select(func.avg(Task.pct_complete))
            .join(KPI, Task.kpi_id == KPI.id)
            .where(KPI.pillar_id == p.id)
        )
        val = float(res.scalar() or 0.0)
        pillar_items.append(RAGItem(id=p.id, name=f"{p.code} – {p.name}", pct_complete=val, rag=rag(val)))

    # Team averages
    teams_res = await db.execute(select(Team).order_by(Team.name))
    teams = teams_res.scalars().all()

    team_items = []
    for t in teams:
        res = await db.execute(
            select(func.avg(Task.pct_complete))
            .join(KPI, Task.kpi_id == KPI.id)
            .where(KPI.team_id == t.id)
        )
        val = float(res.scalar() or 0.0)
        team_items.append(RAGItem(id=t.id, name=t.name, pct_complete=val, rag=rag(val)))

    # Overall
    overall_res = await db.execute(select(func.avg(Task.pct_complete)))
    overall = float(overall_res.scalar() or 0.0)

    return VPSummary(pillars=pillar_items, teams=team_items, overall=overall)


# ─── Dashboard: KPI Progress ────────────────────────────────────────────────

@app.get("/dashboard/kpi-progress", response_model=list[KPIProgress])
async def kpi_progress(
    team_id: Optional[int] = None,
    pillar_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(KPI)
    if team_id:
        q = q.where(KPI.team_id == team_id)
    if pillar_id:
        q = q.where(KPI.pillar_id == pillar_id)
    kpis_res = await db.execute(q)
    kpis = kpis_res.scalars().all()

    out = []
    for k in kpis:
        await db.refresh(k, ["pillar", "team"])
        avg_res = await db.execute(
            select(func.avg(Task.pct_complete), func.count(Task.id))
            .where(Task.kpi_id == k.id)
        )
        row = avg_res.one()
        pct = float(row[0] or 0.0)
        count = int(row[1])
        out.append(KPIProgress(
            kpi_code=k.kpi_code, kpi_name=k.kpi_name,
            pillar_code=k.pillar.code, team_name=k.team.name,
            pct_complete=pct, rag=rag(pct), task_count=count,
        ))
    return out


# ─── Dashboard: Pillar View ─────────────────────────────────────────────────

@app.get("/dashboard/pillar-view", response_model=list[PillarViewItem])
async def pillar_view(db: AsyncSession = Depends(get_db)):
    pillars_res = await db.execute(select(Pillar).order_by(Pillar.code))
    pillars = pillars_res.scalars().all()

    out = []
    for p in pillars:
        kpis_res = await db.execute(select(KPI).where(KPI.pillar_id == p.id))
        kpis = kpis_res.scalars().all()

        kpi_items = []
        for k in kpis:
            await db.refresh(k, ["pillar", "team"])
            avg_res = await db.execute(
                select(func.avg(Task.pct_complete), func.count(Task.id))
                .where(Task.kpi_id == k.id)
            )
            row = avg_res.one()
            pct = float(row[0] or 0.0)
            count = int(row[1])
            kpi_items.append(KPIProgress(
                kpi_code=k.kpi_code, kpi_name=k.kpi_name,
                pillar_code=p.code, team_name=k.team.name,
                pct_complete=pct, rag=rag(pct), task_count=count,
            ))

        p_avg_res = await db.execute(
            select(func.avg(Task.pct_complete))
            .join(KPI, Task.kpi_id == KPI.id)
            .where(KPI.pillar_id == p.id)
        )
        p_pct = float(p_avg_res.scalar() or 0.0)

        out.append(PillarViewItem(
            pillar_code=p.code, pillar_name=p.name,
            pct_complete=p_pct, rag=rag(p_pct), kpis=kpi_items,
        ))
    return out


# ─── Dashboard: Task Drill-down ─────────────────────────────────────────────

@app.get("/dashboard/task-drill", response_model=list[TaskDrillItem])
async def task_drill(
    team_id: Optional[int] = None,
    kpi_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Task).order_by(Task.id)
    if kpi_id:
        q = q.where(Task.kpi_id == kpi_id)
    result = await db.execute(q)
    tasks = result.scalars().all()

    out = []
    for t in tasks:
        await db.refresh(t, ["kpi", "status", "task_type", "report_period"])
        if t.kpi:
            await db.refresh(t.kpi, ["pillar", "team"])
        if team_id and (not t.kpi or t.kpi.team_id != team_id):
            continue
        pct = float(t.pct_complete)
        out.append(TaskDrillItem(
            task_id=t.id, task_name=t.task_name,
            kpi_code=t.kpi.kpi_code if t.kpi else "",
            pillar_code=t.kpi.pillar.code if t.kpi and t.kpi.pillar else "",
            team_name=t.kpi.team.name if t.kpi and t.kpi.team else "",
            status=t.status.value if t.status else "",
            pct_complete=pct, rag=rag(pct),
            effort_days=float(t.effort_days) if t.effort_days else None,
            actual_days=float(t.actual_days) if t.actual_days else None,
            blockers=t.blockers, notes=t.notes,
        ))
    return out


# ─── Dashboard: Blocked & At Risk ───────────────────────────────────────────

@app.get("/dashboard/blocked-at-risk", response_model=BlockedAtRisk)
async def blocked_at_risk(db: AsyncSession = Depends(get_db)):
    # Blocked = status == 'Blocked' OR blockers field non-empty
    all_res = await db.execute(select(Task).order_by(Task.id))
    all_tasks = all_res.scalars().all()

    blocked = []
    at_risk = []

    for t in all_tasks:
        await db.refresh(t, ["kpi", "status", "task_type", "report_period"])
        if t.kpi:
            await db.refresh(t.kpi, ["pillar", "team"])
        pct = float(t.pct_complete)
        item = TaskDrillItem(
            task_id=t.id, task_name=t.task_name,
            kpi_code=t.kpi.kpi_code if t.kpi else "",
            pillar_code=t.kpi.pillar.code if t.kpi and t.kpi.pillar else "",
            team_name=t.kpi.team.name if t.kpi and t.kpi.team else "",
            status=t.status.value if t.status else "",
            pct_complete=pct, rag=rag(pct),
            effort_days=float(t.effort_days) if t.effort_days else None,
            actual_days=float(t.actual_days) if t.actual_days else None,
            blockers=t.blockers, notes=t.notes,
        )
        status_val = t.status.value if t.status else ""
        if status_val == "Blocked" or (t.blockers and t.blockers.strip()):
            blocked.append(item)
        elif rag(pct) == "Amber":
            at_risk.append(item)

    return BlockedAtRisk(blocked=blocked, at_risk=at_risk)


# ─── Dashboard: Delays & Slippage ──────────────────────────────────────────

@app.get("/dashboard/delays")
async def delays_dashboard(
    report_period_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Task).order_by(Task.id)
    if report_period_id:
        q = q.where(Task.report_period_id == report_period_id)
    result = await db.execute(q)
    tasks = result.scalars().all()

    total_committed = 0
    on_track = 0
    delayed_tasks = []

    for tsk in tasks:
        await db.refresh(tsk, ["kpi", "status", "task_type", "report_period"])
        if tsk.kpi:
            await db.refresh(tsk.kpi, ["pillar", "team"])

        rp = tsk.report_period
        if not rp or not rp.end_date or not tsk.due_date:
            continue

        total_committed += 1
        pct = float(tsk.pct_complete)

        if tsk.due_date > rp.end_date:
            slippage = (tsk.due_date - rp.end_date).days
            delayed_tasks.append({
                "task_id": tsk.id,
                "task_code": tsk.task_code or "",
                "task_name": tsk.task_name,
                "team": tsk.kpi.team.name if tsk.kpi and tsk.kpi.team else "",
                "pillar": tsk.kpi.pillar.code if tsk.kpi and tsk.kpi.pillar else "",
                "kpi_code": tsk.kpi.kpi_code if tsk.kpi else "",
                "kpi_name": tsk.kpi.kpi_name if tsk.kpi else "",
                "report_period": rp.label,
                "period_end_date": rp.end_date.isoformat(),
                "due_date": tsk.due_date.isoformat(),
                "slippage_days": slippage,
                "pct_complete": pct,
                "rag": rag(pct),
                "status": tsk.status.value if tsk.status else "",
            })
        else:
            on_track += 1

    delayed_tasks.sort(key=lambda x: x["slippage_days"], reverse=True)
    delayed_count = len(delayed_tasks)
    total_slippage = sum(d["slippage_days"] for d in delayed_tasks)
    avg_slippage = round(total_slippage / delayed_count, 1) if delayed_count else 0.0

    team_agg: dict = {}
    for item in delayed_tasks:
        tn = item["team"]
        if tn not in team_agg:
            team_agg[tn] = {"delayed_tasks": 0, "total_slippage_days": 0}
        team_agg[tn]["delayed_tasks"] += 1
        team_agg[tn]["total_slippage_days"] += item["slippage_days"]

    slippage_by_team = sorted([
        {
            "team": tn,
            "delayed_tasks": agg["delayed_tasks"],
            "total_slippage_days": agg["total_slippage_days"],
            "avg_slippage_days": round(agg["total_slippage_days"] / agg["delayed_tasks"], 1),
        }
        for tn, agg in team_agg.items()
    ], key=lambda x: x["total_slippage_days"], reverse=True)

    kpi_agg: dict = {}
    for item in delayed_tasks:
        kc = item["kpi_code"]
        if kc not in kpi_agg:
            kpi_agg[kc] = {"kpi_name": item["kpi_name"], "team": item["team"],
                            "delayed_tasks": 0, "total_slippage_days": 0}
        kpi_agg[kc]["delayed_tasks"] += 1
        kpi_agg[kc]["total_slippage_days"] += item["slippage_days"]

    slippage_by_kpi = sorted([
        {
            "kpi_code": kc,
            "kpi_name": agg["kpi_name"],
            "team": agg["team"],
            "delayed_tasks": agg["delayed_tasks"],
            "total_slippage_days": agg["total_slippage_days"],
        }
        for kc, agg in kpi_agg.items()
    ], key=lambda x: x["total_slippage_days"], reverse=True)

    return {
        "summary": {
            "total_committed": total_committed,
            "on_track": on_track,
            "delayed": delayed_count,
            "avg_slippage_days": avg_slippage,
            "total_slippage_days": total_slippage,
        },
        "delayed_tasks": delayed_tasks,
        "slippage_by_team": slippage_by_team,
        "slippage_by_kpi": slippage_by_kpi,
    }


# ─── Code generation helpers ─────────────────────────────────────────────────

@app.get("/pillars/{pillar_id}/next-kpi-code")
async def next_kpi_code(pillar_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Pillar).where(Pillar.id == pillar_id))
    pillar = result.scalar_one_or_none()
    if not pillar:
        raise HTTPException(404, "Pillar not found")

    codes_result = await db.execute(
        select(KPI.kpi_code).where(KPI.pillar_id == pillar_id)
    )
    existing_codes = [r[0] for r in codes_result.all()]

    prefix = f"KPI.{pillar.code}."
    max_header_seq = 0
    max_kpi_seq_by_header: dict[int, int] = {}

    for code in existing_codes:
        if code.startswith(prefix):
            parts = code[len(prefix):].split(".")
            if len(parts) >= 2:
                try:
                    h, s = int(parts[0]), int(parts[1])
                    max_header_seq = max(max_header_seq, h)
                    max_kpi_seq_by_header[h] = max(max_kpi_seq_by_header.get(h, 0), s)
                except ValueError:
                    pass

    if max_header_seq == 0:
        kpi_code = f"KPI.{pillar.code}.1.1"
        header_code = f"KPI.{pillar.code}.1"
    else:
        next_seq = max_kpi_seq_by_header.get(max_header_seq, 0) + 1
        kpi_code = f"KPI.{pillar.code}.{max_header_seq}.{next_seq}"
        header_code = f"KPI.{pillar.code}.{max_header_seq}"

    return {"kpi_code": kpi_code, "header_code": header_code}


@app.get("/kpis/{kpi_id}/next-task-code")
async def next_task_code(kpi_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KPI.kpi_code).where(KPI.id == kpi_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "KPI not found")
    kpi_code = row

    codes_result = await db.execute(
        select(Task.task_code).where(Task.kpi_id == kpi_id)
    )
    existing_codes = [r[0] for r in codes_result.all() if r[0]]

    prefix = f"{kpi_code}.T"
    max_seq = 0
    for tc in existing_codes:
        if tc.startswith(prefix):
            try:
                max_seq = max(max_seq, int(tc[len(prefix):]))
            except ValueError:
                pass

    return {"task_code": f"{kpi_code}.T{max_seq + 1}"}


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}
