"""5교시 역할의 독립 IOC 문자열 일치 실습. 문서용 예제이며 위협 판정이 아니다."""
import json


def match_ioc(education_records, indicator):
    if not isinstance(indicator, str) or not indicator:
        raise ValueError("비교할 IP 지표 문자열이 필요합니다.")
    # 실제 HTTP 원본에는 IP가 없으며 그 원본을 이 교육 분석에 적용하지 않는다.
    return [dict(record) for record in education_records
            if record.get("source") == "ioc_education" and record.get("ip") == indicator]


def run_demo():
    records = [
        {"id": "ioc-demo-1", "source": "ioc_education", "ip": "192.0.2.10"},
        {"id": "ioc-demo-2", "source": "ioc_education", "ip": "198.51.100.20"},
    ]
    comparisons = []
    for indicator in ("192.0.2.10", "203.0.113.10"):
        matches = match_ioc(records, indicator)
        comparisons.append({"indicator": indicator, "matched": bool(matches),
                            "match_count": len(matches), "evidence": [record["id"] for record in matches]})
    return {
        "source": "ioc_education", "records": records, "comparisons": comparisons,
        "limitations": "문서용 IP 문자열의 일치 실습입니다. 실제 HTTP 원본에 IP가 없어 사용자나 요청을 식별할 수 없으며, 공격·침해를 확정하지 않습니다. HTTP 카드와 독립입니다.",
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2))
