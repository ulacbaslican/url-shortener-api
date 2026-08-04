from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class URLCreate(BaseModel):
	original_url: HttpUrl
	custom_code: str | None = None

	model_config = ConfigDict(from_attributes=True)


class URLResponse(BaseModel):
	short_code: str
	original_url: str
	short_url: str
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)


class URLStats(BaseModel):
	short_code: str
	original_url: str
	click_count: int
	created_at: datetime
	is_active: bool

	model_config = ConfigDict(from_attributes=True)
