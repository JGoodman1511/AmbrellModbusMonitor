import minimalmodbus
import serial.tools.list_ports
import sys
import customtkinter
import datetime
import csv
import os
from PIL import ImageTk

customtkinter.set_appearance_mode("dark")

####################### FUNCTIONS ################################

#https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
#Using resource_path, add the file or folder to the dist folder after pyinstaller
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


####### COM FUNCTIONS #######

def findCOM():
	ports = serial.tools.list_ports.comports()
	coms=[]
	for port, desc, hwid in sorted(ports):
		coms.append(" {}: {}".format(port, desc))
	if len(coms) < 1:
		coms.append("No Devices Found")
	return coms

def listAddr():
	output = []
	for i in range(1, 33):
		output.append(str(i))
	return output

def setParity():
	if 'MODBUS-N' in modGet:
		mod = 'serial.PARITY_NONE'
	else:
		mod = 'serial.PARITY_EVEN'
	return mod

def setStopBits():
	if 'MODBUS-N' in modGet:
		sb = 2
	else:
		sb = 1
	return sb

def sendInstrumentData():
	app.com=app.toplevel_window.comGet[1:5]
	app.baud=app.toplevel_window.baudGet
	app.mod=app.toplevel_window.modGet
	app.addr=app.toplevel_window.addrGet
	return

####### DECODING FUNCTIONS #######

def decodeReg(regInt):
    hexValue = hex(regInt)
    firstByte = slice(2,4)
    secondByte = slice(4,6)
    byteSwap = hexValue[secondByte] + hexValue[firstByte]
    decodedInt = int(byteSwap,16)
    return decodedInt

def extendHex(inputInt):
    hexValue = hex(inputInt)
    zeroAdd = 6 - len(hexValue)
    zeroString = ""
    while zeroAdd > 0:
        zeroString += "0"
        zeroAdd -= 1
    return (zeroString + hexValue[2:])

def MSB(msbInt):
    msbHex = extendHex(msbInt)
    msbVal = msbHex[2:4]
    decodedmsb = int(msbVal,16)
    return decodedmsb

def LSB(lsbInt):
    lsbHex = extendHex(lsbInt)
    lsbVal = lsbHex[0:2]
    decodedlsb = int(lsbVal,16)
    return decodedlsb

def flagCheck(bit,inputReg):
    bitCheck = bin(inputReg)
    zeroAdd = 10 - len(bitCheck)
    zeroString = ""
    while zeroAdd > 0:
        zeroString += "0"
        zeroAdd -= 1
    flagRegs = zeroString + bitCheck[2:]

    if flagRegs[(8-bit)] == "1":
        return True
    else: return False


##################### INITIALIZATIONS ##############################

readOptions = ['Status Signals','I/O','Setpoint','Power Output',       # WHEN ADDING AND REMOVING READ OPTIONS,
    			'Voltage Output','Percent Match','Frequency',		   # EDIT INSTRUMENT READS AND LOGGING IN
    			'Heat On Timer','Temperatures', 					   # THE READLOOP FUNCTION AND CSV WRITER
    			'Start Frequency', 'Fault Status', 
    			'Cable Current', 'Last Cycle Time']

listCOM = findCOM()
bauds = ['9600']								#'14400','19200','28800','38400','57600','115200' DISCONNECT INSTRUMENT
modType = ['MODBUS-N','MODBUS-E']
addrList = listAddr()
####################################################################


class ToplevelWindow(customtkinter.CTkToplevel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.geometry("300x345")
		self.title("Connect Device")
		
		self.after(200,lambda:self.iconbitmap(resource_path(("assets\\ambrellico.ico"))))
		self.minsize(300,345)
		self.grid_columnconfigure(1,weight=1)
		self.grid_rowconfigure(0,weight=1)


		self.labelDevice = customtkinter.CTkLabel(self, font=("Segoe UI", 15), text="Select COM Device")
		self.labelDevice.grid(row=0,column=1,padx=(20,10),pady=(0,0), sticky='nswe')
		self.comMenu = customtkinter.CTkOptionMenu(self, values=listCOM)
		self.comMenu.grid(row=1,column=1,padx=2,pady=2)

		self.labelBaud = customtkinter.CTkLabel(self, font=("Segoe UI", 15), text="Baud Rate")
		self.labelBaud.grid(row=2,column=1,padx=10,pady=(8,0), sticky='nswe')
		self.baudMenu = customtkinter.CTkOptionMenu(self, values=bauds)
		self.baudMenu.grid(row=3,column=1,padx=2,pady=2)

		self.labelModType = customtkinter.CTkLabel(self, font=("Segoe UI", 15), text="Connection Type")
		self.labelModType.grid(row=4,column=1,padx=10,pady=(8,0), sticky='nswe')
		self.modMenu = customtkinter.CTkOptionMenu(self, values=modType)
		self.modMenu.grid(row=5,column=1,padx=2,pady=2)

		self.labelAddr = customtkinter.CTkLabel(self, font=("Segoe UI", 15), text="Ambrell System Address")
		self.labelAddr.grid(row=6,column=1,padx=10,pady=(8,0), sticky='nswe')
		self.addrMenu = customtkinter.CTkOptionMenu(self, values=addrList)
		self.addrMenu.grid(row=7,column=1,padx=2,pady=2)

		self.connectButton = customtkinter.CTkButton(self, text="Connect", font=("Segoe UI", 15), height= 40, command=self.button_connect)
		self.connectButton.grid(row=8,column=1,padx=10,pady=(25,10), sticky='ew')

	def button_connect(self):
		self.comGet = self.comMenu.get()
		#com=comGet[0:5]
		self.baudGet = self.baudMenu.get()
		self.modGet = self.modMenu.get()
		self.addrGet = self.addrMenu.get()
		sendInstrumentData()
		app.deviceButton.configure(text_color="lime green")
		self.destroy()
		return 


class MyCheckboxFrame(customtkinter.CTkFrame):
	def __init__(self,master, values):
		super().__init__(master)
		self.values = values
		self.checkboxes = []

		for i,value in enumerate(self.values):
			checkbox = customtkinter.CTkCheckBox(self,text=value, font=("Segoe UI", 15) , width=200)
			checkbox.grid(row=i+1,column=0,padx=20,pady=5,sticky='nswe')
			self.checkboxes.append(checkbox)


class App(customtkinter.CTk):
	def __init__(self):
		super().__init__()

		self.title('Ambrell Modbus RTU Monitor')
		self.geometry('700x700')
		self.iconbitmap(resource_path(("assets\\ambrellico.ico")))
		self.minsize(700,700)
		self.grid_columnconfigure(1,weight=1)
		self.grid_rowconfigure(7,weight=1)

		self.instrument = None
		self.running = False
		self.checked_checkboxes = []
		self.sampleRate = 0
		self.sampleCheck = 0
		self.sampleEntry = 0
		self.logList = []
		self.n=0
		self.n = 0
		self.status_n = 0
		self.io_n = 0
		self.sp_n = 0
		self.pwrout_n = 0
		self.vltout_n = 0
		self.match_n = 0
		self.freq_n = 0
		self.heattime_n = 0
		self.temps_n = 0
		self.startfreq_n = 0
		self.fault_n = 0
		self.current_n = 0
		self.status_list = []
		self.io_list = []
		self.sp_list = []
		self.pwrout_list = []
		self.vltout_list = []
		self.match_list = []
		self.freq_list = []
		self.heattime_list = []
		self.temps_list = []
		self.startfreq_list = []
		self.fault_list = []
		self.current_list = []

		self.textbox = customtkinter.CTkTextbox(master=self, width=500, corner_radius=0, font=("Segoe UI", 15))
		self.textbox.grid(row=0, column=1, rowspan=8, sticky="nsew")

		self.checkbox_frame_1 = MyCheckboxFrame(self, values = readOptions)
		self.checkbox_frame_1.grid(row=3,column=0,padx=10,pady=(0,0), sticky='nswe')

		self.entry = customtkinter.CTkEntry(self, font=("Segoe UI", 15), placeholder_text="Sample Rate (sec)")
		self.entry.grid(row=4,column=0,padx=5,pady=(10,0), sticky='nsew')

		self.runButton = customtkinter.CTkButton(self, text="Read", font=("Segoe UI", 15), height= 40, command=self.button_read)
		self.runButton.grid(row=5,column=0,padx=5,pady=(10,10), sticky='ew')

		self.stopButton = customtkinter.CTkButton(self, text="Stop [ESC]", font=("Segoe UI", 15), height= 40, fg_color='red', hover_color = 'dark red', state="disabled", command=self.button_stop)
		self.stopButton.grid(row=6,column=0,padx=5,pady=(0,10), sticky='ew')

		self.deviceButton = customtkinter.CTkButton(self, text="Connect Device", font=("Segoe UI", 15), height=40, command=self.open_toplevel)
		self.deviceButton.grid(row=0,column=0,padx=5,pady=5, sticky='ew')

		self.switch_var = customtkinter.StringVar(value="on")
		self.loggingSwitch = customtkinter.CTkSwitch(self, text="Enable Logging", font=("Segoe UI",15), variable=self.switch_var, onvalue="on", offvalue="off")
		self.loggingSwitch.grid(row=2,column=0,padx=5,pady=(0,10), sticky='ew')

		self.readToggleVar = customtkinter.StringVar(value="continuous")
		self.readToggle = customtkinter.CTkSwitch(self, text="Continuous Mode", font=("Segoe UI",15), variable=self.readToggleVar, command=self.switch_event, onvalue="continuous", offvalue = "single")
		self.readToggle.grid(row=1,column=0,padx=5,pady=(0,10), sticky='ew')


		self.toplevel_window = None


	def open_toplevel(self):
		if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
			self.toplevel_window = ToplevelWindow(self)  # create window if its None or destroyed
			self.toplevel_window.attributes('-topmost', 'true')
		else:
			self.toplevel_window.focus()  # if window exists focus it

	def switch_event(self):
		if self.readToggleVar.get() == "single":
			self.loggingSwitch.deselect()
			self.loggingSwitch.configure(state="disabled")
		else:
			self.loggingSwitch.configure(state="normal")


	def button_read(self):
		self.textbox.delete("0.0", "end") 
		self.checked_checkboxes = []
		self.logList = []
		self.textbox.insert('end', 'Connecting to MODBUS...')


		for checkbox in self.checkbox_frame_1.checkboxes:
			checkbox.configure(state="disabled")
			if checkbox.get() == 1:
				self.checked_checkboxes.append(checkbox.cget("text"))
		#self.textbox.insert('end', '\n' + str(self.checked_checkboxes))    #debug


		if len(self.checked_checkboxes) == 0:
			self.textbox.insert('end', '\nNo Parameters Selected. ')
			for checkbox in self.checkbox_frame_1.checkboxes:
				checkbox.configure(state="normal")

		else:
			self.n = 0
			self.status_n = 0
			self.io_n = 0
			self.sp_n = 0
			self.pwrout_n = 0
			self.vltout_n = 0
			self.match_n = 0
			self.freq_n = 0
			self.heattime_n = 0
			self.temps_n = 0
			self.startfreq_n = 0
			self.fault_n = 0
			self.current_n = 0
			self.status_list = []
			self.io_list = []
			self.sp_list = []
			self.pwrout_list = []
			self.vltout_list = []
			self.match_list = []
			self.freq_list = []
			self.heattime_list = []
			self.temps_list = []
			self.startfreq_list = []
			self.fault_list = []
			self.current_list = []


			self.sampleEntry = self.entry.get()
			try:
				self.sampleCheck = int(self.sampleEntry)
			except ValueError:
				self.sampleCheck = 0

			self.sampleRate = self.sampleCheck * 1000


			try:
				self.instrument = minimalmodbus.Instrument(self.com,int(self.addr),debug=False)  # port name, slave address (in decimal)
				self.instrument.serial.port = self.com
				self.instrument.serial.baudrate = int(self.baud)
				self.instrument.serial.bytesize = 8
				self.instrument.serial.parity   = serial.PARITY_NONE	#setParity()
				self.instrument.serial.stopbits = 2	#setStopBits()
				self.instrument.serial.timeout  = 0.5      			#Default 0.05                 #seconds #default 0.05
				self.instrument.serial.write_timeout = 2.0  			#Default 2

				self.instrument.address    =  int(self.addr)                       # this is the slave address number
				self.instrument.mode = minimalmodbus.MODE_RTU            	     # rtu or ascii mode
				self.instrument.clear_buffers_before_each_transaction = True
				self.instrument.close_port_after_each_call = True

				self.running = True
				self.mode = MSB(self.instrument.read_register(30))
				self.celsius = LSB(self.instrument.read_register(32))

			except:
				self.textbox.insert('end', '\nCould not connect to MODBUS device.')
				self.runButton.configure(state="normal")
				self.stopButton.configure(state="disabled")
				for checkbox in self.checkbox_frame_1.checkboxes:
					checkbox.configure(state="normal")


	def readLoop(self):
		if self.running and self.instrument:
			self.textbox.delete("0.0", "end") 
			self.runButton.configure(state="disabled")
			self.stopButton.configure(state="normal")

			self.timeLog = datetime.datetime.now()
			self.logList.append(self.timeLog)
			self.timeHead = ['Log']

			if 'Status Signals' in self.checked_checkboxes:
				try:
					fullStatus = self.instrument.read_register(0)

					self.textbox.insert('end', '\nReady Signal: ')
					self.readySig = flagCheck(1,LSB(fullStatus))
					self.textbox.insert('end', self.readySig)
					self.logList.append(self.readySig)
					
					self.textbox.insert('end', '\nHeat Signal: ')
					self.heatSig = flagCheck(2,LSB(fullStatus))
					self.textbox.insert('end', self.heatSig)
					self.logList.append(self.heatSig)
				
					self.textbox.insert('end', '\nLimit Signal: ')
					self.limitSig = flagCheck(3,LSB(fullStatus))
					self.textbox.insert('end', self.limitSig)
					self.logList.append(self.limitSig)
					
					self.textbox.insert('end', '\nFault Signal: ')
					self.faultSig = flagCheck(4,LSB(fullStatus))
					self.textbox.insert('end', self.faultSig)
					self.logList.append(self.faultSig)

					self.textbox.insert('end', '\nESTOP Signal: ')
					self.estopSig = flagCheck(6,MSB(fullStatus))
					self.textbox.insert('end', self.estopSig)
					self.logList.append(self.estopSig)
					
					self.textbox.insert('end', '\nSystem Door: ')
					self.doorSig = flagCheck(7,MSB(fullStatus))
					self.textbox.insert('end', self.doorSig)
					self.logList.append(self.doorSig)

					self.textbox.insert('end', '\nWorkhead Cover: ')
					self.wkhdSig = flagCheck(8,MSB(fullStatus))
					self.textbox.insert('end', self.wkhdSig)
					self.logList.append(self.wkhdSig)

					self.status_list = ['Ready','Heat','Limit','Fault','ESTOP','Door','Wkhd Cover'] #update list if read signals change
					self.status_n = len(self.status_list)
				except:
					self.textbox.insert('end', '\nFailed to read STATUS SIGNALS')
			else: pass


			if 'I/O' in self.checked_checkboxes:
				try:
					full_IO = self.instrument.read_register(0)

					self.textbox.insert('end', '\nDOUT1 Signal: ')
					self.dout1Sig = flagCheck(5,LSB(full_IO))
					self.textbox.insert('end', self.dout1Sig)
					self.logList.append(self.dout1Sig)

					self.textbox.insert('end', '\nDOUT2 Signal: ')
					self.dout2Sig = flagCheck(6,LSB(full_IO))
					self.textbox.insert('end', self.dout2Sig)
					self.logList.append(self.dout2Sig)

					self.textbox.insert('end', '\nDOUT3 Signal: ')
					self.dout3Sig = flagCheck(7,LSB(full_IO))
					self.textbox.insert('end', self.dout3Sig)
					self.logList.append(self.dout3Sig)

					self.textbox.insert('end', '\nDOUT4 Signal: ')
					self.dout4Sig = flagCheck(8,LSB(full_IO))
					self.textbox.insert('end', self.dout4Sig)
					self.logList.append(self.dout4Sig)

					self.textbox.insert('end', '\nDIN1 Signal: ')
					self.din1Sig = flagCheck(3,MSB(full_IO))
					self.textbox.insert('end', self.din1Sig)
					self.logList.append(self.din1Sig)

					self.textbox.insert('end', '\nDIN2 Signal: ')
					self.din2Sig = flagCheck(4,MSB(full_IO))
					self.textbox.insert('end', self.din2Sig)
					self.logList.append(self.din2Sig)

					self.textbox.insert('end', '\nAN:IN2: ')
					self.anin2Sig = round(self.instrument.read_float(13,3,2,1),2)
					self.textbox.insert('end', self.anin2Sig)
					self.logList.append(self.anin2Sig)

					self.io_list = ['DOUT1','DOUT2','DOUT3','DOUT4','DIN1','DIN2','AN:IN2']
					self.io_n = len(self.io_list)
				except:
					self.textbox.insert('end', '\nFailed to read I/O SIGNALS')
			else: pass


			if 'Setpoint' in self.checked_checkboxes:
				try:
					#self.mode = MSB(self.instrument.read_register(30))
					if self.mode == 0:
						self.textbox.insert('end', '\nVoltage Setpoint: ') 
						self.vspSig = round(self.instrument.read_float(5,3,2,1),2)
						self.textbox.insert('end', self.vspSig)
						self.logList.append(self.vspSig)

						self.sp_list = ['Voltage Set']
						self.sp_n = len(self.sp_list)

					else:
						self.textbox.insert('end', '\nPower Setpoint: ')
						self.pspSig = round(self.instrument.read_float(7,3,2,1),2)
						self.textbox.insert('end', self.pspSig)
						self.logList.append(self.pspSig)

						self.sp_list = ['Power Set']
						self.sp_n = len(self.sp_list)
				except:
					self.textbox.insert('end', '\nFailed to read SETPOINT')
			else: pass

			if 'Power Output' in self.checked_checkboxes:
				try:
					self.textbox.insert('end', '\nPower Output: ')
					self.poutSig = round(self.instrument.read_float(3,3,2,1),2)
					self.textbox.insert('end', self.poutSig)
					self.logList.append(self.poutSig)

					self.pwrout_list = ['Power Out']
					self.pwrout_n = len(self.pwrout_list)
				except:
					self.textbox.insert('end', '\nFailed to read POWER OUTPUT')
			else: pass

			if 'Voltage Output' in self.checked_checkboxes:
				try:
					self.textbox.insert('end', '\nVoltage Output: ')
					self.voutSig = round(self.instrument.read_float(1,3,2,1),2)
					self.textbox.insert('end', self.voutSig)
					self.logList.append(self.voutSig)

					self.vltout_list = ['Voltage Out']
					self.vltout_n = len(self.vltout_list)
				except:
					self.textbox.insert('end', '\nFailed to read VOLTAGE OUTPUT')
			else: pass
			
			if 'Percent Match' in self.checked_checkboxes:
				try:
					self.textbox.insert('end', '\nPercent Match: ')
					self.matchSig = round(self.instrument.read_float(9,3,2,1),2)
					self.textbox.insert('end', self.matchSig)
					self.logList.append(self.matchSig)

					self.match_list = ['Match']
					self.match_n = len(self.match_list)
				except:
					self.textbox.insert('end', '\nFailed to read PERCENT MATCH')
			else: pass
			
			if 'Frequency' in self.checked_checkboxes:
				try:
					self.textbox.insert('end', '\nFrequency(Hz): ') 
					self.freqSig = self.instrument.read_long(11,3,False,1)
					self.textbox.insert('end', self.freqSig)
					self.logList.append(self.freqSig)

					self.freq_list = ['Frequency']
					self.freq_n = len(self.freq_list)
				except:
					self.textbox.insert('end', '\nFailed to read FREQUENCY')
			else: pass
			
			if 'Heat On Timer' in self.checked_checkboxes:
				try:

					timer1 = self.instrument.read_register(15)
					timer2 = self.instrument.read_register(16)
					self.htimeSig = (str(LSB(timer1)) + ':' + str(MSB(timer1)) + ':' +
									 str(LSB(timer2)) + ':' + str(MSB(timer2)))

					self.textbox.insert('end', '\nHeat On Timer: ')
					self.textbox.insert('end', self.htimeSig)
					self.logList.append(self.htimeSig)
					
					self.heattime_list = ['Heat Time']
					self.heattime_n = len(self.heattime_list)
				except:
					self.textbox.insert('end', '\nFailed to read HEAT ON TIMER')
			else: pass
			

			if 'Temperatures' in self.checked_checkboxes:
				try:
					#celsius = LSB(self.instrument.read_register(32))
					if self.celsius == 0:
						self.textbox.insert('end', '\nIGBT Temp (F): ')
						self.igbttempfSig = decodeReg(instrument.read_register(17))
						self.textbox.insert('end', self.igbttempfSig)
						self.logList.append(self.igbttempfSig)

						self.textbox.insert('end', '\nAmbient Temp (F): ')
						self.airtempfSig = decodeReg(regInt=self.instrument.read_register(21))
						self.textbox.insert('end', self.airtempfSig)
						self.logList.append(self.airtempfSig)

						self.temps_list = ['IGBT Temp_F','Air Temp_F']
						self.temps_n = len(self.temps_list)

					else:
						self.textbox.insert('end', '\nIGBT Temp (C): ')
						self.igbttempcSig = decodeReg(self.instrument.read_register(18))
						self.textbox.insert('end', self.igbttempcSig)
						self.logList.append(self.igbttempcSig)

						self.textbox.insert('end', '\nAmbient Temp (C): ')
						self.airtempcSig = decodeReg(regInt=self.instrument.read_register(22))
						self.textbox.insert('end', self.airtempcSig)
						self.logList.append(self.airtempcSig)

						self.temps_list = ['IGBT Temp_C','Air Temp_C']
						self.temps_n = len(self.temps_list)
				except:
					self.textbox.insert('end', '\nFailed to read TEMPERATURE')
			else: pass
			

			if 'Start Frequency' in self.checked_checkboxes:
				try:
					self.textbox.insert('end', '\nStart Frequency: ')
					self.stfrSig = self.instrument.read_long(27,3,False,1)
					self.textbox.insert('end', self.stfrSig)
					self.logList.append(self.stfrSig)

					self.startfreq_list = ['Start Freq']
					self.startfreq_n = len(self.startfreq_list)
				except:
					self.textbox.insert('end', '\nFailed to read START FREQUENCY')
			else: pass
			

			if 'Fault Status' in self.checked_checkboxes: #REDO AS BITWISE
				try:
					faultReg79 = self.instrument.read_register(79)
					faultReg80 = self.instrument.read_register(80)
					faultReg81 = self.instrument.read_register(81)


					self.textbox.insert('end', '\nWorkhead Cap Flow Fault:')
					self.wkcapSig = flagCheck(1, MSB(faultReg79))
					self.textbox.insert('end', self.wkcapSig)
					self.logList.append(self.wkcapSig)

					self.textbox.insert('end', '\nWorkhead Coil Flow Fault:')
					self.wkcoilSig = flagCheck(2, MSB(faultReg79))
					self.textbox.insert('end', self.wkcoilSig)
					self.logList.append(self.wkcoilSig)

					flowJ11  = flagCheck(1, LSB(faultReg79))
					flowJ12  = flagCheck(2, LSB(faultReg79))
					flowFLS2 = flagCheck(3, LSB(faultReg79))
					xfFLS1   = flagCheck(1, MSB(faultReg81))
					igbtFLS6 = flagCheck(2, MSB(faultReg81))
					xfFLS3   = flagCheck(3, MSB(faultReg81))
					xfFLS4   = flagCheck(4, MSB(faultReg81))
					xfFLS5   = flagCheck(5, MSB(faultReg81))

					internalFLSWfault = flowJ11 or flowJ12 or flowFLS2 or xfFLS1 or igbtFLS6 or xfFLS3 or xfFLS4 or xfFLS5				

					self.textbox.insert('end', '\nPower Supply Flow Fault:')
					self.inflsSig = internalFLSWfault
					self.textbox.insert('end', self.inflsSig)
					self.logList.append(self.inflsSig)

					self.textbox.insert('end', '\nMissing Phase Detect:')
					self.phaseSig = flagCheck(1, LSB(faultReg80))
					self.textbox.insert('end', self.phaseSig)
					self.logList.append(self.phaseSig)

					self.textbox.insert('end', '\nGround Fault:')
					self.gndSig = flagCheck(4, MSB(faultReg79))
					self.textbox.insert('end', self.gndSig)
					self.logList.append(self.gndSig)

					self.textbox.insert('end', '\nOver Maximum Power Fault:')
					self.mxpwrSig = flagCheck(6, MSB(faultReg79))
					self.textbox.insert('end', self.mxpwrSig)
					self.logList.append(self.mxpwrSig)

					self.textbox.insert('end', '\nFrequency Low Limit:')
					self.freqlowSig = flagCheck(1, MSB(faultReg80))
					self.textbox.insert('end', self.freqlowSig)
					self.logList.append(self.freqlowSig)

					self.textbox.insert('end', '\nFrequency High Limit:')
					self.freqhiSig = flagCheck(2, MSB(faultReg80))
					self.textbox.insert('end', self.freqhiSig)
					self.logList.append(self.freqhiSig)

					self.textbox.insert('end', '\nWorkhead Maximum Volts Limit:')
					self.wkmaxvSig = flagCheck(3, MSB(faultReg80))
					self.textbox.insert('end', self.wkmaxvSig)
					self.logList.append(self.wkmaxvSig)

					self.textbox.insert('end', '\nMaximum Match Limit:')
					self.maxmatchSig =  flagCheck(5, MSB(faultReg80))
					self.textbox.insert('end', self.maxmatchSig)
					self.logList.append(self.maxmatchSig)

					self.textbox.insert('end', '\nOutput Max Power Limit:')
					self.maxpwrSig = flagCheck(6, MSB(faultReg80))
					self.textbox.insert('end', self.maxpwrSig)
					self.logList.append(self.maxpwrSig)

					self.textbox.insert('end', '\nOutput Max Current Fault:')
					self.maxcurSig = flagCheck(4, MSB(faultReg81))
					self.textbox.insert('end', self.maxcurSig)
					self.logList.append(self.maxcurSig)

					self.textbox.insert('end', '\nOutput Max Bus Cap Fault:')
					self.maxbuscapSig = flagCheck(5, MSB(faultReg81))
					self.textbox.insert('end', self.maxbuscapSig)
					self.logList.append(self.maxbuscapSig)

					self.textbox.insert('end', '\nIGBT Max Temp Limit:')
					self.igbtmaxSig = flagCheck(7, MSB(faultReg80))
					self.textbox.insert('end', self.igbtmaxSig)
					self.logList.append(self.igbtmaxSig)

					self.textbox.insert('end', '\nIGBT Max Delta Temp Limit:')
					self.igbtdeltaSig = flagCheck(8, MSB(faultReg80))
					self.textbox.insert('end', self.igbtdeltaSig)
					self.logList.append(self.igbtdeltaSig)

					self.textbox.insert('end', '\nIGBT Temp Fault:')
					self.igbttfaultSig = flagCheck(7, MSB(faultReg79))
					self.textbox.insert('end', self.igbttfaultSig)
					self.logList.append(self.igbttfaultSig)

					self.textbox.insert('end', '\nMax Delta Temp Fault:')
					self.dltatempSig = flagCheck(8, MSB(faultReg79))
					self.textbox.insert('end', self.dltatempSig)
					self.logList.append(self.dltatempSig)

					self.textbox.insert('end', '\nDOUT Overcurrent Fault:')
					self.doutfaultSig = flagCheck(5, MSB(faultReg79))
					self.textbox.insert('end', self.doutfaultSig)
					self.logList.append(self.doutfaultSig)

					self.textbox.insert('end', '\nAlarm Tripped Limit:')
					self.altripSig = flagCheck(4, MSB(faultReg80))
					self.textbox.insert('end', self.altripSig)
					self.logList.append(self.altripSig)

					self.fault_list = ['Wrkd Cap Flow Fault', 'Wrkd Coil Flow Fault', 'Internal Flow Fault',     #update list if number of fault signals change DO NOT CHANGE ORDER
										 'Missing Phase Detect', 'Ground Fault', 'Over Maximum Power Fault', 
										 'Frequency Low Limit', 'Frequency High Limit', 'Workhead Maximum Volts Limit',
										 'Maximum Match Limit', 'Output Max Power Limit', 'Output Max Current Fault',
										 'Output Max Bus Cap Fault', 'IGBT Max Temp Limit', 'IGBT Max Delta Temp Limit',
										 'IGBT Temp Fault', 'Max Delta Temp Fault', 'DOUT Overcurrent Fault', 'Alarm Tripped Limit']

					self.fault_n = len(self.fault_list)
				except:
					self.textbox.insert('end', '\nFailed to read FAULTS')
			else: pass
			

			if 'Cable Current' in self.checked_checkboxes:
				try:
					self.textbox.insert('end', '\nCable Current: ')
					self.cableSig = round(self.instrument.read_float(100,3,2,1),2)
					self.textbox.insert('end', self.cableSig)
					self.logList.append(self.cableSig)

					self.current_list = ['Cable Current']
					self.current_n = len(self.current_list) 
				except:
					self.textbox.insert('end', '\nFailed to read CABLE CURRENT')
			else: pass
			

			if 'Last Cycle Time' in self.checked_checkboxes:
				try:
					lastCycle_1 = self.instrument.read_register(45)
					lastCycle_2 = self.instrument.read_register(46)

					self.textbox.insert('end', '\nLast Cycle Time: ')
					self.textbox.insert('end', str(LSB(lastCycle_1)) + ':' +
												str(MSB(lastCycle_1)) + ':' +
												str(LSB(lastCycle_2)) + ':' +
												str(MSB(lastCycle_2)))
				except:
					self.textbox.insert('end', '\nFailed to read Last Cycle Time')
			else: pass	


		self.n = (1 + self.status_n + self.io_n + self.sp_n + self.pwrout_n + self.vltout_n + self.match_n + 
			self.freq_n + self.heattime_n + self.temps_n + self.startfreq_n + self.fault_n + self.current_n)

		if self.readToggleVar.get() == "single":
			self.running = False
			self.runButton.configure(state="normal")
			self.stopButton.configure(state="disabled")
			for checkbox in self.checkbox_frame_1.checkboxes:
				checkbox.configure(state="normal")
		
		self.after((300 + self.sampleRate), self.readLoop)

		return


	def stop_button_check(self,esc):
		if self.running == False:
			pass 
		else:
			try:
				self.button_stop()
			except: pass


	def button_stop(self):
		self.running = False
		self.runButton.configure(state="normal")
		self.stopButton.configure(state="disabled")
		for checkbox in self.checkbox_frame_1.checkboxes:
			checkbox.configure(state="normal")
		#print(self.logList)    #debug
		#print(self.n)			#debug


		if self.switch_var.get() == "on":	

			self.textbox.insert('end','\nWriting file ' + (resource_path('logs\\Ambrell_Modbus_Log '+ writeTime + '.csv')))

			headerList = (self.timeHead + self.status_list + self.io_list + self.sp_list + self.pwrout_list +
					 	 self.vltout_list + self.match_list + self.freq_list + self.heattime_list +
					 	 self.temps_list + self.startfreq_list + self.fault_list + self.current_list)
			#print(headerList)     #debug

			now = datetime.datetime.now()
			writeTime = now.strftime('%Y_%m_%d %H-%M-%S')

			try:
				with open(resource_path('logs\\Ambrell_Modbus_Log '+ writeTime + '.csv'),'w') as csvfile:
					writer = csv.writer(csvfile)
					writer.writerow(headerList)
					for log in range(0,len(self.logList),self.n):
						writer.writerow(self.logList[log:log+self.n])
						#del self.logList[0:self.n]
					self.textbox.insert('end', '\nLogged to <Ambrell_Modbus_Log'+ writeTime + '.csv>')

			except: self.textbox.insert('end', '\nCould not write to file.')

		else: pass
		return


app = App()
app.bind('<Escape>',app.stop_button_check)

if app.readToggleVar.get() == "single":
	self.running = False
	self.runButton.configure(state="normal")
	self.stopButton.configure(state="disabled")
	for checkbox in self.checkbox_frame_1.checkboxes:
		checkbox.configure(state="normal")

app.after((300 + app.sampleRate), app.readLoop)
app.mainloop()