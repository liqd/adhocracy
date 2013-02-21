#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import socket
import struct
import glob
import re
import sys
import time
import signal

_STATE_LISTEN = '0A'

_NETSTAT_FILES_TCP = ['/proc/net/tcp', '/proc/net/tcp6']

def _signalByName(name):
    try:
        return int(name)
    except ValueError:
        pass
    signames = dict((k, v) for k,v in signal.__dict__.iteritems() if k.startswith('SIG'))
    if name in signames:
        return signames[name]
    sname = 'SIG_' + name
    if sname in signames:
        return signames[sname]
    sname = 'SIG' + name
    if sname in signames:
        return signames[sname]
    raise ValueError('Cannot find signal ' + str(name))

def _parseIpPort(kernelStr):
    ipStr,_,portStr = kernelStr.partition(':')
    port = int(portStr, 16)
    ipInt = int(ipStr, 16)
    if len(ipStr) == 8: # IPv4
        ip = socket.inet_ntop(socket.AF_INET, struct.pack('=I', ipInt))
    else: # IPv6
        ip = socket.inet_ntop(socket.AF_INET6, struct.pack('=IIII',
            ((ipInt >> 96) & 0xffffffff),
            ((ipInt >> 64) & 0xffffffff),
            ((ipInt >> 32) & 0xffffffff),
            ((ipInt >> 0) & 0xffffffff)
        ))
    return ip,port

class NoProcessException(BaseException):
    pass

def netstat(includePrograms=True, sourceFiles=_NETSTAT_FILES_TCP):
    """ Returns a list of dictionaries with the following properties:
        proto: The procotol name ('tcp' or 'tcp6')
        port: The port number the application is listening on
        pid: The process ID
        pgid: The process group ID
        exe: executable name of the program in question
    """
    res = []
    for sfn in sourceFiles:
        with open(sfn) as sf:
            proto = os.path.basename(sfn)
            next(sf) # Skip header line

            for line in sf:
                entries = line.split()
                state = entries[3]
                sockId = entries[9]
                if state != _STATE_LISTEN:
                    continue

                local_ip,local_port = _parseIpPort(entries[1])

                d = {
                    'proto': proto,
                    'port': local_port,
                    'local_address': local_ip,
                    'sockId': sockId,
                }
                res.append(d)
    if includePrograms:
        for fdFile in glob.iglob('/proc/[0-9]*/fd/*'):
            pid = int(fdFile.split('/')[2])
            try:
                linkTarget = os.readlink(fdFile)
            except OSError:
                continue

            m = re.match('^socket:\[(?P<sockId>[0-9]+)\]$', linkTarget)
            if m is not None:
                sockId = m.group('sockId')
                for d in res:
                    if d['sockId'] == sockId:
                        d['pid'] = pid
                        try:
                            d['exe'] = os.readlink('/proc/' + str(pid) + '/exe')
                        except OSError:
                            pass
                        try:
                            with open('/proc/' + str(pid) + '/stat') as statf:
                                d['pgid'] = int(statf.read().split()[4])
                        except IOError:
                            pass

    return res

def checkOnce(ports, opts_open=False, opts_kill='dont', opts_killSignal=signal.SIGTERM):
    nstat = netstat()
    errors = []
    messages = []
    for p in ports:
        matchingDicts = list(filter(lambda d: d['port'] == p, nstat))
        if len(matchingDicts) == 0:
            if opts_open:
                errors.append('Port %s not taken by any program' % p)
        else:
            if not opts_open:
                d = matchingDicts[0]
                bexename = os.path.basename(d.get('exe', '-'))

                errors.append('Port %s taken by %s/%s' % (d['port'], d.get('pid', '-'), bexename))
                if opts_kill == 'pid':
                    if 'pid' not in d:
                        raise NoProcessException('Cannot find process occupying port %s - are you root?' % d['port'])
                    messages.append('Killing pid ' + str(d['pid']) + ' (' + bexename + ' bound to ' + d['local_address'] + ':' + str(d['port']) + ')')
                    os.kill(d['pid'], opts_killSignal)
                elif opts_kill == 'pgid':
                    if 'pgid' not in d:
                        raise NoProcessException('Cannot find process group occupying port %s - are you root?' % d['port'])
                    messages.append('Killing pgid ' + str(d['pgid']) + ' (' + bexename + ' bound to ' + d['local_address'] + ':' + str(d['port']) + ')')
                    os.killpg(d['pgid'], opts_killSignal)
    return messages,errors

def check_port_free(ports, message_printer=None, opts_gracePeriod=0, opts_graceInterval=1, opts_open=False, opts_kill='dont', opts_killSignal=signal.SIGTERM):
    if message_printer is None:
        message_printer = lambda messages: None
    remaining_grace = opts_gracePeriod
    while True:
        messages,errors = checkOnce(ports, opts_open, opts_kill, opts_killSignal)
        if messages:
            message_printer(messages)
        if not errors or remaining_grace <= 0:
            break
        if messages:
            message_printer(messages)

        sleepTime = min(remaining_grace, opts_graceInterval)
        time.sleep(sleepTime)
        remaining_grace -= sleepTime
    if errors:
        message_printer(errors)
    return errors


# TODO pgroup
def main():
    from optparse import OptionParser
    parser = OptionParser(usage='usage: %prog [options] port [port..]')
    parser.add_option('-o', '--open', dest='open', action='store_true', default=False, help='require ports to be opened by a process instead of free')
    parser.add_option('-k', '--kill-pid', dest='kill', action='store_const', const='pid', default=None, help='kill offending processes by process id')
    parser.add_option('--kill-pgid', dest='kill', action='store_const', const='pgid', default=None, help='kill the offending process groups')
    parser.add_option('--kill-signal', dest='killSignalStr', default=signal.SIGTERM, help='Use the specified signal instead of SIGTERM', metavar='SIGNAL')
    parser.add_option('-g', '--grace-period', dest='gracePeriod', type='float', default=0, help='Seconds to wait for the condition to be fulfilled', metavar='SECONDS')
    parser.add_option('--grace-interval', dest='graceInterval', type='float', default=1, help='Check every n seconds', metavar='SECONDS')
    (opts, args) = parser.parse_args()

    ports = list(map(int, args))
    if not ports:
        parser.error('Need at least one port to test')
    opts.killSignal = _signalByName(opts.killSignalStr)
    message_printer = lambda messages: print('\n'.join(messages))

    try:
        errors = check_port_free(ports, message_printer,
            opts_gracePeriod=opts.gracePeriod, opts_graceInterval=opts.graceInterval,
            opts_open=opts.open, opts_kill=opts.kill, opts_killSignal=opts.killSignal)
    except NoProcessException as ne:
        sys.stderr.write(ne.message + '\n')
        sys.exit(4)
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()

