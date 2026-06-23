from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, customers, discounts, items, orders, quote

app = FastAPI(title="Mobile Sys API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(discounts.router, prefix="/api/discounts", tags=["discounts"])
app.include_router(quote.router, prefix="/api/quote", tags=["quote"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
