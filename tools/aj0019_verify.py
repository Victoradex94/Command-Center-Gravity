"""Read-only local equality CLI. Run: python3 -m tools.aj0019_verify EXPECTED ACTUAL"""
import argparse
import json
from dispatcher.cutover_readiness import read_compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('expected')
    parser.add_argument('actual')
    args = parser.parse_args()
    report = read_compare(args.expected, args.actual)
    print(json.dumps(report, sort_keys=True))
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
