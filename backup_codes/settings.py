
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--api_token', type=str, default='XXX', help='API token for Lasair')
args = parser.parse_args()

API_TOKEN = args.api_token