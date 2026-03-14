#!/usr/bin/env python3
"""One-off: 清空 openclaw_api_keys 表，使 OpenClaw 数量归零。需 DATABASE_URL。"""

import os
import sys
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import create_engine, text


def main():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("Usage: DATABASE_URL='...' python scripts/clear_openclaw_keys.py", file=sys.stderr)
        sys.exit(1)
    parsed = urlparse(url)
    if parsed.scheme and "postgresql" in parsed.scheme:
        query = parse_qs(parsed.query)
        if "sslmode" not in query:
            query["sslmode"] = ["prefer"]
            parsed = parsed._replace(query=urlencode(query, doseq=True))
        url = urlunparse(parsed)
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        r = conn.execute(text("DELETE FROM openclaw_api_keys"))
        conn.commit()
        n = r.rowcount
    print(f"已清空 OpenClaw 数量：删除 openclaw_api_keys 共 {n} 条。")


if __name__ == "__main__":
    main()
