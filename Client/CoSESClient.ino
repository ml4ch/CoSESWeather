/*  CoSESClient 2019 CONTROLLINO MAXI (ATmega 2560)
 *
 *  This software is part of the CoSESWeather project.
 *  This software interfaces sensors, which by the date written contains:
 *  
 *  1 x PT100 Temperature Sensor
 *  1 x Anemometer
 *  1 x SPN1 Pyranometer
 *  3 x CMP3 Pyranometer
 *  
 *  This software forwards the acquired sensor measurements to a RevolutionPi
 *  that together with the CONTROLLINO forms the core of the CoSES Weather Station.
 *
 *  @Author:      Miroslav Lach (MSE, Technical University Munich)
 *  @Version:     1.0
 *  @Date:        13.01.2019
 *  @Status:      Released, no known bugs
 *  @Link:        https://github.com/ml4ch/CoSESWeather
 */

// ----------------------------------------------------------------------------
// --------- Required libraries -----------------------------------------------
#include <avr/wdt.h> // required for watchdog
#include <Wire.h> // required for I2C communication
#include <math.h> // math library includes pow() function
#include <SPI.h> // required for SPI communication
#include <Ethernet.h> // required for Etehrnet communication
#include <Controllino.h> // Implement CONTROLLINO library
#include <Adafruit_MAX31865.h> // required for RTD PT100 sensor amplifier board
/*************************************************** 
  This is a library for the Adafruit PT100/P1000 RTD Sensor w/MAX31865

  Designed specifically to work with the Adafruit RTD Sensor
  ----> https://www.adafruit.com/products/3328

  This sensor uses SPI to communicate, 4 pins are required to  
  interface
  Adafruit invests time and resources providing this open source code, 
  please support Adafruit and open-source hardware by purchasing 
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.  
  BSD license, all text above must be included in any redistribution
 ****************************************************/
#include <pt100rtd.h> // PT100 lookup-table (for more accuracy)
/*BSD 2-Clause License

Copyright (c) 2017, drhaney
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.*/

// ----------------------------------------------------------------------------
// --------- DEBUG Mode (active / inactive) -----------------------------------
// Comment this #define out when not debugging!
#define DEBUG

// Define Macros for more efficient and convenient Debugging
#ifdef DEBUG
  #define DEBUG_PRINT(x)       Serial.print(x)
  #define DEBUG_PRINT_LN(x)    Serial.println(x)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINT_LN(x) 
#endif

// ----------------------------------------------------------------------------
// --------- General Definitions ----------------------------------------------
// Define the sample interval of the system (e.g. 5000 ms will make the Controllino output data from all sensors once every 5 senconds)
#define SENSOR_SAMPLE_RATE_MSEC   5000
String SensorDataPackage;
byte sampling_rounds = 0;
unsigned long timestamp_last_sampling;
bool isCommand_processing_ongoing = false;
bool isConnectionError = false;
bool isRestarting = false;

// ----------------------------------------------------------------------------
// --------- EthernetShield ---------------------------------------------------
// Define the IP address and Port of the RevPi (eth0)
IPAddress RevPi_IP(192, 168, 21, 100);
#define REVPI_PORT_SOCKET   7785

// Assign MAC and IP address to the Controllino
byte Controllino_MAC[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};
IPAddress Controllino_IP(192, 168, 21, 101);

EthernetClient client_eth;
bool isConnected = false;

// ----------------------------------------------------------------------------
// --------- Anemometer -------------------------------------------------------
#define ANEMOMETER_SIGNAL_INPUT_PIN   2
volatile int anemometer_pulses = 0; // declare as volatile to load variable from RAM (and not register) because used in ISR
float windspeed = 0.0;
unsigned long timestamp_duration;

// ----------------------------------------------------------------------------
// --------- RTD PT100 Sensor Amplifier Board --------------------------------- 
float PT100_temp;
#define RTD_PT100_BOARD_CHIP_SELECT_PIN   53
Adafruit_MAX31865 max = Adafruit_MAX31865(RTD_PT100_BOARD_CHIP_SELECT_PIN); // SPI, declaring the CS pin
// The value of the Rref resistor. Use 430.0 for PT100 and 4300.0 for PT1000
#define RREF    430.0
// The 'nominal' 0-degrees-C resistance of the sensor: 100.0 for PT100, 1000.0 for PT1000
#define RNOMINAL    100.0
// initialize the Pt100 table lookup module
pt100rtd PT100 = pt100rtd() ;

// ----------------------------------------------------------------------------
// --------- SPN1 Pyranometer -------------------------------------------------
String SPN1_COMMAND = "RS"; // Command that wakes up the SPN1 ('R') and requests measurements ('S')
String SPN1data;
#define SPN1_SERIAL   Serial2

// ----------------------------------------------------------------------------
// --------- CMP3 Pyranometers ------------------------------------------------ 
#define CMP3PyranometersInUse    3
double CMP3_DataArray[CMP3PyranometersInUse];
#define rSAMPLES_TO_TAKE   4
int32_t outputCode, *p_outputCode;
float LSB_size = 15.625; // ADC 18Bit LSB size with V_ref = 2.048V is 15.625uV
byte INA_GAIN = 69; // amplification factor of INA set by gain resistors
bool ADCfail = false;

// --------- ADC register addresses ------------------------------------------- 
//I2C address of ADC (MCP3424)
#define ADC_ADDRESS               0X6E // ADDR pins HIGH/HIGH yields 01101110 or 0x6E
//ADC sampling mode
#define ADC_SAMPLING              0X10 //continuous sampling = 1 | one-shot sampling = 0
//ADC sample rate and resolution
#define ADC_18BIT                 0X0C //18-bit yields 3.75 SPS
//ADC gain
#define ADC_GAIN                  0X00 //PGA unity gain
//ADC MUX channel selection
#define ADC_CHANNEL1              0X00 //ADC input channel 1 (channel 3 on amplification board)
#define ADC_CHANNEL2              0X20 //ADC input channel 2 (not used)
#define ADC_CHANNEL3              0X40 //ADC input channel 3 (channel 1 on amplification board)
#define ADC_CHANNEL4              0X60 //ADC input channel 4 (channel 2 on amplification board)
//Config
#define ADC_CONFIG                0X80 //In write-mode: start a new conversion (only in single shot conversion mode)

//Declare and initialize ADC config byte for config register (for used ADC channels, we use 3 CMP3 sensors)
uint8_t ADC_CONFIG_BYTE_CHANNEL[CMP3PyranometersInUse] = {
  ADC_CONFIG | ADC_CHANNEL1 | ADC_SAMPLING | ADC_18BIT | ADC_GAIN,
  ADC_CONFIG | ADC_CHANNEL3 | ADC_SAMPLING | ADC_18BIT | ADC_GAIN,
  ADC_CONFIG | ADC_CHANNEL4 | ADC_SAMPLING | ADC_18BIT | ADC_GAIN
};
//Declare individual sensitivity of CMP3 sensors [µV/W/m²]
float CMP3_sensitivity[CMP3PyranometersInUse] = {
  14.11,
  15.15,
  15.09
};  
//Declare individual channel offset for calibration
int offset_compensation[CMP3PyranometersInUse] = {
  20,
  84,
  30
};  
// ----------------------------------------------------------------------------

void setup() 
{
  // Initialize some VARs  
  wdt_enable(WDTO_8S); // enable watchdog (8 sec)
  isRestarting = false;
  isCommand_processing_ongoing = false;
  isConnectionError = false;
  sampling_rounds = 0;
  
  // ----------------------------------------------------------------------------
  // --------- EthernetShield ---------------------------------------------------  
  // Select EthernetShield as active slave (CS/SS Pin)
  pinMode(CONTROLLINO_ETHERNET_CHIP_SELECT, OUTPUT); // Define the CS Pin as output
  digitalWrite(CONTROLLINO_ETHERNET_CHIP_SELECT, LOW); // In SPI a LOW on CS Pin declares an active Slave
  isConnected = false;

  // ----------------------------------------------------------------------------
  // --------- Anemometer -------------------------------------------------------
  pinMode(ANEMOMETER_SIGNAL_INPUT_PIN, INPUT_PULLUP); // Use internal PULLUP resistors in INPUT so the pin is in a defined non-floating state
  attachInterrupt(digitalPinToInterrupt(ANEMOMETER_SIGNAL_INPUT_PIN), ISR_Anemometer, FALLING); // Attach Interrupt to input pin

  // ----------------------------------------------------------------------------
  // --------- RTD PT100 Sensor Amplifier Board---------------------------------- 
  max.begin(MAX31865_4WIRE);  // set to 4WIRE
  pinMode(RTD_PT100_BOARD_CHIP_SELECT_PIN, OUTPUT); // Define the CS Pin as output
  digitalWrite(RTD_PT100_BOARD_CHIP_SELECT_PIN, HIGH); // In SPI a LOW on CS Pin declares an active Slave

  // ----------------------------------------------------------------------------
  // --------- SPN1 Pyranometer -------------------------------------------------
  SPN1_SERIAL.begin(9600); // Initiate RS232 (Serial TX/RX) communication
  // ----------------------------------------------------------------------------

  // ----------------------------------------------------------------------------
  // --------- CMP3 Pyranometers -------------------------------------------------
  Wire.begin(); // Initiate I2C communication
  // ----------------------------------------------------------------------------

  // Compile only when in DEBUG mode
  #ifdef DEBUG
    // Initialize serial monitor
    Serial.begin(9600);
    while(!Serial) 
    {
      ; // wait for serial port to connect. Needed for native USB port only
    }
  #endif
  
  // Initialize ethernet connection
  Ethernet.begin(Controllino_MAC, Controllino_IP);

  if(Ethernet.hardwareStatus() == EthernetNoHardware) 
  {
    DEBUG_PRINT_LN("No Ethernet Shield found!");
    isConnectionError = true;
  }
  if(Ethernet.linkStatus() == LinkOFF) 
  {
    DEBUG_PRINT_LN("Ethernet cable not connected!");
    isConnectionError = true;
  }
  #ifdef DEBUG
    if(!isConnectionError)
    {
      DEBUG_PRINT("Connecting to RevPi at ");
      DEBUG_PRINT(RevPi_IP);
      DEBUG_PRINT(" on Port ");
      DEBUG_PRINT(REVPI_PORT_SOCKET);
      DEBUG_PRINT_LN(" ...");
    }
  #endif

  delay(6000); // Make sure the ethernet connection has been fully initialized
  wdt_reset(); // reset watchdog timer

  if(!isConnectionError) // If Hardware has been detected and initialized successfully
  {
    // Connect to RevPi
    if(client_eth.connect(RevPi_IP, REVPI_PORT_SOCKET)) 
    {
      DEBUG_PRINT("Established connection to RevPi at ");
      DEBUG_PRINT_LN(client_eth.remoteIP());
      isConnected = true;
      wdt_enable(WDTO_4S); // enable watchdog (reduce to 4 sec)
    } 
    else 
    {
      DEBUG_PRINT_LN("Could not connect to the RevPi! Retrying in 5 seconds ...");
      delay(5000);
      initiateRestart();
    }
  }
  else initiateRestart(); // In case of hardware errors: try to restart and re-initialize system
}

void loop() 
{ 
  if(isConnected) // if there is an active and valid connection
  {   
    // if the server has disconnected, stop the client:
    if(!client_eth.connected()) 
    {
      isConnected = false; 
      DEBUG_PRINT_LN("-------------- Lost connection to Server -----------------");
      initiateRestart();
    }
   
    // if connected, send data to RevPi
    if(client_eth.connected())
    { 
      // Check for incoming commands from RevPi
      CB_OnCommandReceived();

      // send sensor data according to defined sampling intervals
      if((millis()-timestamp_last_sampling) > SENSOR_SAMPLE_RATE_MSEC) 
      {
        sampling_rounds++;
        DEBUG_PRINT_LN("Current sampling time: " + String(millis() - timestamp_last_sampling) + " [ms]");
        DEBUG_PRINT_LN("------------ Sensor Data ------------");  
        timestamp_last_sampling = millis(); // update the timestamp
                
        // ----------------------------------------------------------------------------
        // --------- SPN1 Pyranometer (request data) ----------------------------------
        SPN1_SERIAL.print(SPN1_COMMAND); // Send command to SPN1 (request measurements)
        // Data sent back from the SPN1 will be read later so the device has enough time to reply
        
        // Manage SPI-Bus: Deactivate Ethernet-Board (ensure that only one SPI slave is activa at a time)
        digitalWrite(CONTROLLINO_ETHERNET_CHIP_SELECT, HIGH); // Deactivate SPI Slave (Ethernet)
        digitalWrite(RTD_PT100_BOARD_CHIP_SELECT_PIN, LOW); // Activate SPI Slave (RTD PT100 Amp-Board)

        // ----------------------------------------------------------------------------
        // --------- Anemometer -------------------------------------------------------
        noInterrupts(); // disable interrupts before reading volatile variables
        if(anemometer_pulses == 0 || timestamp_duration == 0)windspeed = 0.0;
        else windspeed = ((anemometer_pulses/((micros()-timestamp_duration)/1000000)) * 0.07881) + 0.32; // calculate windspeed according to formula given in datasheet
        anemometer_pulses = 0;  
        interrupts(); // re-enable interrupts after finished reading
        timestamp_duration = micros();      
        DEBUG_PRINT_LN("Anemometer: " + String(windspeed));
        
        // ----------------------------------------------------------------------------
        // --------- RTD PT100 Sensor Amplifier Board---------------------------------- 
        // This code is taken from the example code-files that show how temperature/resistance can be read out from the MAX31865:
        // Link to code sources: https://github.com/adafruit/Adafruit_MAX31865/blob/master/examples/max31865/max31865.ino (Adafruit Industries)
        //                       https://github.com/drhaney/pt100rtd/blob/master/examples/pt100_temperature/pt100_temperature.ino (drhaney)
        uint16_t rtd, ohmsx100;
        uint32_t rtd_dummy;        
        //PT100_temp = max.temperature(RNOMINAL, RREF); // read temperature without lookup-table
        rtd = max.readRTD(); // read resistance
        // Use uint16_t (ohms * 100) since it matches data type in lookup table.
        rtd_dummy = ((uint32_t)(rtd << 1)) * 100 * ((uint32_t) floor(RREF));
        rtd_dummy >>= 16;
        ohmsx100 = (uint16_t) (rtd_dummy & 0xFFFF);
        PT100_temp = PT100.celsius(ohmsx100); // lookup temperature for determined resistance in lookup-table (empirical data)
        uint8_t fault = max.readFault();
        
        #ifdef DEBUG   
          Serial.print("PT100: "); Serial.println(PT100_temp); 
          // Check and print any faults
          if (fault) 
          {
            Serial.print("Fault 0x"); Serial.println(fault, HEX);
            if (fault & MAX31865_FAULT_HIGHTHRESH) 
            {
              Serial.println("RTD High Threshold"); 
            }
            if (fault & MAX31865_FAULT_LOWTHRESH) 
            {
              Serial.println("RTD Low Threshold"); 
            }
            if (fault & MAX31865_FAULT_REFINLOW) 
            {
              Serial.println("REFIN- > 0.85 x Bias"); 
            }
            if (fault & MAX31865_FAULT_REFINHIGH) 
            {
              Serial.println("REFIN- < 0.85 x Bias - FORCE- open"); 
            }
            if (fault & MAX31865_FAULT_RTDINLOW) 
            {
              Serial.println("RTDIN- < 0.85 x Bias - FORCE- open"); 
            }
            if (fault & MAX31865_FAULT_OVUV) 
            {
              Serial.println("Under/Over voltage"); 
            }
            max.clearFault();
          }
        #endif  
        if(fault)PT100_temp = 9999.1; // if RTD-Amp-Board returned an invalid response

        // Manage SPI-Bus: Re-Activate Ethernet-Board 
        digitalWrite(CONTROLLINO_ETHERNET_CHIP_SELECT, LOW); // Activate SPI Slave (Ethernet)
        digitalWrite(RTD_PT100_BOARD_CHIP_SELECT_PIN, HIGH); // Deactivate SPI Slave (RTD PT100 Amp-Board)

        // ----------------------------------------------------------------------------
        // --------- CMP3 Pyranometer ADC --------------------------------------------- 
        double rSAMPLE_ARRAY_chan[rSAMPLES_TO_TAKE];
        //Get and calculate data for all CMP3 sensors respectively
        for(int i = 0; i<sizeof(ADC_CONFIG_BYTE_CHANNEL); i++)
        {
          // Write config byte to ADC config register (and change ADC MUX channels)
          Wire.beginTransmission(ADC_ADDRESS); // begin I2C communication (write operation)
          Wire.write(ADC_CONFIG_BYTE_CHANNEL[i]); // send data to ADC
          Wire.endTransmission(); // free I2C bus
      
          byte s_index = 0, is_zero = 0;
          while(s_index < rSAMPLES_TO_TAKE) // takes 4 samples per reading per channel
          {          
            // Read ADC digital data output and calculate physical units
            if(!readADC(i) && !ADCfail)continue; // new sample not ready yet - repeat
            else
            { 
              if(ADCfail)break; // ADC did not return any or faulty response
              else // new sample returned
              {
                double voltage_amp, voltage_adc, voltage_corrected, radiation;
                if(*p_outputCode != 0x00000000) // if output code not negative/zero
                {
                  // Calculate voltage from digital output code
                  voltage_adc = (double)*p_outputCode * (LSB_size*pow(10,-6));

                  // Compensate for voltage drop
                  voltage_corrected = voltage_adc*(1+((20*pow(10,3))*(((3.2*pow(10,-12)*262144)+(1/(21*pow(10,6)))))));
                
                  // Calculate radiation in W/m²
                  voltage_amp = voltage_corrected/INA_GAIN;
                  radiation = voltage_amp/(CMP3_sensitivity[i]*pow(10,-6));
                }
                else // output yields zero
                {
                  radiation = 0.0;
                  is_zero++;
                }
                rSAMPLE_ARRAY_chan[s_index] = radiation;
                s_index++;   
              }
            }
          }
          if(ADCfail) // ADC did not return any or faulty response
          {
            CMP3_DataArray[0] = 9999.21;
            CMP3_DataArray[1] = 9999.22;
            CMP3_DataArray[2] = 9999.23;
            break;
          }
          else // ADC returned valid response - calculate required values
          {
            //Calculcate average of 4 samples for current channel
            double radiation_tmp = 0.0, radiation_average;
            if(is_zero == rSAMPLES_TO_TAKE)radiation_average = 0.0; // prevent division by zero
            else
            {
              for(int ii = 0; ii<rSAMPLES_TO_TAKE; ii++)radiation_tmp = radiation_tmp + rSAMPLE_ARRAY_chan[ii]; // take sum
              radiation_average = radiation_tmp/rSAMPLES_TO_TAKE; // calculate average
            }
            CMP3_DataArray[i] = radiation_average;
          }
        }
        DEBUG_PRINT("CMP3_1: "), DEBUG_PRINT_LN(CMP3_DataArray[0]);  
        DEBUG_PRINT("CMP3_2: "), DEBUG_PRINT_LN(CMP3_DataArray[1]);  
        DEBUG_PRINT("CMP3_3: "), DEBUG_PRINT_LN(CMP3_DataArray[2]);  

        // ----------------------------------------------------------------------------
        // --------- SPN1 Pyranometer (receive requested data) ------------------------
        SPN1data = "_ERR_SPN1_";
        if (SPN1_SERIAL.available() > 0) // If received data from SPN1 (buffer not empty)
        {
          SPN1data = SPN1_SERIAL.readString(); // read SPN1 response for the command that has been sent earlier
          //extract needed data
          SPN1data.remove(0, 2);
          SPN1data.replace(" ", "");      
          SPN1data.replace("\r", "");                    
        }        
        DEBUG_PRINT("SPN1: ");          
        DEBUG_PRINT_LN(SPN1data);   
        
        // ----------------------------------------------------------------------------
        // --------- EthernetShield ---------------------------------------------------  
        // Transmit Data via Ethernet to RevPi
        if(sampling_rounds > 2) // Do not transmit the first few samples as they might not be accurate
        {
          // Create Sensor Data Package      
          SensorDataPackage = String(windspeed) + "|" + String(PT100_temp) + "|" + String(SPN1data) + "|" + String(CMP3_DataArray[0]) + "|" + String(CMP3_DataArray[1]) + "|" + String(CMP3_DataArray[2]);
          client_eth.println(SensorDataPackage + "\n"); // Send sensor data package to RevPi
        }
        // ----------------------------------------------------------------------------
        DEBUG_PRINT_LN("-------------------------------------");
        DEBUG_PRINT_LN("Execution time (data acquisition): " + String(millis() - timestamp_last_sampling) + " [ms]");
        DEBUG_PRINT_LN(); 
      }
    }    
  }
  wdt_reset(); // reset watchdog timer
}

// Function will trigger a Controllino board restart (Software Reset using the watchdog)
void initiateRestart() 
{
  if(!isRestarting) // if no restart has been triggered yet
  {
    isRestarting = true;
    DEBUG_PRINT_LN("Restarting ...");
    if(isConnected)client_eth.stop(); // close socket
    isConnected = false; 
    delay(1000);
    wdt_enable(WDTO_15MS); // activate watchdog
    while(1){} // let the watchdog timeout  
  }
}

// This Interrupt Service Routine counts the pulses of the Anemometer in the defined measurement/sample interval
void ISR_Anemometer() 
{
  anemometer_pulses++;
}

// This function reads the ADC on the amplification board for the 3 CMP3 pyranometers
bool readADC(int channel) // changed from int32_t to bool !! check if working properly!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
{    
  Wire.requestFrom(ADC_ADDRESS, 4); //request 4 bytes from ADC (containing conversion data)
  if(Wire.available() != 4) // ADC returned unexpected number of bytes
  {
    DEBUG_PRINT_LN("[ERROR]Error occured while reading ADC!");
    ADCfail = true;
    return false;
  }
  else
  {
    uint8_t ADCByte[4];
    int32_t sign_byte, first_byte, middle_byte, last_byte;
      
    ADCByte[0] = Wire.read(); //MSB-Byte (upper data byte)
    ADCByte[1] = Wire.read(); //Mid-Byte (middle data byte)
    ADCByte[2] = Wire.read(); //LSB-Byte (lower data byte)
    ADCByte[3] = Wire.read(); //config byte
    ADCfail = false;

    if(ADCByte[3] & 0x80){
      return false; //new sample not ready yet 
    }

    //sign extension (check if sign bit is set)
    if(ADCByte[0] & 0x80)sign_byte = (int32_t)0xFF << 24; //result is negative
    else sign_byte = 0x00000000; //result is positive

    //build 32 bit data
    first_byte = (int32_t)ADCByte[0] << 16;
    middle_byte = (int32_t)ADCByte[1] << 8;
    last_byte = (int32_t)ADCByte[2];

    //build 32bit data   
    outputCode = (sign_byte | first_byte | middle_byte | last_byte);

    //we do not want negative values - set to zero or compensate channel offset mathematically  
    if(outputCode & 0x80000000)outputCode = 0x00000000;
    else outputCode = outputCode + offset_compensation[channel];
    
    //update pointer address with new output code
    p_outputCode = &outputCode;

    //new sample ready
    return true;
  }
}

// Callback that parses and processes incoming commands sent by RevPi
void CB_OnCommandReceived() 
{
  // ---------- Check for received Commands ---------------------
  // 'a' = restart | 'b' = NOT USED | '#' = HEARTBEAT
  // ------------------------------------------------------------
  while(client_eth.available() > 0) // if buffer not empty, check for commands
  {
    char incomingChar = client_eth.read(); // read incoming byte of data
    DEBUG_PRINT("[DATA]Received from RevPi: "); 
    DEBUG_PRINT("Dezimal: " + String(incomingChar, DEC) + " | ");
    DEBUG_PRINT_LN("ASCII-Char: " + String(incomingChar));
    // Check for HeartBeat from RevPi
    if(incomingChar == '#')
    {
      DEBUG_PRINT_LN("HeartBeat detected."); 
      client_eth.println("*\n"); // Respond to HeartBeat signal 
    }       
    // Process commands
    if(!isCommand_processing_ongoing) // If no command is currently being processed (one command at a time)
    {  
      switch(incomingChar) // differentiate between existing commands
      {
        case 'a': // Reset CONTROLLINO
        {
          DEBUG_PRINT_LN("Executing command 1 (Reset).");  
          isCommand_processing_ongoing = true;
          initiateRestart();
          break;
        }
        case 'b': // CURRENTLY NOT USED
        {
          //DEBUG_PRINT_LN("Executing command 2 (--)."); 
          //isCommand_processing_ongoing = true;
          break;
        }      
      }
    }
  }
}
