import argparse

parser = argparse.ArgumentParser(
    description = "testing"
    )

parser.add_argument(
    "first"
    )
    
parser.add_argument(        
    "--messages",
    type = int
    )

parser.add_argument(        
    "--test",    
    )

args = parser.parse_args()
print(args)