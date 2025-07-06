import argparse

DEFAULT_START_DATE = "2023-07-06"
DEFAULT_END_DATE = "2025-07-03"

parser = argparse.ArgumentParser(description='Run backtest')
parser.add_argument('--start-date', type=str, default=DEFAULT_START_DATE, help='Start date for backtest (YYYY-MM-DD)')
parser.add_argument('--end-date', type=str, default=DEFAULT_END_DATE, help='End date for backtest (YYYY-MM-DD)')

args = parser.parse_args()

start_date = args.start_date
end_date = args.end_date 