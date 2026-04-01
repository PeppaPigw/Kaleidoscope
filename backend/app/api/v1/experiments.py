"""Experiment & Method API — first-class research entities (§14 ext)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.experiment import Dataset, Experiment, Method

router = APIRouter(prefix="/experiments", tags=["experiments"])


# ─── Schemas ─────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    paper_id: str | None = None
    name: str
    description: str | None = None
    setup: dict | None = None
    parameters: dict | None = None
    results: dict | None = None
    metrics: dict | None = None
    source: str = "manual"


class MethodCreate(BaseModel):
    name: str
    category: str | None = None
    description: str | None = None
    typical_params: dict | None = None


class DatasetCreate(BaseModel):
    name: str
    url: str | None = None
    description: str | None = None
    domain: str | None = None
    size_description: str | None = None
    license: str | None = None


# ─── Experiment endpoints ────────────────────────────────────────

@router.post("")
async def create_experiment(body: ExperimentCreate, db: AsyncSession = Depends(get_db)):
    exp = Experiment(
        paper_id=body.paper_id,
        name=body.name,
        description=body.description,
        setup=body.setup,
        parameters=body.parameters,
        results=body.results,
        metrics=body.metrics,
        source=body.source,
    )
    db.add(exp)
    await db.flush()
    return _ser_experiment(exp)


@router.get("")
async def list_experiments(
    paper_id: str | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Experiment).order_by(Experiment.created_at.desc()).limit(limit)
    if paper_id:
        query = query.where(Experiment.paper_id == paper_id)
    result = await db.execute(query)
    return [_ser_experiment(e) for e in result.scalars().all()]


# ─── Method endpoints ────────────────────────────────────────────

@router.get("/methods")
async def list_methods(
    category: str | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Method).order_by(Method.paper_count.desc()).limit(limit)
    if category:
        query = query.where(Method.category == category)
    result = await db.execute(query)
    return [_ser_method(m) for m in result.scalars().all()]


@router.post("/methods")
async def create_method(body: MethodCreate, db: AsyncSession = Depends(get_db)):
    method = Method(
        name=body.name,
        category=body.category,
        description=body.description,
        typical_params=body.typical_params,
    )
    db.add(method)
    await db.flush()
    return _ser_method(method)


# ─── Dataset endpoints ───────────────────────────────────────────

@router.get("/datasets")
async def list_datasets(
    domain: str | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Dataset).order_by(Dataset.paper_count.desc()).limit(limit)
    if domain:
        query = query.where(Dataset.domain == domain)
    result = await db.execute(query)
    return [_ser_dataset(d) for d in result.scalars().all()]


@router.post("/datasets")
async def create_dataset(body: DatasetCreate, db: AsyncSession = Depends(get_db)):
    ds = Dataset(
        name=body.name,
        url=body.url,
        description=body.description,
        domain=body.domain,
        size_description=body.size_description,
        license=body.license,
    )
    db.add(ds)
    await db.flush()
    return _ser_dataset(ds)


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(404, "Experiment not found")
    return _ser_experiment(exp)


# ─── Serializers ─────────────────────────────────────────────────

def _ser_experiment(e: Experiment) -> dict:
    return {
        "id": str(e.id), "paper_id": str(e.paper_id) if e.paper_id else None,
        "name": e.name, "description": e.description, "setup": e.setup,
        "parameters": e.parameters, "results": e.results, "metrics": e.metrics,
        "source": e.source, "status": e.status,
        "created_at": str(e.created_at),
    }


def _ser_method(m: Method) -> dict:
    return {
        "id": str(m.id), "name": m.name, "category": m.category,
        "description": m.description, "typical_params": m.typical_params,
        "paper_count": m.paper_count, "created_at": str(m.created_at),
    }


def _ser_dataset(d: Dataset) -> dict:
    return {
        "id": str(d.id), "name": d.name, "url": d.url,
        "description": d.description, "domain": d.domain,
        "size_description": d.size_description, "license": d.license,
        "paper_count": d.paper_count, "created_at": str(d.created_at),
    }
