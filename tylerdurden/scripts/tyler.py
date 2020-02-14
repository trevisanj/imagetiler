#!/usr/bin/env python
"""Redbuilds image using a bank of very small square images ("tiles")"""


import a107
import argparse
import tylerdurden
import os

def main(args):
    output = a107.new_filename("tyled-"+os.path.splitext(args.input)[0], "jpg")
    print(f"input filename: {args.input}")
    print(f"output filename: {output}")
    print(f"thumbnails directory: {args.thumbnails_dir}")
    print(f"Interactive? {'YES' if args.interactive else 'no'}")
    td = tylerdurden.TylerDurden(args.input, output, args.thumbnails_dir, args.niter, args.interactive)
    td.init()
    td.run()
    td.save()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=a107.SmartFormatter)
    parser.add_argument("-t", "--thumbnails-dir", type=str, help="thumbnails directory", nargs="?",
                        default=tylerdurden.consts.THUMBNAILS_DIR)
    parser.add_argument("-n", "--niter", type=int, help="number of iterations", nargs="?",
                        default=100)
    parser.add_argument("-i", "--interactive", action="store_true", help="interactive mode",
                        )
    parser.add_argument("input", type=str, help="Input filename")

    args = parser.parse_args()
    main(args)
