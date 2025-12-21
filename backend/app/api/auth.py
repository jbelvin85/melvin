from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.security import create_access_token, hash_password, verify_password
from ..dependencies import get_current_admin, get_db
from ..models.account_request import AccountRequest, AccountRequestStatus
from ..models.user import User
from ..schemas.auth import (
    AccountRequestCreate,
    AccountRequestOut,
    ApproveRequest,
    LoginRequest,
    TokenResponse,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request", response_model=AccountRequestOut)
def submit_account_request(
    payload: AccountRequestCreate,
    db: Session = Depends(get_db),
) -> AccountRequestOut:
    existing_user = db.query(User).filter(User.username == payload.username).first()
    existing_request = db.query(AccountRequest).filter(AccountRequest.username == payload.username).first()
    if existing_user or existing_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already requested")
    request_record = AccountRequest(
        username=payload.username,
        password_hash=hash_password(payload.password),
        status=AccountRequestStatus.PENDING,
    )
    db.add(request_record)
    db.commit()
    db.refresh(request_record)
    return request_record


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "username": user.username, "admin": user.is_admin})
    return TokenResponse(access_token=token)


@router.get("/requests", response_model=list[AccountRequestOut])
def list_requests(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[AccountRequestOut]:
    return db.query(AccountRequest).filter(AccountRequest.status == AccountRequestStatus.PENDING).all()


@router.post("/requests/{request_id}/approve", response_model=AccountRequestOut)
def approve_request(
    request_id: int,
    _: User = Depends(get_current_admin),
    payload: ApproveRequest | None = None,
    db: Session = Depends(get_db),
) -> AccountRequestOut:
    record = db.get(AccountRequest, request_id)
    if not record or record.status != AccountRequestStatus.PENDING:
        raise HTTPException(status_code=404, detail="Request not found")
    username = payload.approved_username if payload and payload.approved_username else record.username
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=username, password_hash=record.password_hash, is_admin=False)
    db.add(user)
    record.status = AccountRequestStatus.APPROVED
    db.commit()
    db.refresh(record)
    return record


@router.post("/requests/{request_id}/deny", response_model=AccountRequestOut)
def deny_request(
    request_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> AccountRequestOut:
    record = db.get(AccountRequest, request_id)
    if not record or record.status != AccountRequestStatus.PENDING:
        raise HTTPException(status_code=404, detail="Request not found")
    record.status = AccountRequestStatus.DENIED
    db.commit()
    db.refresh(record)
    return record
