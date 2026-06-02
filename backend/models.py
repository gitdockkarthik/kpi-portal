from sqlalchemy import Column, Integer, String, Text, Date, Numeric, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database import Base


class Pillar(Base):
    __tablename__ = "pillars"
    id   = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    kpis = relationship("KPI", back_populates="pillar")


class Team(Base):
    __tablename__ = "teams"
    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    kpis        = relationship("KPI", back_populates="team")


class KPI(Base):
    __tablename__ = "kpis"
    id          = Column(Integer, primary_key=True)
    kpi_code    = Column(String(50), nullable=False, unique=True)
    pillar_id   = Column(Integer, ForeignKey("pillars.id"), nullable=False)
    team_id     = Column(Integer, ForeignKey("teams.id"), nullable=False)
    header_code = Column(String(50), nullable=False)
    header_name = Column(String(200), nullable=False)
    kpi_name    = Column(String(200), nullable=False)
    pillar      = relationship("Pillar", back_populates="kpis")
    team        = relationship("Team", back_populates="kpis")
    tasks       = relationship("Task", back_populates="kpi")


class ReportPeriod(Base):
    __tablename__ = "report_periods"
    id          = Column(Integer, primary_key=True)
    period_date = Column(Date, nullable=False)
    label       = Column(String(50), nullable=False)
    start_date  = Column(Date, nullable=True)
    end_date    = Column(Date, nullable=True)
    tasks       = relationship("Task", back_populates="report_period")


class StatusLookup(Base):
    __tablename__ = "status_lookup"
    id    = Column(Integer, primary_key=True)
    value = Column(String(50), nullable=False, unique=True)
    tasks = relationship("Task", back_populates="status")


class TaskTypeLookup(Base):
    __tablename__ = "task_type_lookup"
    id    = Column(Integer, primary_key=True)
    value = Column(String(50), nullable=False, unique=True)
    tasks = relationship("Task", back_populates="task_type")


class Task(Base):
    __tablename__ = "tasks"
    id               = Column(Integer, primary_key=True)
    kpi_id           = Column(Integer, ForeignKey("kpis.id"), nullable=False)
    report_period_id = Column(Integer, ForeignKey("report_periods.id"), nullable=False)
    task_code        = Column(String(50))
    task_name        = Column(String(200), nullable=False)
    task_type_id     = Column(Integer, ForeignKey("task_type_lookup.id"), nullable=False)
    start_date       = Column(Date)
    due_date         = Column(Date)
    status_id        = Column(Integer, ForeignKey("status_lookup.id"), nullable=False)
    pct_complete     = Column(Numeric(4, 2), nullable=False, default=0.0)
    effort_days      = Column(Numeric(6, 2))
    actual_days      = Column(Numeric(6, 2))
    blockers         = Column(Text)
    notes            = Column(Text)
    owner         = Column(String(100))
    created_at       = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at       = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    kpi           = relationship("KPI", back_populates="tasks", lazy="selectin")
    report_period = relationship("ReportPeriod", back_populates="tasks", lazy="selectin")
    status        = relationship("StatusLookup", back_populates="tasks", lazy="selectin")
    task_type     = relationship("TaskTypeLookup", back_populates="tasks", lazy="selectin")
