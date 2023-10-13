# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# This code is designed to work with any MCP23017 Board available from ncd.io.
# Source: https://github.com/ncd-io/MCP23017/blob/master/Python/mcp23017.py

# I2C address of the device
MCP23017_DEFAULT_ADDRESS                = 0x20 

# MCP23017 Register Map
MCP23017_REG_IODIRA                        = 0x00 # I/O DIRECTION-A Register
MCP23017_REG_IPOLA                        = 0x02 # INPUT POLARITY PORT-A Register
MCP23017_REG_GPINTENA                    = 0x04 # INTERRUPT-ON-CHANGE-A PINS
MCP23017_REG_DEFVALA                    = 0x06 # DEFAULT VALUE-A Register
MCP23017_REG_INTCONA                    = 0x08 # INTERRUPT-ON-CHANGE CONTROL-A Register
MCP23017_REG_IOCONA                        = 0x0A # I/O EXPANDER CONFIGURATION-A Register
MCP23017_REG_GPPUA                        = 0x0C # GPIO PULL-UP RESISTOR-A Register
MCP23017_REG_INTFA                        = 0x0E # INTERRUPT FLAG-A Register
MCP23017_REG_INTCAPA                    = 0x10 # INTERRUPT CAPTURED VALUE FOR PORT-A Register
MCP23017_REG_GPIOA                        = 0x12 # GENERAL PURPOSE I/O PORT-A Register
MCP23017_REG_OLATA                        = 0x14 # OUTPUT LATCH-A Register 0

MCP23017_REG_IODIRB                        = 0x01 # I/O DIRECTION-B Register
MCP23017_REG_IPOLB                        = 0x03 # INPUT POLARITY PORT-B Register
MCP23017_REG_GPINTENB                    = 0x05 # INTERRUPT-ON-CHANGE-B PINS
MCP23017_REG_DEFVALB                    = 0x07 # DEFAULT VALUE-B Register
MCP23017_REG_INTCONB                    = 0x09 # INTERRUPT-ON-CHANGE CONTROL-B Register
MCP23017_REG_IOCONB                        = 0x0B # I/O EXPANDER CONFIGURATION-B Register
MCP23017_REG_GPPUB                        = 0x0D # GPIO PULL-UP RESISTOR-B Register
MCP23017_REG_INTFB                        = 0x0F # INTERRUPT FLAG-B Register
MCP23017_REG_INTCAPB                    = 0x11 # INTERRUPT CAPTURED VALUE FOR PORT-B Register
MCP23017_REG_GPIOB                        = 0x13 # GENERAL PURPOSE I/O PORT-B Register
MCP23017_REG_OLATB                        = 0x15 # OUTPUT LATCH-B Register 0

# MCP23017 I/O Direction Register Configuration
MCP23017_IODIR_PIN_7_INPUT                = 0x80 # Pin-7 is configured as an input
MCP23017_IODIR_PIN_6_INPUT                = 0x40 # Pin-6 is configured as an input
MCP23017_IODIR_PIN_5_INPUT                = 0x20 # Pin-5 is configured as an input
MCP23017_IODIR_PIN_4_INPUT                = 0x10 # Pin-4 is configured as an input
MCP23017_IODIR_PIN_3_INPUT                = 0x08 # Pin-3 is configured as an input
MCP23017_IODIR_PIN_2_INPUT                = 0x04 # Pin-2 is configured as an input
MCP23017_IODIR_PIN_1_INPUT                = 0x02 # Pin-1 is configured as an input
MCP23017_IODIR_PIN_0_INPUT                = 0x01 # Pin-0 is configured as an input
MCP23017_IODIR_PIN_INPUT                = 0xFF # All Pins are configured as an input
MCP23017_IODIR_PIN_OUTPUT                = 0x00 # All Pins are configured as an output

# MCP23017 Pull-Up Resistor Register Configuration
MCP23017_GPPU_PIN_7_EN                    = 0x80 # Pull-up enabled on Pin-7
MCP23017_GPPU_PIN_6_EN                    = 0x40 # Pull-up enabled on Pin-6
MCP23017_GPPU_PIN_5_EN                    = 0x20 # Pull-up enabled on Pin-5
MCP23017_GPPU_PIN_4_EN                    = 0x10 # Pull-up enabled on Pin-4
MCP23017_GPPU_PIN_3_EN                    = 0x08 # Pull-up enabled on Pin-3
MCP23017_GPPU_PIN_2_EN                    = 0x04 # Pull-up enabled on Pin-2
MCP23017_GPPU_PIN_1_EN                    = 0x02 # Pull-up enabled on Pin-1
MCP23017_GPPU_PIN_0_EN                    = 0x01 # Pull-up enabled on Pin-0
MCP23017_GPPU_PIN_EN                    = 0xFF # Pull-up enabled on All Pins
MCP23017_GPPU_PIN_DS                    = 0x00 # Pull-up disabled on All Pins

# MCP23017 General Purpose I/O Port Register
MCP23017_GPIO_PIN_7_HIGH                = 0x80 # Logic-high on Pin-7
MCP23017_GPIO_PIN_6_HIGH                = 0x40 # Logic-high on Pin-6
MCP23017_GPIO_PIN_5_HIGH                = 0x20 # Logic-high on Pin-5
MCP23017_GPIO_PIN_4_HIGH                = 0x10 # Logic-high on Pin-4
MCP23017_GPIO_PIN_3_HIGH                = 0x08 # Logic-high on Pin-3
MCP23017_GPIO_PIN_2_HIGH                = 0x04 # Logic-high on Pin-2
MCP23017_GPIO_PIN_1_HIGH                = 0x02 # Logic-high on Pin-1
MCP23017_GPIO_PIN_0_HIGH                = 0x01 # Logic-high on Pin-0
MCP23017_GPIO_PIN_HIGH                    = 0xFF # Logic-high on All Pins
MCP23017_GPIO_PIN_LOW                    = 0x00 # Logic-low on All Pins

class mcp23017():
    def __init__(self, smbus, kwargs = {}):
        self.__dict__.update(kwargs)
        #set address to default if not passed
        if not hasattr(self, 'address'):
            self.address = MCP23017_DEFAULT_ADDRESS

        self.smbus = smbus

        #we only need to know which are outputs as the chip sets all GPIOs as inputs by default for safety reasons.
        if hasattr(self, 'gpio_output_map'):
            bank = 0
            for bank_map in self.gpio_output_map:
                register_byte = 255
                for channel in bank_map:
                    register_byte = register_byte ^ 1 << channel

                if(register_byte != 255):
                    self.set_output_register(bank, register_byte)
                bank = bank+1

    def set_output_register(self, bank, register_value):
        self.smbus.write_byte_data(self.address, bank, register_value)

    def set_bank_status(self, bank, status_value):
        self.smbus.write_byte_data(self.address, MCP23017_REG_GPIOA+bank-1, status_value)

    def set_gpio_high(self, bank, target_gpio, status = None):
        if(status == None):
            status = self.get_gpio_bank_status(bank)

        target_byte_value = 1 << target_gpio
        new_status_byte = status | target_byte_value
        self.smbus.write_byte_data(self.address, MCP23017_REG_GPIOA+bank-1, new_status_byte)

#pseudo method
    def turn_on_relay(self, bank, target_relay, status = None):
        self.set_gpio_high(bank, target_relay, status)

    def set_gpio_high_by_index(self, target_gpio):
        bank = 1
        while target_gpio > 7:
            target_gpio = target_gpio - 8
            ++bank
        self.set_gpio_high(bank, target_gpio)

    def set_gpio_low(self, bank, target_gpio, status = None):
        if(status == None):
            status = self.get_gpio_bank_status(bank)
        target_byte_value = 1 << target_gpio
        new_status_byte = status ^ target_byte_value
        self.smbus.write_byte_data(self.address, MCP23017_REG_GPIOA+bank-1, new_status_byte)

#pseudo method
    def turn_off_relay(self, bank, target_relay, status = None):
        self.set_gpio_low(bank, target_relay, status)

    def set_gpio_low_by_index(self, target_gpio):
        bank = 1
        while target_gpio > 7:
            target_gpio = target_gpio - 8
            bank = bank + 1
        self.toggle_gpio(bank, target_gpio)

    def toggle_gpio(self, bank, target_gpio):
        target_byte_value = 1 << target_gpio
        status = self.get_gpio_bank_status(bank)
        #check if the gpio is set high
        if(status & target_byte_value != 0):
            self.set_gpio_low(bank, target_gpio, status)
        else:
            self.set_gpio_high(bank, target_gpio, status)

#pseudo method
    def toggle_relay(self, bank, target_relay):
        self.toggle_gpio(bank, target_relay)

    def toggle_gpio_by_index(self, target_gpio):
        bank = 1
        while target_gpio > 7:
            target_gpio = target_gpio - 8
            ++bank
        self.toggle_gpio(bank, target_gpio)

    def get_single_gpio_status(self, bank, target_gpio):
        status = self.get_gpio_bank_status(bank)
        target_byte_value = 1 << target_gpio
        return (status & target_byte_value) != 0

    def get_single_gpio_status_by_index(self, target_gpio):
        bank = 1
        while target_gpio > 7:
            target_gpio = target_gpio - 8
            ++bank
        self.get_single_gpio_status(bank, target_gpio)

    def get_gpio_bank_status(self, bank):
        return self.smbus.read_byte_data(self.address, MCP23017_REG_GPIOA+bank-1)

    def get_gpio_bank_resistor_settings(self, bank):
        return self.smbus.read_byte_data(self.address, MCP23017_REG_GPPUA+bank-1)

    def pull_up_gpio(self, bank, target_gpio):
        target_byte_value = 1 << target_gpio
        status = self.get_gpio_bank_resistor_settings(bank-1)
        new_status_byte = status | target_byte_value
        self.smbus.write_byte_data(self.address, MCP23017_REG_GPPUA+bank-1, new_status_byte)