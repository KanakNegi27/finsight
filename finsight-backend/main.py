from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import database
from schemas import (
    AuthResponse,
    LoginRequest,
    PurchaseCreate,
    RegisterRequest,
    UserPublic,
)
from services import auth
from services.data_quality import check_data_quality
from services.estimator import estimate_missing_expenses
from services.affordability import assess_affordability
from services.forecast import forecast_cash_flow
from services.analysis import analyze_purchases_30_days


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="FinSight API",
    description="Financial affordability with missing-data handling",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class FinancialProfile(BaseModel):
    savings: float | None = Field(default=None, ge=0)
    monthly_income: float | None = Field(default=None, ge=0)
    monthly_expenses: float | None = Field(default=None, ge=0)
    monthly_debt_payments: float | None = Field(default=None, ge=0)
    purchase_amount: float | None = Field(default=None, ge=0)
    emergency_reserve: float | None = Field(default=None, ge=0)

    historical_expenses: list[float] = Field(default_factory=list)
    field_status: dict[str, str] = Field(default_factory=dict)

    pending_refund: float | None = Field(default=None, ge=0)


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header.",
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        user_id = auth.verify_token(token)
    except auth.AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user = database.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="Account not found.")

    return user


@app.get("/")
def home():
    return {
        "message": "Welcome to FinSight API",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    try:
        user = auth.register_user(
            payload.name,
            payload.email,
            payload.password,
        )
    except auth.AuthError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "access_token": auth.create_token(user["id"]),
        "user": auth.public_user(user),
    }


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    try:
        user = auth.authenticate_user(payload.email, payload.password)
    except auth.AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return {
        "access_token": auth.create_token(user["id"]),
        "user": auth.public_user(user),
    }


@app.get("/auth/me", response_model=UserPublic)
def me(current_user: dict = Depends(get_current_user)):
    return auth.public_user(current_user)


@app.get("/profile")
def read_profile(current_user: dict = Depends(get_current_user)):
    return database.get_profile(current_user["id"])


@app.put("/profile")
def write_profile(
    profile: FinancialProfile,
    current_user: dict = Depends(get_current_user),
):
    return database.save_profile(current_user["id"], profile.model_dump())


@app.post("/assess")
def assess(profile: FinancialProfile):
    # Preserve the user's original data for quality checks.
    original = profile.model_dump()

    quality = check_data_quality(original)

    # Work on a separate copy so estimated values are not
    # mistaken for user-confirmed information.
    working = {
        field: original[field]
        for field in [
            "savings",
            "monthly_income",
            "monthly_expenses",
            "monthly_debt_payments",
            "purchase_amount",
            "emergency_reserve",
        ]
    }

    warnings = list(quality["warnings"])
    estimate = None

    if working["monthly_expenses"] is None:
        estimate = estimate_missing_expenses(
            working,
            original["historical_expenses"],
        )

        if estimate["estimated"]:
            working["monthly_expenses"] = estimate["value"]
            warnings.extend(estimate["warnings"])
        else:
            warnings.extend(estimate["warnings"])

    # Pending refunds are deliberately not added to savings.
    if original["pending_refund"] is not None:
        warnings.append(
            "Any pending refund is excluded from available savings."
        )

    affordability = assess_affordability(working)

    forecast = forecast_cash_flow(working, days=90)

    if not forecast["success"]:
        warnings.extend(forecast["warnings"])

    if estimate and estimate["estimated"]:
        affordability["confidence"] = "LOW"
        affordability["warnings"].append(
            "The decision uses estimated expenses. "
            "Confirm the amount before relying on the result."
        )

    if not quality["is_valid"]:
        affordability["confidence"] = "LOW"

    # Remove duplicate warnings while preserving their order.
    warnings = list(dict.fromkeys(warnings))

    return {
        "data_quality": quality,
        "expense_estimate": estimate,
        "affordability": affordability,
        "forecast": forecast,
        "warnings": warnings,
    }


@app.get("/purchases")
def get_purchases(current_user: dict = Depends(get_current_user)):
    return database.list_purchases(current_user["id"])


@app.post("/purchases")
def create_purchase(
    payload: PurchaseCreate,
    current_user: dict = Depends(get_current_user),
):
    return database.add_purchase(
        current_user["id"],
        payload.name,
        payload.category,
        payload.amount,
        payload.days_from_now,
    )


@app.delete("/purchases/{purchase_id}")
def remove_purchase(
    purchase_id: int,
    current_user: dict = Depends(get_current_user),
):
    deleted = database.delete_purchase(current_user["id"], purchase_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Purchase not found.")

    return {"status": "deleted", "id": purchase_id}


@app.get("/analysis/30-days")
def analysis_30_days(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
):
    profile = database.get_profile(current_user["id"]) or {}
    purchases = database.list_purchases(current_user["id"])
    return analyze_purchases_30_days(profile, purchases, days=days)
