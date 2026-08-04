from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from database import Base


class URL(Base):
	__tablename__ = "urls"

	id = Column(Integer, primary_key=True, index=True)
	original_url = Column(String, nullable=False)
	short_code = Column(String, unique=True, nullable=False, index=True)
	created_at = Column(DateTime, nullable=False, server_default=func.now())
	click_count = Column(Integer, nullable=False, default=0)
	is_active = Column(Boolean, nullable=False, default=True)
