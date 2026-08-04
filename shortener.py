import random
import string

from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import URL


def generate_short_code(length=6):
	characters = string.ascii_letters + string.digits
	return "".join(random.choice(characters) for _ in range(length))


def create_short_url(db: Session, original_url, custom_code=None):
	if custom_code:
		existing_url = db.query(URL).filter(URL.short_code == custom_code).first()
		if existing_url:
			raise HTTPException(status_code=409, detail="Short code already exists")
		short_code = custom_code
	else:
		short_code = generate_short_code()
		while db.query(URL).filter(URL.short_code == short_code).first():
			short_code = generate_short_code()

	url_record = URL(original_url=str(original_url), short_code=short_code)
	db.add(url_record)
	db.commit()
	db.refresh(url_record)
	return url_record


def get_url_by_code(db: Session, short_code):
	url_record = db.query(URL).filter(URL.short_code == short_code).first()
	if not url_record:
		raise HTTPException(status_code=404, detail="URL not found")
	return url_record


def increment_click(db: Session, url_record):
	url_record.click_count += 1
	db.commit()
	db.refresh(url_record)
	return url_record
