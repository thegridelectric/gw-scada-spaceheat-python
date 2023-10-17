# -*- coding: utf-8 -*
'''!
  @file  DFRobot_GP8403.py
  @brief This is a function library of the DAC module.
  @copyright  Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license  The MIT License (MIT)
  @author  [tangjie](jie.tang@dfrobot.com)
  @version  V1.0
  @date  2022-03-03
  @url  https://github.com/DFRobot/DFRobot_GP8403
'''

import smbus2 as smbus

addr = 0x5f
  
##Select DAC output voltage of 0-5V
OUTPUT_RANGE_5V             =    0
##Select DAC output voltage of 0-10V
OUTPUT_RANGE_10V            =     17
##Select to output from channel 0
CHANNEL0                    =     1
##Select to output from channel 1
CHANNEL1                    =     2
##Select to output from all the channels
CHANNELALL                  =     3
  
class gp8403():
	## Configure current sensor register   
    GP8403_CONFIG_CURRENT_REG   =    0x02
  
    
    def __init__(self,addr):
        self._addr = addr
        self.outPutSetRange = 0x01
        self.voltage = 5000
        self._scl     = 3
        self._sda     = 2
        self.data_transmission = 0
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setwarnings(False)
        self.smbus = smbus.SMBus(1)


    def begin(self):
        '''!
        @param Initialize the sensor
        '''
        if(self.smbus.read_byte(self._addr) != 0):
            return 0
        return 1

    def set_DAC_outrange(self,mode):
        '''!
        @brief Set DAC output range
        @param mode Select DAC output range
        '''
        if mode == OUTPUT_RANGE_5V:
            self.voltage = 5000
        elif mode == OUTPUT_RANGE_10V :
            self.voltage = 10000
        self.smbus.write_word_data(self._addr, self.outPutSetRange, mode)

    def set_DAC_out_voltage(self, data, channel):
        '''!
        @brief Select DAC output channel & range
        @param data Set output data
        @param channel Set output channel
        '''
        self.data_transmission = ((float(data) / self.voltage) * 4095)
        self.data_transmission = int(self.data_transmission) << 4
        self._send_data(self.data_transmission, channel)


    def _send_data(self ,data, channel):
        if channel == 0:
            self.smbus.write_word_data(self._addr,self.GP8403_CONFIG_CURRENT_REG,data)
        
        elif channel == 1:
            self.smbus.write_word_data(self._addr,self.GP8403_CONFIG_CURRENT_REG<<1,data)
        else:
            self.smbus.write_word_data(self._addr,self.GP8403_CONFIG_CURRENT_REG,data)
            self.smbus.write_word_data(self._addr,self.GP8403_CONFIG_CURRENT_REG<<1,data)



