#!/usr/bin/env python
"""
List the Proposals in an instance sorted by the number of comments.
"""

from adhocracy.model import Proposal

# boilerplate code. copy that
import os
import sys
sys.path.insert(0,  os.path.abspath(os.path.dirname(__file__)))
from common import create_parser, get_instances, load_from_args
# /end boilerplate code


def main():
    parser = create_parser(description=__doc__)
    args = parser.parse_args()
    load_from_args(args)
    instances = get_instances(args)

    for instance in instances:
        proposals = Proposal.all_q(instance=instance)
        proposals = sorted(proposals, key=lambda x: x.comment_count(),
                           reverse=True)

        print instance.label
        for proposal in proposals:
            print "%s: %s" % (proposal.comment_count(), proposal.title)

if __name__ == '__main__':
    sys.exit(main())
