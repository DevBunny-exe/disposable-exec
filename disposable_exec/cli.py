import argparse
from disposable_exec import run

def main():
    parser = argparse.ArgumentParser(
        prog="disposable",
        description="Execute Python code in Disposable sandbox"
    )

    subparsers = parser.add_subparsers(dest="command")

    run_cmd = subparsers.add_parser("run", help="Run python code")
    run_cmd.add_argument("code", help="Python code string")

    args = parser.parse_args()

    if args.command == "run":
        result = run(args.code)
        print(result["stdout"], end="")

if __name__ == "__main__":
    main()