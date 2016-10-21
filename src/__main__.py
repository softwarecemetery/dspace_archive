import argparse

import dspace_archive

if (__name__ == "__main__"):

  parser = argparse.ArgumentParser()
  parser.add_argument(
    "action",
    help="action",
    nargs="?",
    choices=["test", "init", "sync"]
  )

  args = parser.parse_args()

  if args.action in ["test"]:
    dspace_archive.test()
  elif args.action in ["init"]:
    dspace_archive.init()
  elif args.action in ["sync"]:
    dspace_archive.sync()
  else:
    parser.print_help()
    exit(-1)

  exit()
