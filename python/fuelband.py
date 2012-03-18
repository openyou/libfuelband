import sys, os
import fcntl
import array
import logging

# when in doubt and/or lazy, use someone else's ioctl code for feature reports
# Gotten from http://www.lowlevel.cz/log/cats/english/Toradex%20Embedded%20Controller%20with%20Python%20in%20Linux.html

"""
Kernel definitions for ioctl commands come from the ioctl.h of Linux kernel
"""
_IOC_NRBITS   = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS  = 2

_IOC_NRSHIFT   = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT  = _IOC_SIZESHIFT + _IOC_SIZEBITS

_IOC_WRITE = 1
_IOC_READ  = 2

_IOC = lambda d,t,nr,size: (d << _IOC_DIRSHIFT) | (ord(t) << _IOC_TYPESHIFT) | \
     (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)
_IOW  = lambda t,nr,size: _IOC(_IOC_WRITE, t, nr, size)
_IOR  = lambda t,nr,size: _IOC(_IOC_READ, t, nr, size)
_IOWR = lambda t,nr,size: _IOC(_IOC_READ | _IOC_WRITE, t, nr, size)

# HIDIOCGRDESCSIZE                =_IOR('H', 0x01, struct.calcsize("I"))
# HIDIOCGRDESC                    =_IOR('H', 0x02, len(hidraw_report_descriptor()))
# HIDIOCGRAWINFO                  =_IOR('H', 0x03, len(hidraw_devinfo()))
#HIDIOCGRAWINFO                 =_IOR('H', 0x03, struct.calcsize("Ihh"))
def HIDIOCGRAWNAME(buflen):     return _IOR('H', 0x04, buflen)
def HIDIOCGRAWPHYS(buflen):     return _IOR('H', 0x05, buflen)
def HIDIOCSFEATURE(buflen):     return _IOWR('H', 0x06, buflen)
def HIDIOCGFEATURE(buflen):     return _IOWR('H', 0x07, buflen)

class Fuelband(object):
  def __init__(self):
    pass

def read_feature_report(f, value):
  """
  Reading and writing of FEATURE reports is done directly by kernel ioctl
  """
  ret = array.array('B', [0x4]*len(value))
  result = fcntl.ioctl(f, HIDIOCGFEATURE(64), ret, True)
  retstring = ' '.join( ['0x%02x ' % b for b in ret] )
  logging.debug('READ returned  : %d, %s' % (result, retstring))
  return ret

def write_feature_report(f, value):
  result = fcntl.ioctl(f, HIDIOCSFEATURE(len(value)), value, True)
  valstring = ' '.join( ['0x%02x '%b for b in value] )
  logging.debug('WRITE          : %d, %s' % (result, valstring))
  return result

def main():
  # get_account_info = [0x0a, 0x07, 0xbb, 0x50, 0x37, 0x36, 0x00, 0x00, 0x00]
  f = open("/dev/hidraw0", "w+b")
  if f == None:
    print("Cannot open device!")
    return 1
  g = array.array('B', [0 for i in range(63)])
  # #get_account_info = [0x09, 0x02, 0x29, 0x08, 0x00, 0x00, 0x00, 0x00]
  # Get info from band, offset 0
  offset = 0
  final_output = []
  while True:
    get_account_info = array.array('B', [0x09, 0x05, 0x43, 0x19, 0x00, (offset & 0xff00) >> 8, offset & 0xff, 0x00])
    write_feature_report(f, get_account_info)
    r = read_feature_report(f, g)
    final_output += r[6:]
    for c in r:
      sys.stdout.write("0x%.02x " % c)
    print ""
    offset += 0x37
    if r[1] != 0x3d:
      break
  f.close()
  i = 12
  offset = 0
  packet_index = 1
  # Stupid packet parsing
  while i < len(final_output):
    offset = 0
    while (final_output[i+offset]) != packet_index:
      offset += 1
    offset += 1
    print ["0x%.02x" % x for x in final_output[i:i+offset]]
    i += offset
    packet_index += 1
    if(packet_index == 255): packet_index = 1
    print "%d %d" % (i, len(final_output))
  return 0

if __name__ == "__main__":
  sys.exit(main())