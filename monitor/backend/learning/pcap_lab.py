"""4교시 역할의 독립 PCAP 실습. 패킷을 파일로만 만들며 전송·실제 캡처하지 않는다."""
import argparse
import json
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from scapy.all import Ether, IP, UDP, Raw, rdpcap, wrpcap


def generate_education_pcap(path):
    """문서용 주소와 고정 교육 시각으로 여섯 프레임을 생성한다."""
    packets = []
    for index, (offset, payload_size) in enumerate([
        ("0", 10), ("0.5", 20), ("1", 30), ("2", 40), ("4.999999", 50), ("5", 60),
    ]):
        packet = (Ether(src="02:00:00:00:00:01", dst="02:00:00:00:00:02")
                  / IP(src="192.0.2.10", dst="198.51.100.20", id=index + 1)
                  / UDP(sport=12000 + index, dport=9999)
                  / Raw(load=b"E" * payload_size))
        packet.time = Decimal("1700000000") + Decimal(offset)
        packets.append(packet)
    wrpcap(str(path), packets)


def summarize_pcap(path, window_seconds):
    """첫 프레임 시각부터 [0, window) 구간의 저장된 프레임 수와 바이트 합."""
    window = Decimal(str(window_seconds))
    if not window.is_finite() or window <= 0:
        raise ValueError("관찰 구간은 양수의 유한한 초 단위 값이어야 합니다.")
    packets = rdpcap(str(path))
    if not packets:
        return {"source": "pcap_education", "window_seconds": str(window), "packet_count": 0, "byte_sum": 0, "relative_times": []}
    start = Decimal(str(packets[0].time))
    selected = [packet for packet in packets if Decimal("0") <= Decimal(str(packet.time)) - start < window]
    return {
        "source": "pcap_education", "window_seconds": str(window),
        "packet_count": len(selected), "byte_sum": sum(len(bytes(packet)) for packet in selected),
        "relative_times": [str(Decimal(str(packet.time)) - start) for packet in selected],
    }


def run_demo(path):
    generate_education_pcap(path)
    return {
        "description": "직접 생성한 교육용 PCAP이며 실제 게시판 캡처가 아닙니다. HTTP 카드에 합치지 않습니다.",
        "generated_packets": 6,
        "comparisons": [summarize_pcap(path, seconds) for seconds in (5, 1)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="교육용 PCAP을 저장할 경로. 생략하면 임시 파일 생성 후 정리")
    args = parser.parse_args()
    if args.output is None:
        with TemporaryDirectory(prefix="mini-watch-pcap-education-") as directory:
            result = run_demo(Path(directory) / "education.pcap")
    else:
        result = run_demo(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
