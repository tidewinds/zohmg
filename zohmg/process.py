from zohmg.config import Config, Environ
from zohmg.utils import fail
import os, re, sys

class Process(object):
    def go(self, mapper, input, for_dumbo):

        table = Config().dataset()
        resolver = 'fm.last.darling.HBaseIdentifierResolver'
        outputformat = 'org.apache.hadoop.hbase.mapred.TableOutputFormat'

        opts = [('jobconf',"hbase.mapred.outputtable=" + table),
                ('jobconf','stream.io.identifier.resolver.class=' + resolver),
                ('streamoutput','hbase'), # resolved by identifier.resolver
                ('outputformat', outputformat),
                ('input', input),
                ('output','/tmp/does-not-matter'),
                # Push zohmg egg and darling jar.
                ('libegg',[z for z in sys.path if "zohmg" in z][0]),
                ('libjar','/usr/local/lib/zohmg/darling-0.0.3.jar'),
                ('file','lib/usermapper.py') # TODO: handle this more betterer.
               ]

        # check for '--lzo' as first extra argument.
        if len(for_dumbo) > 0 and for_dumbo[0] == '--lzo':
            opts.append(('inputformat', 'org.apache.hadoop.mapred.LzoTextInputFormat'))
            for_dumbo.pop(0) # remove '--lzo'.

        # read environment and attach.
        env = Environ()
        hadoop_home = env.get("HADOOP_HOME")
        if not os.path.isdir(hadoop_home):
            msg = "Error: HADOOP_HOME not set in config/environment.py."
            fail(msg)
        else:
            opts.append(('hadoop',env.get("HADOOP_HOME")))

        classpath = env.get("CLASSPATH")
        if classpath is not None:
            for jar in classpath:
                if not os.path.isfile(jar):
                    msg = "Error: File not found, %s." % jar
                    fail(msg)
                else:
                    opts.append(('libjar', jar))
        else:
            msg = "Error: CLASSPATH in config/environment is empty."
            fail(msg)

        # pull everything in config and lib.
        file_opts = self.__add_files(["config","lib"])
        opts.extend(file_opts)

        # stringify arguments.
        opts_args = ' '.join("-%s '%s'" % (k, v) for (k, v) in opts)
        more_args = ' '.join(for_dumbo) # TODO: is this necessary?
        dumboargs = "%s %s" % (opts_args, more_args)
        print "giving dumbo these args: " + dumboargs

        # link-magic for usermapper.
        usermapper = os.path.abspath(".")+"/lib/usermapper.py"
        if os.path.isfile(usermapper):
            # TODO: need to be *very* certain we're not unlinking the wrong file.
            os.unlink(usermapper)
        # TODO: SECURITY, need to be certain that we symlink correct file.
        os.symlink(mapper,usermapper)

        # dispatch.
        # PYTHONPATH is added because dumbo makes a local run before
        # engaging with hadoop.
        os.system("PYTHONPATH=lib dumbo start /usr/local/lib/zohmg/import.py " + dumboargs)


    # reads directories and returns list of tuples of
    # file/libegg/libjar options for dumbo.
    def __add_files(self,dirs):
        opts = []
        # TODO: optimize? this is now O(dirs*entries*files).
        for dir in dirs:
            for entry in os.walk(dir):
                dir,dirnames,files = entry
                # for each file add it with correct option.
                for file in files:
                    if not os.path.isfile(dir+"/"+file):
                        msg = "Error: File not found, %s." % file
                        fail(msg)

                    option = None
                    suffix = file.split(".")[-1] # infer file suffix.

                    # ignore all other files but egg/jar/yaml.
                    if   suffix == "egg":  option = "libegg"
                    elif suffix == "jar":  option = "libjar"
                    elif suffix == "py":   option = "file"
                    #elif suffix == "py":   option = "pyfile" # TODO: implement this in dumbo maybe?
                    elif suffix == "yaml": option = "file"
                    # TODO: what about text files or other files the user wants?
                    #       we still want to ignore certain files (e.g. .pyc).

                    if option:
                        opts.append((option,dir+"/"+file))

        return opts
