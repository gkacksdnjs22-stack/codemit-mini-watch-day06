import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from scapy.all import rdpcap
from learning.pcap_lab import generate_education_pcap, summarize_pcap
from learning.ioc_lab import match_ioc, run_demo


class EducationTests(unittest.TestCase):
    def test_pcap_roundtrip_and_exact_window_boundaries(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "education.pcap"
            generate_education_pcap(path)
            self.assertEqual(len(rdpcap(str(path))), 6)
            one = summarize_pcap(path, 1)
            five = summarize_pcap(path, 5)
            self.assertEqual((one["packet_count"], one["byte_sum"]), (2, 114))
            self.assertEqual((five["packet_count"], five["byte_sum"]), (5, 360))
            self.assertEqual([float(time) for time in one["relative_times"]], [0, .5])
            self.assertEqual([float(time) for time in five["relative_times"]], [0, .5, 1, 2, 4.999999])
            for window in (0, -1, "NaN", "Infinity"):
                with self.assertRaises(ValueError):
                    summarize_pcap(path, window)

    def test_ioc_exact_strings_preserve_original_and_exclude_http(self):
        records = [
            {"id": "example", "source": "ioc_education", "ip": "192.0.2.10"},
            {"id": "near", "source": "ioc_education", "ip": "192.0.2.100"},
            {"id": "http-1", "source": "http_live"},
            {"id": "http-2", "source": "http_live", "ip": "192.0.2.10"},
        ]
        saved = deepcopy(records)
        matched = match_ioc(records, "192.0.2.10")
        self.assertEqual([record["id"] for record in matched], ["example"])
        self.assertEqual(match_ioc(records, "203.0.113.10"), [])
        matched[0]["ip"] = "changed"
        self.assertEqual(records, saved)
        cases = run_demo()["comparisons"]
        self.assertEqual([case["matched"] for case in cases], [True, False])


if __name__ == "__main__":
    unittest.main()
