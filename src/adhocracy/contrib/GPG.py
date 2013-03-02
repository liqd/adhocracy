""" A wrapper for the 'gpg' command.  

We're wrapping gpg instead of using, for example, cryptlib, in order
to reduce dependencies and cut down on the amount of code which
institutional ISconf users would have to audit before installing.
This portability will cost slightly us in terms of performance due to
the fact that we have to fork 'gpg' one or more times for each message
processed.  I don't expect ISconf4 message rates to be high enough for
this to matter.  If and when we start chunking files and managing
large blobs like install images with ISconf, this will likely have to
change.

This is a generic wrapper and is not ISconf-specific -- feel free to
use it in your own applications, and see the pycrypto license below.  

Portions of this module are derived from A.M. Kuchling's well-designed
GPG.py, using Richard Jones' updated version 1.3, which can be found
in the pycrypto CVS repository on Sourceforge:

    http://cvs.sourceforge.net/viewcvs.py/pycrypto/gpg/GPG.py

This module is *not* forward-compatible with amk's; some of the
old interface has changed.  For instance, since I've added decrypt
functionality, I elected to initialize with a 'gnupghome' argument
instead of 'keyring', so that gpg can find both the public and secret
keyrings.  I've also altered some of the returned objects in order for
the caller to not have to know as much about the internals of the
result classes.

While the rest of ISconf is released under the GPL, I am releasing
this single file under the same terms that A.M. Kuchling used for
pycrypto:

_____________________ pycrypto LICENSE file starts __________________________
===================================================================
Distribute and use freely; there are no restrictions on further
dissemination and usage except those imposed by the laws of your
country of residence.  This software is provided "as is" without
warranty of fitness for use or suitability for any purpose, express
or implied. Use at your own risk or not at all.
===================================================================

Incorporating the code into commercial products is permitted; you do
not have to make source available or contribute your changes back
(though that would be nice).

--amk                                                             (www.amk.ca)
_______________________ pycrypto LICENSE file ends __________________________



Steve Traugott, stevegt@terraluna.org
Thu Jun 23 21:27:20 PDT 2005

    
"""

import os
import StringIO
import popen2

class GPG:

    def __init__(self, gpgbinary='gpg', gnupghome=None, verbose=False):
        """Initialize a GPG process wrapper.  Options are:

        gpgbinary -- full pathname for GPG binary.  

        gnupghome -- full pathname to where we can find the public and
        private keyrings.  Default is whatever gpg defaults to.
    
        >>> gpg = GPG(gnupghome="/tmp/pygpgtest")

        """
        self.gpgbinary = gpgbinary
        self.gnupghome = gnupghome
        self.verbose = verbose
        if gnupghome and not os.path.isdir(self.gnupghome):
            os.makedirs(self.gnupghome,0700)
        # if not os.path.isfile(self.gnupghome + "/secring.gpg"):
        #     self.gen_key()

    def _open_subprocess(self, args, passphrase=None):
        # Internal method: open a pipe to a GPG subprocess and return
        # the file objects for communicating with it.
        cmd = [self.gpgbinary, '--status-fd 2 --no-tty']
        if self.gnupghome:
            cmd.append('--homedir "%s" ' % self.gnupghome)
        if passphrase:
            cmd.append('--passphrase-fd 3')

        cmd.extend(args)
        cmd = ' '.join(cmd)
        if self.verbose: 
            print cmd

        child_stdout, child_stdin, child_stderr, child_pass = \
            PopenHi.open(cmd, 3)
        if passphrase:
            child_pass.write(passphrase + "\n")
            child_pass.close()
        return child_stdout, child_stdin, child_stderr

    def _read_response(self, child_stderr, response):
        # Internal method: reads all the output from GPG, taking notice
        # only of lines that begin with the magic [GNUPG:] prefix.
        # 
        # Calls methods on the response object for each valid token found,
        # with the arg being the remainder of the status line.
        response.stderr = ''
        while 1:
            line = child_stderr.readline()
            response.stderr += line
            if self.verbose: print line
            if line == "": break
            line = line.rstrip()
            if line[0:9] == '[GNUPG:] ':
                # Chop off the prefix
                line = line[9:]
                L = line.split(None, 1)
                keyword = L[0]
                if len(L) > 1:
                    value = L[1]
                else:
                    value = ""
                getattr(response, keyword)(value)

    def _handle_gigo(self, args, file, result,passphrase=None):
        # Handle a basic data call - pass data to GPG, handle the output
        # including status information. Garbage In, Garbage Out :)
        child_stdout, child_stdin, child_stderr = \
            self._open_subprocess(args,passphrase)

        # Copy the file to the GPG subprocess
        while 1:
            data = file.read(1024)
            if data == "": break
            child_stdin.write(data)
        child_stdin.close()

        # Get the response information
        self._read_response(child_stderr, result)
        self._read_data(child_stdout, result)

        return result
    
    def _read_data(self,child_stdout,result):
        # Read the contents of the file from GPG's stdout
        result.data = ""
        while 1:
            data = child_stdout.read(1024)
            if data == "": break
            result.data = result.data + data
    
    #
    # SIGNATURE METHODS
    #
    def sign(self,message,keyid=None,passphrase=None,clearsign=True):
        """sign message"""
        
        args = ["-sa"]
        if clearsign:
            args.append("--clearsign")
        if keyid:
            args.append("--default-key %s" % keyid)
        child_stdout, child_stdin, child_stderr = \
            self._open_subprocess(args,passphrase=passphrase)
        child_stdin.write(message)
        child_stdin.close()
        # Get the response information
        result = Sign()
        self._read_response(child_stderr, result)
        self._read_data(child_stdout, result)
        return result
        
    def verify(self, data):
        """Verify the signature on the contents of the string 'data'

        >>> gpg = GPG(gnupghome="/tmp/pygpgtest")
        >>> input = gpg.gen_key_input(Passphrase='foo')
        >>> key = gpg.gen_key(input)
        >>> assert key 
        >>> sig = gpg.sign('hello',keyid=key.fingerprint,passphrase='bar')
        >>> assert not sig
        >>> sig = gpg.sign('hello',keyid=key.fingerprint,passphrase='foo')
        >>> assert sig
        >>> verify = gpg.verify(str(sig))
        >>> assert verify

        """

        file = StringIO.StringIO(data)
        return self.verify_file(file)
    
    def verify_file(self, file):
        "Verify the signature on the contents of the file-like object 'file'"
        sig = Verify()
        self._handle_gigo([], file, sig)
        return sig

    #
    # KEY MANAGEMENT
    #

    def import_key(self, key_data):
        """ import the key_data into our keyring 

        >>> import shutil
        >>> shutil.rmtree("/tmp/pygpgtest")
        >>> gpg = GPG(gnupghome="/tmp/pygpgtest")
        >>> input = gpg.gen_key_input()
        >>> result = gpg.gen_key(input)
        >>> print1 = result.fingerprint
        >>> result = gpg.gen_key(input)
        >>> print2 = result.fingerprint
        >>> pubkey1 = gpg.export_key(print1)
        >>> seckey1 = gpg.export_key(print1,secret=True)
        >>> seckeys = gpg.list_keys(secret=True)
        >>> pubkeys = gpg.list_keys()
        >>> assert print1 in seckeys.fingerprints
        >>> assert print1 in pubkeys.fingerprints
        >>> gpg.delete_key(print1,secret=True)
        ''
        >>> gpg.delete_key(print1)
        ''
        >>> seckeys = gpg.list_keys(secret=True)
        >>> pubkeys = gpg.list_keys()
        >>> assert not print1 in seckeys.fingerprints
        >>> assert not print1 in pubkeys.fingerprints
        >>> result = gpg.import_key('foo')
        >>> assert not result
        >>> result = gpg.import_key(pubkey1)
        >>> pubkeys = gpg.list_keys()
        >>> seckeys = gpg.list_keys(secret=True)
        >>> assert not print1 in seckeys.fingerprints
        >>> assert print1 in pubkeys.fingerprints
        >>> result = gpg.import_key(seckey1)
        >>> assert result
        >>> seckeys = gpg.list_keys(secret=True)
        >>> pubkeys = gpg.list_keys()
        >>> assert print1 in seckeys.fingerprints
        >>> assert print1 in pubkeys.fingerprints
        >>> assert print2 in pubkeys.fingerprints

        """
        child_stdout, child_stdin, child_stderr = \
            self._open_subprocess(['--import'])

        child_stdin.write(key_data)
        child_stdin.close()

        # Get the response information
        result = ImportResult()
        resp = self._read_response(child_stderr, result)

        return result

    def delete_key(self,fingerprint,secret=False):
        which='key'
        if secret:
            which='secret-key'
        args = ["--batch --delete-%s %s" % (which,fingerprint)]
        child_stdout, child_stdin, child_stderr = \
            self._open_subprocess(args)
        child_stdin.close()
        # XXX might want to check more status here
        return child_stdout.read()

    def export_key(self,keyid,secret=False):
        """export the indicated key -- 'keyid' is anything gpg accepts"""
        which=''
        if secret:
            which='-secret-key'
        args = ["--armor --export%s %s" % (which,keyid)]
        child_stdout, child_stdin, child_stderr = \
            self._open_subprocess(args)
        child_stdin.close()
        # gpg --export produces no status-fd output; stdout will be
        # empty in case of failure
        return child_stdout.read()

    def list_keys(self,secret=False):
        """ list the keys currently in the keyring 

        >>> import shutil
        >>> shutil.rmtree("/tmp/pygpgtest")
        >>> gpg = GPG(gnupghome="/tmp/pygpgtest")
        >>> input = gpg.gen_key_input()
        >>> result = gpg.gen_key(input)
        >>> print1 = result.fingerprint
        >>> result = gpg.gen_key(input)
        >>> print2 = result.fingerprint
        >>> pubkeys = gpg.list_keys()
        >>> assert print1 in pubkeys.fingerprints
        >>> assert print2 in pubkeys.fingerprints
        
        """

        which='keys'
        if secret:
            which='secret-keys'
        args = "--list-%s --fixed-list-mode --fingerprint --with-colons" % (which)
        args = [args]
        child_stdout, child_stdin, child_stderr = \
            self._open_subprocess(args)
        child_stdin.close()

        # there might be some status thingumy here I should handle... (amk)
        # ...nope, unless you care about expired sigs or keys (stevegt)

        # Get the response information
        result = ListKeys()
        valid_keywords = 'pub uid sec fpr'.split()
        while 1:
            line = child_stdout.readline()
            if self.verbose: print line
            if not line:
                break
            L = line.strip().split(':')
            if not L:
                continue
            keyword = L[0]
            if keyword in valid_keywords:
                getattr(result, keyword)(L)
        return result

    def gen_key(self,input):
        """Generate a key; you might use gen_key_input() to create the
        control input.
        
        >>> gpg = GPG(gnupghome="/tmp/pygpgtest")
        >>> input = gpg.gen_key_input()
        >>> result = gpg.gen_key(input)
        >>> assert result 
        >>> result = gpg.gen_key('foo')
        >>> assert not result 
        
        """
        args = ["--gen-key --batch"]
        result = GenKey()
        file = StringIO.StringIO(input)
        self._handle_gigo(args, file, result)
        return result

    def gen_key_input(self,**kwargs):
        """
        Generate --gen-key input per gpg doc/DETAILS

        """
        parms = {}
        for (key,val) in kwargs.items():
            key = key.replace('_','-')
            parms[key] = val
        parms.setdefault('Key-Type','RSA')
        parms.setdefault('Key-Length',1024)
        parms.setdefault('Name-Real', "Autogenerated Key")
        parms.setdefault('Name-Comment', "Generated by isconf.GPG")
        logname = os.environ['LOGNAME']
        import socket
        hostname = socket.gethostname()
        parms.setdefault('Name-Email', "%s@%s" % (logname,hostname))
        out = "Key-Type: %s\n" % parms['Key-Type']
        del parms['Key-Type']
        for (key,val) in parms.items():
            out += "%s: %s\n" % (key, str(val))
        out += "%commit\n"
        return out
        
        # Key-Type: RSA
        # Key-Length: 1024
        # Name-Real: ISdlink Server on %s
        # Name-Comment: Created by %s
        # Name-Email: isdlink@%s
        # Expire-Date: 0
        # %commit
        #
        #
        # Key-Type: DSA
        # Key-Length: 1024
        # Subkey-Type: ELG-E
        # Subkey-Length: 1024
        # Name-Real: Joe Tester
        # Name-Comment: with stupid passphrase
        # Name-Email: joe@foo.bar
        # Expire-Date: 0
        # Passphrase: abc
        # %pubring foo.pub
        # %secring foo.sec
        # %commit


    def import_keys(self,keydata,filter=None):
        """import a set of keys, but only if filter(fingerprint)
        is true for all of them

        XXX test filter 

        """
        args = "--with-fingerprint --with-colons" % self.path
        args = [args]
        result = ListKeys()
        file = StringIO.StringIO(keydata)
        self._handle_gigo(args, file, result)
        for key in result:
            if filter and not filter(key.fingerprint):
                return None
        return self.import_key(keydata)

    def showpubkey(self,i=0):
        """return the ascii armored public key for the first key on
        the secret ring, or the 'i'th key if given

        XXX test

        """
        keys = self.list_keys(secret=True)
        primary = keys[i]
        ascii = self.export_key(keyid=primary['keyid'])
        return ascii

    def fingerprints(self,keyid='',secret=False):
        keys = self.list_keys(secret=True)
        return keys.fingerprints

    #
    # ENCRYPTION
    #
    def encrypt_file(self, file, recipients, sign=None, 
            always_trust=False, passphrase=None):
        "Encrypt the message read from the file-like object 'file'"
        args = ['--encrypt --armor']
        if not (isinstance(recipients,list) or isinstance(recipients,tuple)):
            recipients = [recipients]
        for recipient in recipients:
            args.append('--recipient %s' % recipient)
        if sign:
            args.append("--sign --default-key %s" % sign)
        if always_trust:
            args.append("--always-trust")
        result = Crypt()
        self._handle_gigo(args, file, result, passphrase=passphrase)
        return result

    def encrypt(self, data, recipients, **kwargs):
        """Encrypt the message contained in the string 'data'

        >>> import shutil
        >>> if os.path.exists("/tmp/pygpgtest"): 
        ...     shutil.rmtree("/tmp/pygpgtest")
        >>> gpg = GPG(gnupghome="/tmp/pygpgtest")
        >>> input = gpg.gen_key_input(passphrase='foo')
        >>> result = gpg.gen_key(input)
        >>> print1 = result.fingerprint
        >>> input = gpg.gen_key_input()
        >>> result = gpg.gen_key(input)
        >>> print2 = result.fingerprint
        >>> result = gpg.encrypt("hello",print2)
        >>> message = str(result)
        >>> assert message != 'hello'
        >>> result = gpg.decrypt(message)
        >>> assert result
        >>> str(result)
        'hello'
        >>> result = gpg.encrypt("hello again",print1)
        >>> message = str(result)
        >>> result = gpg.decrypt(message)
        >>> result.status
        'need passphrase'
        >>> result = gpg.decrypt(message,passphrase='bar')
        >>> result.status
        'bad passphrase'
        >>> assert not result
        >>> result = gpg.decrypt(message,passphrase='foo')
        >>> result.status
        'decryption ok'
        >>> str(result)
        'hello again'
        >>> result = gpg.encrypt("signed hello",print2,sign=print1)
        >>> result.status
        'need passphrase'
        >>> result = gpg.encrypt("signed hello",print2,sign=print1,passphrase='foo')
        >>> result.status
        'encryption ok'
        >>> message = str(result)
        >>> result = gpg.decrypt(message)
        >>> result.status
        'decryption ok'
        >>> assert result.fingerprint == print1

        """
        file = StringIO.StringIO(data)
        return self.encrypt_file(file, recipients, **kwargs)

    def decrypt(self,message,always_trust=False,passphrase=None):
        args = ["--decrypt"]
        if always_trust:
            args.append("--always-trust")
        result = Crypt()
        file = StringIO.StringIO(message)
        self._handle_gigo(args, file, result, passphrase)
        return result

class Verify:
    "Used to hold output of --verify"

    def __init__(self):
        self.valid = 0
        self.fingerprint = self.creation_date = self.timestamp = None
        self.signature_id = self.key_id = None
        self.username = None

    def __nonzero__(self):
        if self.is_valid(): return 1
        return 0

    def BADSIG(self, value):
        self.valid = 0
        self.key_id, self.username = value.split(None, 1)
    def GOODSIG(self, value):
        self.valid = 1
        self.key_id, self.username = value.split(None, 1)
    def VALIDSIG(self, value):
        #         C54065C14467F344A9585C1B96D482BAE5F1EA31 2005-08-10
        #         1123652038 0 3 0 1 2 01
        #         C54065C14467F344A9585C1B96D482BAE5F1EA31
        self.fingerprint, self.creation_date, self.sig_timestamp, \
                self.expire_timestamp = value.split()[:4]
    def SIG_ID(self, value):
        self.signature_id, self.creation_date, self.timestamp = value.split()

    # XXX do something with these; start using trust db
    def TRUST_UNDEFINED(self,value): pass
    def TRUST_NEVER(self,value): pass
    def TRUST_MARGINAL(self,value): pass
    def TRUST_FULLY(self,value): pass
    def TRUST_ULTIMATE(self,value): pass

    # these showed up in gpg 1.4.1
    def PLAINTEXT(self,value): pass
    def PLAINTEXT_LENGTH(self,value): pass

    def is_valid(self):
        return self.valid
 
class ImportResult:
    "Used to hold information about a key import result"

    counts = '''count no_user_id imported imported_rsa unchanged
            n_uids n_subk n_sigs n_revoc sec_read sec_imported
            sec_dups not_imported'''.split()
    def __init__(self):
        self.imported = []
        self.results = []
        self.fingerprints = []
        for result in self.counts:
            setattr(self, result, None)
    
    def __nonzero__(self):
        if self.not_imported: return 0
        if not self.fingerprints: return 0
        return 1

    def NODATA(self, value):
        self.results.append({'fingerprint': None,
            'problem': '0', 'text': 'No valid data found'})
    def IMPORTED(self, value):
        # this duplicates info we already see in import_ok and import_problem
        pass

    ok_reason = {
        '0': 'Not actually changed',
        '1': 'Entirely new key',
        '2': 'New user IDs',
        '4': 'New signatures',
        '8': 'New subkeys',
        '16': 'Contains private key',
    }
    def IMPORT_OK(self, value):
        reason, fingerprint = value.split()
        reasons = []
        for (code,text) in self.ok_reason.items():
            if int(reason) | int(code) == int(reason):
                reasons.append(text)
        reasontext = '\n'.join(reasons) + "\n"
        self.results.append({'fingerprint': fingerprint,
            'ok': reason, 'text': reasontext})
        self.fingerprints.append(fingerprint)

    problem_reason = {
        '0': 'No specific reason given',
        '1': 'Invalid Certificate',
        '2': 'Issuer Certificate missing',
        '3': 'Certificate Chain too long',
        '4': 'Error storing certificate',
    }
    def IMPORT_PROBLEM(self, value):
        try:
            reason, fingerprint = value.split()
        except:
            reason = value
            fingerprint = '<unknown>'
        self.results.append({'fingerprint': fingerprint,
            'problem': reason, 'text': self.problem_reason[reason]})
    def IMPORT_RES(self, value):
        import_res = value.split()
        for i in range(len(self.counts)):
            setattr(self, self.counts[i], int(import_res[i]))

    def summary(self):
        l = []
        l.append('%d imported' % self.imported)
        if self.not_imported:
            l.append('%d not imported' % self.not_imported)
        return ', '.join(l)

class ListKeys(list):
    ''' Parse a --list-keys output

        Handle pub and uid (relating the latter to the former).

        Don't care about (info from src/DETAILS):

        crt = X.509 certificate
        crs = X.509 certificate and private key available
        sub = subkey (secondary key)
        ssb = secret subkey (secondary key)
        uat = user attribute (same as user id except for field 10).
        sig = signature
        rev = revocation signature
        pkd = public key data (special field format, see below)
        grp = reserved for gpgsm
        rvk = revocation key
    '''
    def __init__(self):
        self.curkey = None
        self.fingerprints = []

    def key(self, args):
        vars = ("""
            type trust length algo keyid date expires dummy ownertrust uid
        """).split()
        self.curkey = {}
        for i in range(len(vars)):
            self.curkey[vars[i]] = args[i]
        self.curkey['uids'] = [self.curkey['uid']]
        del self.curkey['uid']
        self.append(self.curkey)

    pub = sec = key

    def fpr(self, args):
        # fpr:::::::::3324C8D0D1196A6CB497ABD6D694CE9742ABDCE6:
        self.curkey['fingerprint'] = args[9]
        self.fingerprints.append(args[9])
        
    def uid(self, args):
        self.curkey['uids'].append(args[9])

class Crypt(Verify):
    """Handle --encrypt or --decrypt status """

    def __init__(self):
        Verify.__init__(self)
        self.data = ''
        self.ok = False
        self.status = ''
    def __nonzero__(self):
        if self.ok: return 1
        return 0
    def __str__(self):
        return self.data
    def ENC_TO(self, value): pass
    def USERID_HINT(self, value): pass
    def NEED_PASSPHRASE(self, value): 
        self.status = 'need passphrase'
    def BAD_PASSPHRASE(self, value): 
        self.status = 'bad passphrase'
    def GOOD_PASSPHRASE(self, value): 
        self.status = 'good passphrase'
    def BEGIN_DECRYPTION(self, value): 
        self.status = self.status or 'decryption incomplete'
    def DECRYPTION_FAILED(self, value): 
        self.status = self.status or 'decryption failed'
    def DECRYPTION_OKAY(self, value): 
        self.status = 'decryption ok'
        self.ok = True
    def GOODMDC(self, value): pass
    def END_DECRYPTION(self, value): pass

    def BEGIN_ENCRYPTION(self, value): 
        self.status = self.status or 'encryption incomplete'
    def END_ENCRYPTION(self, value): 
        self.status = 'encryption ok'
        self.ok = True
    def INV_RECP(self, value): 
        self.status = 'invalid recipient'
    def KEYEXPIRED(self, value): 
        self.status = 'key expired'
    def SIG_CREATED(self, value): 
        self.status = 'sig expired'
    def SIGEXPIRED(self, value): 
        self.status = 'sig expired'


class GenKey:
    """Handle --gen-key status """
    def __init__(self):
        self.type = None
        self.fingerprint = None
    def __nonzero__(self):
        if self.fingerprint: return 1
        return 0
    def __str__(self):
        return self.fingerprint or ''
    def PROGRESS(self, value): pass
    def GOOD_PASSPHRASE(self, value): pass
    def NODATA(self, value): pass
    def KEY_CREATED(self, value):
        # P 95C91606D36AB8CACEB762DCD8DA31F0EE77B3A6
        (self.type,self.fingerprint) = value.split()

class Sign:
    """Handle --sign status """

    def __init__(self):
        self.type = None
        self.fingerprint = None
    def __nonzero__(self):
        if self.fingerprint: return 1
        return 0
    def __str__(self):
        return self.data or ''
    def USERID_HINT(self, value): pass
    def NEED_PASSPHRASE(self, value): pass
    def BAD_PASSPHRASE(self, value): pass
    def GOOD_PASSPHRASE(self, value): pass

    # SIG_CREATED <type> <pubkey algo> <hash algo> <class> <timestamp> <key fpr>
    def SIG_CREATED(self, value):
        # P 95C91606D36AB8CACEB762DCD8DA31F0EE77B3A6
        (self.type,algo,hashalgo,cls,self.timestamp,self.fingerprint
            ) = value.split()

import types
class PopenHi:
    """derived from open2.Popen3, but opens a fourth, high-numbered
    fd for input to the child
    
    """

    try:
        MAXFD = os.sysconf('SC_OPEN_MAX')
    except (AttributeError, ValueError):
        MAXFD = 256

    _active = []

    def _cleanup(cls):
        for obj in cls._active[:]:
            obj.poll()
    _cleanup = classmethod(_cleanup)

    def __init__(self, cmd, fd, bufsize = -1):
        PopenHi._cleanup()
        self.sts = -1
        p2cread, p2cwrite = os.pipe()
        c2pread, c2pwrite = os.pipe()
        hiread, hiwrite = os.pipe()
        errout, errin = os.pipe()
        self.pid = os.fork()
        if self.pid == 0:
            # Child
            # os.setsid() # disconnect from tty
            os.dup2(p2cread, 0)
            os.dup2(c2pwrite, 1)
            os.dup2(errin, 2)
            os.dup2(hiread, fd)
            if isinstance(cmd, types.StringTypes):
                cmd = ['/bin/sh', '-c', cmd]
            for i in range(3, PopenHi.MAXFD):
                if i == fd:
                    continue
                try:
                    os.close(i)
                except OSError:
                    pass
            # debug = "%d child running %s\n" % (os.getpid(), cmd)
            # open("/tmp/debug", 'w').write(debug)
            try:
                os.execvp(cmd[0], cmd)
            finally:
                os._exit(1)
        os.close(p2cread)
        self.tochild = os.fdopen(p2cwrite, 'w', bufsize)
        os.close(c2pwrite)
        self.fromchild = os.fdopen(c2pread, 'r', bufsize)
        os.close(errin)
        self.childerr = os.fdopen(errout, 'r', bufsize)
        os.close(hiread)
        self.childhi = os.fdopen(hiwrite, 'w', bufsize)
        PopenHi._active.append(self)

    def poll(self):
        """Return the exit status of the child process if it has finished,
        or -1 if it hasn't finished yet."""
        if self.sts < 0:
            try:
                pid, sts = os.waitpid(self.pid, os.WNOHANG)
                if pid == self.pid:
                    self.sts = sts
                    PopenHi._active.remove(self)
            except os.error:
                pass
        return self.sts

    def open(cls, cmd, fd, bufsize = -1):
        obj = PopenHi(cmd, fd, bufsize = -1)
        return obj.fromchild, obj.tochild, obj.childerr, obj.childhi
    open = classmethod(open)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        print 'Usage: GPG.py <signed file>'
        sys.exit()

    obj = GPGSubprocess()
    file = open(sys.argv[1], 'rb')
    sig = obj.verify_file(file)
    print sig.__dict__
