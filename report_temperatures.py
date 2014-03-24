import os
import sys
import time
import logging
import yaml
import graphiteudp
import time 

# Read configuration file
cfg = yaml.load(file(os.path.dirname(os.path.realpath(__file__)) + '/local_settings.yml'))

# Setup logging module
numeric_level = getattr(logging, cfg['log']['level'].upper(), None)
if not isinstance(numeric_level, int):
  raise ValueError('Invalid log level: %s' % loglevel)
logging.basicConfig(level=numeric_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logging.debug("Config Options: %s" % cfg)

graphite = graphiteudp.GraphiteUDPClient(cfg['graphite']['host'], prefix = cfg['graphite']['device_location'].replace(" ","_"))

while True:
  for serial, name in cfg['sensor_mappings'].iteritems():
    try:
      f = open("/sys/bus/w1/devices/%s/w1_slave" % serial)
    except:
      logging.error("Error opening file for %s" % serial)
      next
  
    first_line = f.readline().strip().split(" ")
  
    #Testing to see if element 11 is there
    if len(first_line) != 12:
      logging.error("File /sys/bus/w1/devices/%s/w1_slave is malformed" % serial )
      f.close()
      next
  
    if first_line[11] == "YES":
      logging.debug("Sensor %s is YES. Using reading." % serial)
      second_line = f.readline().strip().split(" ")
  
      if len(second_line) != 10:
        logging.error("File /sys/bus/w1/devices/%s/w1_slave is malformed" % serial )
        f.close()
        next
        
      temp_c = int(second_line[9].replace("t=", "")) / 1000.0
      temp_f = temp_c * 1.8 + 32
      logging.info("Sensor %s(%s) reporting %f C" % (serial, name, temp_c))
  
      # report to graphite
      graphite.send("%s.temperature.f" % name.replace(" ","_") , temp_f)
      graphite.send("%s.temperature.c" % name.replace(" ","_") , temp_c)
    else:
      logging.debug("Sensor %s is not YES" % serial)
    f.close()
  time.sleep(cfg['sleep_time'])
