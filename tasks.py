import time

from loguru import logger


def send_analytics_event(short_code, original_url, timestamp):
	logger.info(
		"Analytics event: {short_code} -> {original_url} at {timestamp}",
		short_code=short_code,
		original_url=original_url,
		timestamp=timestamp,
	)
	time.sleep(1)
	return {"status": "ok", "short_code": short_code}
