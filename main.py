from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from schemas import URLCreate, URLResponse, URLStats
from shortener import create_short_url, get_url_by_code, increment_click


limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
	Base.metadata.create_all(bind=engine)
	yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.post("/shorten", response_model=URLResponse, tags=["Shorten"])
@limiter.limit("10/minute")
def shorten_url(
	request: Request,
	url_data: URLCreate,
	db: Session = Depends(get_db),
):
	del request
	url_record = create_short_url(db, url_data.original_url, url_data.custom_code)
	return URLResponse(
		short_code=url_record.short_code,
		original_url=url_record.original_url,
		short_url=f"http://localhost:8000/{url_record.short_code}",
		created_at=url_record.created_at,
	)


@app.get("/stats/{short_code}", response_model=URLStats, tags=["Stats"])
def read_url_stats(short_code: str, db: Session = Depends(get_db)):
	url_record = get_url_by_code(db, short_code)
	return URLStats(
		short_code=url_record.short_code,
		original_url=url_record.original_url,
		click_count=url_record.click_count,
		created_at=url_record.created_at,
		is_active=url_record.is_active,
	)


@app.delete("/urls/{short_code}", tags=["Management"])
def deactivate_url(short_code: str, db: Session = Depends(get_db)):
	url_record = get_url_by_code(db, short_code)
	url_record.is_active = False
	db.commit()
	db.refresh(url_record)
	return {"message": "URL deactivated"}


@app.get("/{short_code}", response_class=RedirectResponse, tags=["Redirect"])
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
	url_record = get_url_by_code(db, short_code)
	increment_click(db, url_record)
	return RedirectResponse(url=url_record.original_url, status_code=302)