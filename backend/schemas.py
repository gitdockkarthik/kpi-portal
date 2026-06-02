from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


# ─── Lookup ────────────────────────────────────────────────────────────────

class LookupItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:    int
    value: str


class PillarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:   int
    code: str
    name: str


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:          int
    name:        str
    description: Optional[str] = None


class TeamCreate(BaseModel):
    name:        str
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None


class PillarCreate(BaseModel):
    code: str
    name: str


class PillarUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None


class ReportPeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:          int
    period_date: date
    label:       str
    start_date:  Optional[date] = None
    end_date:    Optional[date] = None


class ReportPeriodCreate(BaseModel):
    period_date: date
    label:       str
    start_date:  Optional[date] = None
    end_date:    Optional[date] = None


class ReportPeriodUpdate(BaseModel):
    period_date: Optional[date] = None
    label:       Optional[str] = None
    start_date:  Optional[date] = None
    end_date:    Optional[date] = None


# ─── KPI ───────────────────────────────────────────────────────────────────

class KPIOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:          int
    kpi_code:    str
    pillar_id:   int
    team_id:     int
    header_code: str
    header_name: str
    kpi_name:    str
    pillar_name: Optional[str] = None
    team_name:   Optional[str] = None


class KPICreate(BaseModel):
    kpi_code:    str
    pillar_id:   int
    team_id:     int
    header_code: str
    header_name: str
    kpi_name:    str


class KPIUpdate(BaseModel):
    kpi_code:    Optional[str] = None
    pillar_id:   Optional[int] = None
    team_id:     Optional[int] = None
    header_code: Optional[str] = None
    header_name: Optional[str] = None
    kpi_name:    Optional[str] = None


# ─── Task ──────────────────────────────────────────────────────────────────

class TaskOut(BaseModel):
    owner: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    id:               int
    kpi_id:           int
    report_period_id: int
    task_code:        Optional[str]
    task_name:        str
    task_type_id:     int
    start_date:       Optional[date]
    due_date:         Optional[date]
    status_id:        int
    pct_complete:     Decimal
    effort_days:      Optional[Decimal]
    actual_days:      Optional[Decimal]
    blockers:         Optional[str]
    notes:            Optional[str]
    created_at:       Optional[datetime]
    updated_at:       Optional[datetime]
    # Resolved labels
    status_value:     Optional[str] = None
    task_type_value:  Optional[str] = None
    kpi_code:         Optional[str] = None
    kpi_name:         Optional[str] = None
    pillar_code:      Optional[str] = None
    team_name:        Optional[str] = None
    period_label:     Optional[str] = None


class TaskCreate(BaseModel):
    owner: Optional[str] = None
    kpi_id:           int
    report_period_id: int
    task_code:        Optional[str] = None
    task_name:        str
    task_type_id:     int
    start_date:       Optional[date] = None
    due_date:         Optional[date] = None
    status_id:        int
    pct_complete:     Decimal = Decimal("0.0")
    effort_days:      Optional[Decimal] = None
    actual_days:      Optional[Decimal] = None
    blockers:         Optional[str] = None
    notes:            Optional[str] = None


class TaskUpdate(BaseModel):
    owner: Optional[str] = None
    kpi_id:           Optional[int] = None
    report_period_id: Optional[int] = None
    task_code:        Optional[str] = None
    task_name:        Optional[str] = None
    task_type_id:     Optional[int] = None
    start_date:       Optional[date] = None
    due_date:         Optional[date] = None
    status_id:        Optional[int] = None
    pct_complete:     Optional[Decimal] = None
    effort_days:      Optional[Decimal] = None
    actual_days:      Optional[Decimal] = None
    blockers:         Optional[str] = None
    notes:            Optional[str] = None


# ─── Dashboard aggregates ───────────────────────────────────────────────────

class RAGItem(BaseModel):
    id:           int
    name:         str
    pct_complete: float
    rag:          str   # Green | Amber | Red


class VPSummary(BaseModel):
    pillars: list[RAGItem]
    teams:   list[RAGItem]
    overall: float


class KPIProgress(BaseModel):
    kpi_code:    str
    kpi_name:    str
    pillar_code: str
    team_name:   str
    pct_complete: float
    rag:          str
    task_count:   int


class PillarViewItem(BaseModel):
    pillar_code:  str
    pillar_name:  str
    pct_complete: float
    rag:          str
    kpis:         list[KPIProgress]


class TaskDrillItem(BaseModel):
    task_id:      int
    task_name:    str
    kpi_code:     str
    pillar_code:  str
    team_name:    str
    status:       str
    pct_complete: float
    rag:          str
    effort_days:  Optional[float]
    actual_days:  Optional[float]
    blockers:     Optional[str]
    notes:        Optional[str]


class BlockedAtRisk(BaseModel):
    blocked: list[TaskDrillItem]
    at_risk: list[TaskDrillItem]
