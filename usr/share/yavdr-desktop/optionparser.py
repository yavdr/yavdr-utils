from optparse import OptionParser
import logging

class Options():
    def __init__(self):
        self.parser = OptionParser()
        self.parser.add_option("-c", "--hdf", dest="hdf_file",
            default='/etc/yavdr/test.hdf', help=u"clearsilver hdf file",
            metavar="HDF_FILE")
        self.parser.add_option("-l", "--log", dest="logfile",
            default='/tmp/yavdr-frontend.log', help=u"log file",
            metavar="LOGFILE")
        self.parser.add_option("-v", "--loglevel", dest="loglevel",
            default='DEBUG', help=u"--loglevel [DEBUG|INFO|WARNING|ERROR|CRITICAL]",
            metavar="LOG_LEVEL")
            
    def get_options(self):
        (options, args) = self.parser.parse_args()
        return options
            
if __name__ == '__main__':
    opt = Options()
    help(opt)
    opt.get_options()
