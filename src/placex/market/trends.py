from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


def fetch_google_trends(
    keywords: List[str],
    timeframe: str,
    geo: str,
) -> Dict[str, dict]:
    """
    Fetch Google Trends interest-over-time for keywords.

    Returns:
      {
        "Python": {"dates": [...], "values": [...]},
        ...
      }

    Best-effort: any failure returns an empty dict.

    Note: Google Trends compares at most **5** keywords per request; extra
    keywords are dropped.
    """
    if not keywords:
        return {}

    keywords = [str(k).strip() for k in keywords if str(k).strip()][:5]

    try:
        from pytrends.request import TrendReq  # type: ignore
    except Exception:
        return {}

    try:
        pytrends = TrendReq(hl="en-US", tz=330)  # IST-ish; safe default
        pytrends.build_payload(kw_list=keywords, timeframe=timeframe, geo=geo)
        data = pytrends.interest_over_time()
        if data is None or data.empty:
            return {}

        if "isPartial" in data.columns:
            data = data.drop(columns=["isPartial"])

        out: Dict[str, dict] = {}
        for kw in keywords:
            if kw in data.columns:
                out[kw] = {
                    "dates": [str(d.date()) if hasattr(d, "date") else str(d) for d in data.index],
                    "values": [float(v) for v in data[kw].fillna(0).tolist()],
                }
        return out
    except Exception:
        return {}

