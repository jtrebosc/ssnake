#!/usr/bin/env python

import numpy as np
import sys
if sys.version_info >= (3,0):
    from tkinter import *
    import tkinter as tk
    from tkinter.ttk import *
    from tkinter.filedialog import askopenfilename
else:
    from Tkinter import *
    import Tkinter as tk
    from ttk import *
    from tkFileDialog   import askopenfilename
import spectrum_classes as sc
import fitting as fit
import math
#For varianload
import os
from struct import unpack
#------------
from safeEval import safeEval

pi=math.pi

#one window to rule them all
class Main1DWindow(Frame):
    def __init__(self,parent):
        Frame.__init__(self,parent)
        self.undoList = [] #the list to hold all the undo lambda functions
        self.redoList = [] #the list to hold all the redo lambda functions
        self.parent = parent #remember your parents
        #create the menu
        menubar = Menu(self.parent)
        self.parent.config(menu=menubar)
        #the file drop down menu
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New", command=self.NewFile)
        filemenu.add_command(label="Open...", command=self.OpenFile)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        #the hotkeys for different commands
        self.bind_all("<Control-q>", lambda extra: self.quit())
        self.bind_all("<Control-z>", self.undo)
        self.bind_all("<Control-y>", self.redo)
	#the load drop down menu
        loadmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Load", menu=loadmenu)
        loadmenu.add_command(label="Load Varian data", command=self.LoadVarianFile)
        loadmenu.add_command(label="Load infinity data", command=self.LoadChemFile)
        loadmenu.add_command(label="Load Simpson data", command=self.LoadSimpsonFile)
        
        #the save drop down menu
        savemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Save", menu=savemenu)
        savemenu.add_command(label="Save as Simpson data", command=self.SaveSimpsonFile)
        
	#the edit drop down menu
        editmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=editmenu)
        editmenu.add_command(label="Undo", command=self.undo)
        editmenu.add_command(label="Redo", command=self.redo)

	#the tool drop down menu
        toolMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools",menu=toolMenu)
        toolMenu.add_command(label="Real", command=self.real)
        toolMenu.add_command(label="Imag", command=self.imag)
        toolMenu.add_command(label="Abs", command=self.abs) 
        toolMenu.add_command(label="Apodize", command=self.createApodWindow)
        toolMenu.add_command(label="Phasing", command=self.createPhaseWindow)
        toolMenu.add_command(label="Sizing", command=self.createSizeWindow) 
        toolMenu.add_command(label="Swap Echo", command=self.createSwapEchoWindow)
        toolMenu.add_command(label="Shift Data", command=self.createShiftDataWindow)
        toolMenu.add_command(label="DC offset correction", command=self.createDCWindow)

        #the fft drop down menu
        fftMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fourier",menu=fftMenu)
        fftMenu.add_command(label="Fourier transform", command=self.fourier)
        fftMenu.add_command(label="Fftshift", command=self.fftshift)
        fftMenu.add_command(label="Inv fftshift", command=self.invFftshift)
        fftMenu.add_command(label="Hilbert transform", command=self.hilbert)

	#the fitting drop down menu
        fittingMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fitting",menu=fittingMenu)
        fittingMenu.add_command(label="Relaxation Curve", command=self.createRelaxWindow)
        fittingMenu.add_command(label="Peak Deconvolution", command=self.createPeakDeconvWindow)

	#the plot drop down menu
        plotMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plot",menu=plotMenu)
        plotMenu.add_command(label="1D plot", command=self.plot1D)
        plotMenu.add_command(label="Stack plot", command=self.plotStack)
        plotMenu.add_command(label="User x-axis", command=self.createXaxWindow)

        x=np.linspace(0,2*np.pi*10,1000)[:-1] #fake data
        test=np.exp(-1j*x)*np.exp(-1*x/10.0)#fake data
        self.masterData=sc.Spectrum(np.array([np.array([test,test*2,test*3]),np.array([test*3,test*4,test*5])]),[600000000.0,500000000.0,400000000.0],[1000.0,2000.0,3000.0])#create a Spectrum instance with the fake data
        self.current=sc.Current1D(self,self.masterData) 
        #self.current=sc.CurrentStacked(self,self.masterData) 
        self.current.grid(row=0,column=0,sticky="nswe")
	#create the sideframe, bottomframe and textframe
        self.sideframe=SideFrame(self) 
        self.sideframe.grid(row=0,column=2,sticky='n')
        Separator(self,orient=VERTICAL).grid(row=0,column=1,rowspan=4,sticky='ns')
        self.bottomframe=BottomFrame(self)
        self.bottomframe.grid(row=1,column=0,sticky='w') 
        Separator(self,orient=HORIZONTAL).grid(row=2,sticky='ew')
        self.textframe=TextFrame(self)
        self.textframe.grid(row=3,column=0,sticky='s')  

#all the functions that will be called from the menu and the extra frames

    def NewFile(self):
        print("New File!") #to be added

    def OpenFile(self):
        name = askopenfilename() #to be added
        print(name)

    def LoadVarianFile(self):
        FilePath = askopenfilename()
        if FilePath is not '': #if not canceled
            Dir = os.path.dirname(FilePath) #convert path to file to path of folder
            #Extract Procpar data if it exist------------------------
            #Initilize standard values
            freq = 300e6
            sw   = 50e3
            sw1  = 50e3
            if os.path.exists(Dir+'/procpar'):
                with open(Dir+'/procpar', 'r') as f: #read entire procfile (data[0] gives first line)
                    data = f.read().split('\n')
                for s in range(0,len(data)): #exctract info from procpar
                    if data[s].startswith('sfrq '):
                        freq=float(data[s+1].split()[1])*1e6 #convert to MHz
                    elif data[s].startswith('sw '):
                        sw=float(data[s+1].split()[1])
                    elif data[s].startswith('sw1 '):
                        sw1=float(data[s+1].split()[1])
            else:
                print(Dir+'/procpar does not exits, used standard sw and freq')
            #Get fid data----------------------------- 
            if os.path.exists(Dir+'/fid'):    
                try:
                    with open(Dir+'/fid', "rb") as f:
                        raw = np.fromfile(f, np.int32,6) #read 6 steps, 32 bits
                        nblocks = unpack('>l', raw[0])[0] #unpack bitstring using bigendian and as LONG interger
                        ntraces = unpack('>l', raw[1])[0]
                        npoints = unpack('>l', raw[2])[0]
                        ebytes = unpack('>l', raw[3])[0]
                        tbytes = unpack('>l', raw[4])[0]
                        bbytes = unpack('>l', raw[5])[0]
                        raw = np.fromfile(f, np.int16,2) #16bit, 2 steps
                        vers_id = unpack('>h', raw[0])[0] #bigendian short
                        status = unpack('>h', raw[1])[0]
                        raw = np.fromfile(f, np.int32,1) 
                        nbheaders = unpack('>l', raw[0])[0]
                        SizeTD2 = npoints
                        SizeTD1 = nblocks*ntraces
                        a = []
                        fid32 = bin(status)[-3] #check if 32 bits, or float
                        fidfloat = bin(status)[-4]
                        for iter1 in range(0,nblocks): #now read all blocks
                            b = []
                            for iter2 in range(0,nbheaders):
                                raw = np.fromfile(f, np.int16,nbheaders*14)
                            if not fid32 and not fidfloat:
                                raw = np.fromfile(f, np.int16,ntraces*npoints)
                                for iter3 in raw:
                                    b.append(unpack('>h', iter3)[0])
                            elif fid32 and not fidfloat:
                                raw = np.fromfile(f, np.int32,ntraces*npoints)
                                for iter3 in raw:
                                    b.append(unpack('>l', iter3)[0])
                            else:
                                raw = np.fromfile(f, np.float32,ntraces*npoints)
                                for iter3 in raw:
                                    b.append(unpack('>f', iter3)[0])
                            b=np.array(b)
                            if(len(b) != ntraces*npoints):
                                b.append(np.zeros(ntraces*npoints-len(b)))
                            a.append(b)
                    a=np.complex128(a)
                    fid = a[:,::2]-1j*a[:,1::2]
                    self.current.grid_remove()
                    self.current.destroy()
                    if SizeTD1 is 1: #convert to 1D dat if the data is 1D (so no 1xnp data, but np)
                        fid = fid[0][:]
                        self.masterData=sc.Spectrum(fid,[freq],[sw])
                        self.current=sc.Current1D(self,self.masterData) #create the Current1D instance from the Spectrum  
                    else: #For 2D data
                        self.masterData=sc.Spectrum(fid,[freq]*2,[sw]*2)
                        self.current=sc.Current1D(self,self.masterData) #create the Current1D instance from the Spectrum  
                    #add some check to see if current exists
                    self.current.grid(row=0,column=0,sticky="nswe")
                    self.updAllFrames()
                except:
                    print('Error loading Varian data from '+Dir+'/fid. No data loaded!')
            else: #If /fid does not exist
                print(Dir+'/fid does not exits, no Varian data loaded!')

    def LoadChemFile(self):
        name = askopenfilename()#to be added
        print(name)
        
    def LoadSimpsonFile(self):
        #Loads Simpson data (Fid or Spectrum) to the ssNake data format
        FileLocation = askopenfilename()#to be added
        if FileLocation is not '': #if not empty
            with open(FileLocation, 'r') as f: #read entire procfile (data[0] gives first line)
                Lines = f.read().split('\n')
            try:
                NP, NI, SW, SW1, TYPE, FORMAT = 0,1,0,0,'','Normal'
                for s in range(0,len(Lines)):
                    if Lines[s].startswith('NP='):
                        NP = int(re.sub('NP=','',Lines[s]))
                    elif Lines[s].startswith('NI='):
                        NI = int(re.sub('NI=','',Lines[s]))
                    elif Lines[s].startswith('SW='):
                        SW = float(re.sub('SW=','',Lines[s]))
                    elif Lines[s].startswith('SW1='):
                        SW1 = float(re.sub('SW1=','',Lines[s]))
                    elif Lines[s].startswith('TYPE='):
                        TYPE = re.sub('TYPE=','',Lines[s])
                    elif Lines[s].startswith('FORMAT='):
                        FORMAT = re.sub('FORMAT=','',Lines[s])
                    elif Lines[s].startswith('DATA'):
                        DataStart = s
                    elif Lines[s].startswith('END'):
                        DataEnd = s
                if 'Normal' in FORMAT: #If normal format (e.g. not binary)
                    data = []
                    for iii in range(DataStart+1,DataEnd): #exctract data
                        temp = Lines[iii].split()
                        data.append(float(temp[0])+1j*float(temp[1]))
                elif 'BINARY' in FORMAT: #needs to be im-plemented
                    AGD=1
                data = np.array(data) #convert to numpy array
                self.current.grid_remove()
                self.current.destroy()
                if 'FID' in TYPE:
                    axis=0
                    spec = [False]
                elif 'SPE' in TYPE:
                    axis=1
                    spec = [True]
                if NI is 1:
                    self.masterData=sc.Spectrum(data,[0],[SW],spec)
                    self.current=sc.Current1D(self,self.masterData) #create the Current1D instance from the Spectrum  
                else:
                    data = np.transpose(data.reshape((NP,NI)))
                    self.masterData=sc.Spectrum(data,[0,0],[SW,SW1],spec*2)
                    self.current=sc.Current1D(self,self.masterData) #create the Current1D instance from the Spectrum  
                self.current.grid(row=0,column=0,sticky="nswe")
                self.updAllFrames()
            except:
                print('Error loading Simpson data from '+FileLocation+' . No data loaded!')
        
    def SaveSimpsonFile(self):
        akhfv=1
        
    def real(self):
        self.redoList = []
        self.undoList.append(self.masterData.real())
        self.current.upd()
        self.current.showFid()

    def imag(self):
        self.redoList = []
        self.undoList.append(self.masterData.imag())
        self.current.upd()
        self.current.showFid()

    def abs(self):
        self.redoList = []
        self.undoList.append(self.masterData.abs())
        self.current.upd()
        self.current.showFid()

    def fourier(self):
        self.redoList = []
        self.undoList.append(self.current.fourier())
        self.bottomframe.upd()

    def fftshift(self):
        self.redoList = []
        self.undoList.append(self.current.fftshift())
        self.updAllFrames()

    def invFftshift(self):
        self.redoList = []
        self.undoList.append(self.current.fftshift(inv=True))
        self.updAllFrames()
    
    def hilbert(self):
        self.redoList = []
        self.undoList.append(self.current.hilbert())

    def setFreq(self,freq,sw):
        self.redoList = []
        self.undoList.append(self.current.setFreq(freq,sw))

    def createPhaseWindow(self):
        PhaseWindow(self,self.current)
        
    def createApodWindow(self):
        ApodWindow(self,self.current)

    def createSizeWindow(self):
        SizeWindow(self,self.current)

    def createSwapEchoWindow(self):
        SwapEchoWindow(self,self.current)

    def createShiftDataWindow(self):
        ShiftDataWindow(self,self.current)

    def createDCWindow(self):
        DCWindow(self,self.current)

    def createRelaxWindow(self):
        root = fit.RelaxWindow(self.parent,self.current)
        root.title("Relaxation Curve") 
        #root.attributes('-zoomed', True)
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

    def createPeakDeconvWindow(self):
        root = fit.PeakDeconvWindow(self.parent,self.current)
        root.title("Peak Deconvolution") 
        #root.attributes('-zoomed', True)
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
    
    def plot1D(self):
        self.current.grid_remove()
        self.current.destroy()
        self.current = sc.Current1D(self,self.masterData)
        self.current.grid(row=0,column=0,sticky="nswe")
        self.updAllFrames()

    def plotStack(self):
        if len(self.masterData.data.shape) > 1:
            self.current.grid_remove()
            self.current.destroy()
            self.current = sc.CurrentStacked(self,self.masterData) 
            self.current.grid(row=0,column=0,sticky="nswe")
            self.updAllFrames()
        else:
            print("Data does not have enough dimensions")

    def createXaxWindow(self):
        XaxWindow(self,self.current)

    def updAllFrames(self):
        self.bottomframe.upd()
        self.sideframe.upd()

    def undo(self, *args):
        if self.undoList:
            self.redoList.append(self.undoList.pop()(self.masterData))
            self.current.upd()
            self.current.plotReset()
            self.current.showFid()
            self.updAllFrames()
        else:
            print("no undo information")

    def redo(self, *args):
        if self.redoList:
            self.undoList.append(self.redoList.pop()(self.masterData))
            self.current.upd()
            self.current.plotReset()
            self.current.showFid()
            self.updAllFrames()
        else:
            print("no redo information")

########################################################################################
#the sideframe class which displays (if necessary) the position of the shown data relative to the full data matrix
class SideFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self,parent)
        self.parent = parent
        self.labels=[]
        self.entries=[]
        self.entryVars=[]
        self.buttons1=[]
        self.button1Var=IntVar()
        self.button1Var.set(0)
        self.buttons2=[]
        self.button2Var=IntVar()
        self.button2Var.set(1)
        self.plotIs2D = False
        self.upd()

    def upd(self): #destroy the old widgets and create new ones 
        self.current = self.parent.current
        self.shape = self.current.data.data.shape
        self.length = len(self.shape)
        self.button1Var.set(self.current.axes)
        offset = 0
        self.plotIs2D = isinstance(self.current, sc.CurrentStacked)
        if self.plotIs2D:
            offset = 1
            self.button2Var.set(self.current.axes2)
        for num in self.labels:
            num.destroy()
        self.labels = []
        for num in self.entries:
            num.destroy()
        self.entries=[]
        for num in self.buttons1:
            num.destroy()
        self.buttons1=[]
        for num in self.buttons2:
            num.destroy()
        self.buttons2=[]
        self.entryVars = []
        if self.length > 1:
            for num in range(self.length):
                self.buttons1.append(Radiobutton(self, variable=self.button1Var, value=num, command=lambda: self.setAxes(True)))
                self.buttons1[num].grid(row=num*2+1,column=0)
                if self.plotIs2D:
                    self.buttons2.append(Radiobutton(self, variable=self.button2Var, value=num, command=lambda: self.setAxes(False)))
                    self.buttons2[num].grid(row=num*2+1,column=1)
                self.labels.append(Label(self,text="TD"+str(num+1))) 
                self.labels[num].grid(row=num*2,column=1+offset)
                self.entryVars.append(StringVar())
                if not self.plotIs2D:
                    if num < self.current.axes:
                        self.entryVars[num].set(str(self.current.locList[num]))
                    elif num == self.current.axes:
                        self.entryVars[num].set("0")
                    else:
                        self.entryVars[num].set(str(self.current.locList[num-1]))
                else:
                    if (num < self.current.axes) and (num < self.current.axes2):
                        self.entryVars[num].set(str(self.current.locList[num]))
                    elif (num == self.current.axes) or (num == self.current.axes2):
                        self.entryVars[num].set("0")
                    elif (num > self.current.axes) or (num > self.current.axes2):
                        self.entryVars[num].set(str(self.current.locList[num-1]))
                    else:
                        self.entryVars[num].set(str(self.current.locList[num-2]))
                self.entries.append(Spinbox(self,textvariable=self.entryVars[num],from_=0,to=self.shape[num]-1,justify="center",command=lambda event=None,num=num: self.getSlice(event,num)))
                self.entries[num].bind("<Return>", lambda event=None,num=num: self.getSlice(event,num)) 
                self.entries[num].grid(row=num*2+1,column=1+offset)

    def setAxes(self,first=True):
        if self.plotIs2D:
            axes= self.button1Var.get()
            axes2=self.button2Var.get()
            if axes==axes2:
                if first:
                    axes2 = self.current.axes
                else:
                    axes = self.current.axes2
            self.button2Var.set(axes2)
            self.getSlice(None, axes,True)
        else:
            self.getSlice(None, self.button1Var.get(),True)

    def getSlice(self, event, entryNum, button=False): #change the slice which is currently displayed
        if button:
            dimNum = entryNum
        elif not self.plotIs2D:
            if entryNum == self.current.axes:
                if entryNum == self.length-1:
                    dimNum = self.length-2
                else:
                    dimNum = self.length-1
            else:
                dimNum = self.current.axes
        else:
            dimNum = self.current.axes

        locList=[]
        for num in range(self.length):
            appendLoc = True
            if self.plotIs2D and (num == self.button2Var.get()):
                appendLoc = False
            inp = safeEval(self.entryVars[num].get())
            if num == dimNum:
                pass
            else:
                if inp < -self.shape[num]:
                    val=int(round(-(self.shape[num])))
                elif inp >= self.shape[num]:
                    val=int(round(self.shape[num]-1))
                elif inp < 0:
                    val = int(round(self.shape[num] + inp)) 
                else:
                    val = int(round(inp))
                if appendLoc:
                    locList.append(val)
                self.entryVars[num].set(val)
        self.button1Var.set(dimNum)
        if self.plotIs2D:
            self.current.setBlock(dimNum,self.button2Var.get(), locList)
        else:
            self.current.setSlice(dimNum,locList)
        self.parent.bottomframe.upd()

################################################################################  
#the bottom frame holding the fourier button and stuff      
class BottomFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self,parent)
        self.parent = parent
        self.current = parent.current
        self.specVal = IntVar() #value for the time/freq radiobutton
        self.freqVal = StringVar() #value for frequency entybox
        self.swVal = StringVar() #value for sw entrybox
        self.plotOption = StringVar() #value for dropdown plot type box
        self.plotOption.set("Real")
        self.axisOption1 = StringVar()
        self.axisOption2 = StringVar()
        self.echoTick = IntVar()
        self.echoTick.set(0)
        Button(self, text="Fourier",command=self.parent.fourier).grid(row=0,column=0,rowspan=2)
        self.rb1 = Radiobutton(self,text="Time",variable=self.specVal,value=0,command=self.changeSpec)
        self.rb1.grid(row=0,column=1)
        self.rb2 = Radiobutton(self,text="Frequency",variable=self.specVal,value=1,command=self.changeSpec)
        self.rb2.grid(row=1,column=1)
        Checkbutton(self,text="Whole echo",variable=self.echoTick, command=self.setWholeEcho).grid(row=0,column=2,rowspan=2)
        Label(self,text="Freq (MHz)").grid(row=0,column=3)
        self.freqEntry = Entry(self,textvariable=self.freqVal,justify='center')
        self.freqEntry.bind("<Return>", self.changeFreq)
        self.freqEntry.grid(row=1,column=3)
        Label(self,text="Sweepwidth (kHz)").grid(row=0,column=4)
        self.swEntry = Entry(self,textvariable=self.swVal,justify='center')
        self.swEntry.bind("<Return>", self.changeFreq)
        self.swEntry.grid(row=1,column=4)
        Label(self,text="Plot").grid(row=0,column=5)
        self.plotDrop = OptionMenu(self, self.plotOption,"Real","Real", "Imag", "Both","Abs",command=self.changePlot)
        self.plotDrop.grid(row=1,column=5)
        Label(self,text="Axis").grid(row=0,column=6)
        self.axisDropTime = OptionMenu(self, self.axisOption1, "s", "s", "ms", u"\u03bcs",command=self.changeAxis)
        self.axisDropFreq = OptionMenu(self, self.axisOption2, "Hz", "Hz", "kHz", "MHz","ppm",command=self.changeAxis)
        self.axisDropTime.grid(row=1,column=6)
        self.axisDropFreq.grid(row=1,column=6)
        self.swEntry
        self.upd()
 
    def upd(self): #upd the values displayed in the bottom menu
        self.current = self.parent.current
        self.freqVal.set(str(self.current.freq/1000000)) #show in MHz
        self.swVal.set(str(self.current.sw/1000)) #show in kHz
        if self.current.spec==0:
            self.specVal.set(0)
            self.axisDropFreq.grid_forget()
            self.axisDropTime.grid(row=1,column=6)
            val = self.current.axType
            if val == 0:
                self.axisOption1.set("s")
            elif val == 1:
                self.axisOption1.set("ms")
            elif val == 2:
                self.axisOption1.set( u"\u03bcs")
                
        elif self.current.spec==1:
            self.specVal.set(1)
            self.axisDropTime.grid_forget()
            self.axisDropFreq.grid(row=1,column=6)
            val = self.current.axType
            if val == 0:
                self.axisOption1.set("Hz")
            elif val == 1:
                self.axisOption1.set("kHz")
            elif val == 2:
                self.axisOption1.set("MHz")
            elif val == 3:
                self.axisOption1.set("ppm")
        if self.current.wholeEcho:
            self.echoTick.set(1)
        else:
            self.echoTick.set(0)

    def setWholeEcho(self):
        self.current.setWholeEcho(self.echoTick.get())

    def changeSpec(self, *args): #change from time to spectral domain and vice versa
        self.parent.redoList = []
        self.parent.undoList.append(self.current.changeSpec(self.specVal.get()))
        self.upd()

    def changeFreq(self, *args): #change the frequency and sw of the displayed axes
        freq = safeEval(self.freqVal.get())*1000000 #show in MHz
        sw = safeEval(self.swVal.get())*1000 #show in kHz
        if freq != 0 and sw != 0:
            self.parent.setFreq(freq,sw)
        self.upd()
    
    def changePlot(self, *args): #change the plot type
        pType = self.plotOption.get()
        if pType == "Real":
            self.current.plotType=0
        elif pType == "Imag":
            self.current.plotType=1
        elif pType == "Both":
            self.current.plotType=2
        elif pType == "Abs":
            self.current.plotType=3
        self.current.showFid()

    def changeAxis(self, *args):
        if self.current.spec == 0:
            pType = self.axisOption1.get()
            if pType == "s":
                self.current.setAxType(0)
            elif pType == "ms":
                self.current.setAxType(1)
            elif pType == u"\u03bcs":
                self.current.setAxType(2)
        if self.current.spec == 1:
            pType = self.axisOption2.get()
            if pType == "Hz":
                self.current.setAxType(0)
            elif pType == "kHz":
                self.current.setAxType(1)
            elif pType == "MHz":
                self.current.setAxType(2)
            elif pType == "ppm":
                print("not implemented yet")
                #self.current.setAxType(3)
        self.current.showFid()

##################################################################
#the frame showing the get position data
class TextFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self,parent)
        self.parent = parent
        self.pos = StringVar()      #number of get_position data point
        self.pos.set(str(0))
        self.oldx = 0.0
        self.oldy = 0.0
        self.xpoint = StringVar()   #x value of the get_position data point
        self.xpoint.set(str(self.oldx))
        self.ypoint = StringVar()   #y value of the get_position data point
        self.ypoint.set(str(self.oldy))
        self.deltaxpoint = StringVar()   #x value of the get_position data point
        self.deltaxpoint.set(str(0.0))
        self.deltaypoint = StringVar()   #y value of the get_position data point
        self.deltaypoint.set(str(0.0))
        
        Button(self,text="get Position", command=self.getPosition).grid(row=0,column=0)
        Label(self,text="Position:").grid(row=0,column=1)
        Entry(self,textvariable=self.pos,justify='center').grid(row=0,column=2)
        Label(self,text="x-value:").grid(row=0,column=3)
        Entry(self,textvariable=self.xpoint,justify='center').grid(row=0,column=4)
        Label(self,text="y-value:").grid(row=0,column=5)
        Entry(self,textvariable=self.ypoint,justify='center').grid(row=0,column=6)
        Label(self,text=u"\u0394x:").grid(row=0,column=7)
        Entry(self,textvariable=self.deltaxpoint,justify='center').grid(row=0,column=8)
        Label(self,text=u"\u0394y:").grid(row=0,column=9)
        Entry(self,textvariable=self.deltaypoint,justify='center').grid(row=0,column=10)
    
    def setLabels(self,position):
        self.deltaxpoint.set('%.3e' % np.abs(self.oldx-position[1]))
        self.deltaypoint.set('%.3e' % np.abs(self.oldy-position[2]))
        self.pos.set(str(position[0]))
        self.xpoint.set('%.3e' % position[1])
        self.ypoint.set('%.3e' % position[2])
        self.oldx = position[1]
        self.oldy = position[2]

    def getPosition(self, *args):
        self.parent.current.peakPickFunc = lambda pos,self=self: self.setLabels(pos) 
        self.parent.current.peakPick = True
        
#################################################################################   
class PhaseWindow(Frame): #a window for phasing the data
    def __init__(self, parent,current):
        Frame.__init__(self, parent)
        #initialize variables for the widgets
        self.zeroValue = StringVar()
        self.zeroValue.set("0.00")
        self.firstValue = StringVar()
        self.firstValue.set("0.000")
        self.refValue = StringVar()
        self.refValue.set("0.0")
        #set stepsizes for the buttons
        self.phase0step = 0.01
        self.phase1step = 0.001
        #create a new window
        self.parent = parent
        self.current = current
        self.window = Toplevel(self)
        self.window.geometry('+0+0')
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancelAndClose)
        self.window.title("Phasing")
        self.window.resizable(width=FALSE, height=FALSE)
        Label(self.window,text="Zero order phasing").grid(row=0,column=0,columnspan=3)
        Button(self.window,text="Autophase 0th order",command=lambda: self.autophase(0)).grid(row=1,column=1)
        self.zeroEntry = Entry(self.window,textvariable=self.zeroValue,justify="center")
        self.zeroEntry.bind("<Return>", self.inputZeroOrder)
        self.zeroEntry.grid(row=2,column=1)
        tk.Button(self.window,text="<",repeatdelay=100, repeatinterval=1,command=lambda:self.stepPhase(-1,0)).grid(row=2,column=0)
        tk.Button(self.window,text=">",repeatdelay=100, repeatinterval=1,command=lambda:self.stepPhase(1,0)).grid(row=2,column=2)
        self.zeroScale=Scale(self.window, from_=-pi, to=pi,  orient="horizontal", command=self.setZeroOrder,length=300)
        self.zeroScale.grid(row=3,column=0,columnspan=3)
        Label(self.window,text="First order phasing").grid(row=4,column=0,columnspan=3)
        Button(self.window,text="Autophase 0th+1st order",command=lambda: self.autophase(1)).grid(row=5,column=1)
        self.firstEntry = Entry(self.window,textvariable=self.firstValue,justify="center")
        self.firstEntry.bind("<Return>", self.inputFirstOrder) 
        self.firstEntry.grid(row=6,column=1)
        tk.Button(self.window,text="<",repeatdelay=100, repeatinterval=1,command=lambda:self.stepPhase(0,-1)).grid(row=6,column=0)
        tk.Button(self.window,text=">",repeatdelay=100, repeatinterval=1,command=lambda:self.stepPhase(0,1)).grid(row=6,column=2)
        self.firstScale=Scale(self.window, from_=-0.1*pi*(self.current.data1D.shape[-1])/self.current.sw, to=0.1*pi*self.current.data1D.shape[-1]/self.current.sw, orient="horizontal", command=self.setFirstOrder,length=300)
        self.firstScale.grid(row=7,column=0,columnspan=3)
        Label(self.window,text="Reference").grid(row=8,column=0,columnspan=3)
        self.refEntry = Entry(self.window,textvariable=self.refValue,justify="center")
        self.refEntry.bind("<Return>", self.inputRef) 
        self.refEntry.grid(row=9,column=1)
        if self.current.spec > 0:
            Button(self.window, text="Pick reference", command=self.pickRef).grid(row=10,column=1)
        Button(self.window, text="Apply",command=self.applyPhaseAndClose).grid(row=11,column=0)
        Button(self.window, text="Cancel",command=self.cancelAndClose).grid(row=11,column=2)      
        
    def setZeroOrder(self,value, *args): #function called by the zero order scale widget
        self.zeroValue.set('%.3e' % float(value))
        self.current.setPhaseInter(self.zeroValue.get(),self.firstValue.get())
        
    def inputZeroOrder(self, *args): #function called by the zero order entry widget
        inp = safeEval(self.zeroValue.get())
        inp = np.mod(inp+pi,2*pi)-pi
        self.zeroScale.set(inp) #setting the scale to a value calls the previous function, so the phase of current doesn't need to be set here

    def setFirstOrder(self,value, *args): #function called by the first order scale widget
        newZero = (float(self.zeroValue.get())-(float(value)-float(self.firstValue.get()))*float(self.refValue.get())) #calculate the new zero order phase depending on the reference
        newZero = np.mod(newZero+pi,2*pi)-pi
        self.firstValue.set('%.3e' % float(value))
        self.zeroValue.set('%.3e' % newZero)
        self.zeroScale.set(newZero)

    def inputFirstOrder(self, *args): #function called by the first order entry widget
        inp = safeEval(self.firstValue.get())
        self.firstScale.set(inp) #setting the scale to a value calls the previous function, so the phase of current doesn't need to be set here

    def autophase(self, num): #run the autophase for either zero order (0) or both orders (1)
        phases = self.current.autoPhase(num)
        if num == 0:
            phase0=(np.mod(phases[0]+pi,2*pi)-pi)
            self.zeroValue.set('%.3e' % phase0)
            self.zeroScale.set(phase0)
        elif num == 1:
            phase0=(np.mod(phases[0]+pi,2*pi)-pi)
            self.zeroValue.set('%.3e' % phase0)
            self.zeroScale.set(phase0)
            self.firstValue.set('%.3e' % phases[1])
            self.firstScale.set(phases[1])

    def stepPhase(self,phase0,phase1): #step phase from < and > keys
        inp = safeEval(self.zeroValue.get())+phase0*self.phase0step
        inp = np.mod(inp+pi,2*pi)-pi
        self.zeroScale.set(inp)
        inp = safeEval(self.firstValue.get())+phase1*self.phase1step
        self.firstScale.set(inp)

    def inputRef(self, *args): #set the reference from the entry widget
        inp = safeEval(self.refValue.get())
        self.refValue.set('%.3e' % inp)

    def pickRef(self, *args): #run the pick function to pick the reference value
        self.current.peakPickFunc = lambda pos,self=self: self.refValue.set('%.2f' % pos[1])
        self.current.peakPick = True

    def cancelAndClose(self):
        self.current.upd()
        self.current.showFid()
        self.window.destroy()

    def applyPhaseAndClose(self):
        self.parent.redoList = []
        self.parent.undoList.append(self.current.applyPhase(self.zeroValue.get(),self.firstValue.get()))
        self.window.destroy()

################################################################
class ApodWindow(Frame): #a window for apodization
    def __init__(self, parent,current):
        Frame.__init__(self, parent)
        #initialize variables for the widgets
        self.lorTick = IntVar()
        self.lorVal = StringVar()
        self.lorVal.set("0.0")
        self.gaussTick = IntVar()
        self.gaussVal = StringVar()
        self.gaussVal.set("0.0")
        self.cos2Tick = IntVar()
        self.cos2Val = StringVar()
        self.cos2Val.set("1.0")
        #set stepsizes for the buttons
        self.lorstep = 1.0
        self.gaussstep = 1.0
        self.parent = parent
        self.current = current
        self.window = Toplevel(self)
        self.window.geometry('+0+0')
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancelAndClose)
        self.window.title("Apodize")
        self.window.resizable(width=FALSE, height=FALSE)
        self.frame1 = Frame(self.window)
        self.frame1.grid(row=0,column=0)
        Label(self.frame1,text="Lorentzian").grid(row=0,column=0,columnspan=4)
        Checkbutton(self.frame1,variable=self.lorTick, command=lambda: self.checkEval(self.lorTick,self.lorEntry)).grid(row=1,column=1)
        self.lorEntry = Entry(self.frame1,textvariable=self.lorVal,justify="center", state='disabled')   
        tk.Button(self.frame1,text="<",repeatdelay=100, repeatinterval=1,command=lambda:self.stepLB(-0.5*self.current.sw/(self.current.data1D.shape[-1]),0)).grid(row=1,column=0)
        tk.Button(self.frame1,text=">",repeatdelay=100, repeatinterval=1,command=lambda:self.stepLB(0.5*self.current.sw/(self.current.data1D.shape[-1]),0)).grid(row=1,column=4)
        self.lorEntry.bind("<Return>", self.apodPreview)
        self.lorEntry.grid(row=1,column=2)
        self.lorScale=Scale(self.frame1, from_=0, to=100.0*self.current.sw/(self.current.data1D.shape[-1]),  orient="horizontal", command=self.setLor,length=200)
        self.lorScale.grid(row=2,column=1,columnspan=2)
        Label(self.frame1,text="Gaussian").grid(row=3,column=0,columnspan=4)
        Checkbutton(self.frame1,variable=self.gaussTick, command=lambda: self.checkEval(self.gaussTick,self.gaussEntry)).grid(row=4,column=1)
        self.gaussEntry = Entry(self.frame1,textvariable=self.gaussVal,justify="center", state='disabled')
        self.gaussEntry.bind("<Return>", self.apodPreview)
        self.gaussEntry.grid(row=4,column=2)
        tk.Button(self.frame1,text="<",repeatdelay=100, repeatinterval=1,command=lambda:self.stepLB(0,-0.5*self.current.sw/(self.current.data1D.shape[-1]))).grid(row=4,column=0)
        tk.Button(self.frame1,text=">",repeatdelay=100, repeatinterval=1,command=lambda:self.stepLB(0,0.5*self.current.sw/(self.current.data1D.shape[-1]))).grid(row=4,column=4)
        self.gaussScale=Scale(self.frame1, from_=0, to=100.0*self.current.sw/(self.current.data1D.shape[-1]),  orient="horizontal", command=self.setGauss,length=200)
        self.gaussScale.grid(row=5,column=1,columnspan=2)
        Label(self.frame1,text="Cos^2").grid(row=6,column=0,columnspan=4)
        Checkbutton(self.frame1,variable=self.cos2Tick, command=lambda: self.checkEval(self.cos2Tick,self.cos2Entry)).grid(row=7,column=1)
        self.cos2Entry = Entry(self.frame1,textvariable=self.cos2Val,justify="center", state='disabled')
        self.cos2Entry.bind("<Return>", self.apodPreview)
        self.cos2Entry.grid(row=7,column=2)
        self.frame2 = Frame(self.window)
        self.frame2.grid(row=1,column=0)
        Button(self.frame2, text="Apply",command=self.applyApodAndClose).grid(row=0,column=0)
        Button(self.frame2, text="Cancel",command=self.cancelAndClose).grid(row=0,column=2) 

    def checkEval(self,checkVar,entryVar): #change the state of the entry widget that the 
        if checkVar.get() == 0:
            entryVar.configure(state='disabled')
        else:
            entryVar.configure(state='normal')
        self.apodPreview()

    def setLor(self,value, *args): #set the lorentzian value from the scale widget
        if self.lorTick.get() == 0:
            self.lorTick.set(1)
            self.lorEntry.configure(state='normal')
        self.lorVal.set('%.2f' % float(value))
        self.apodPreview()

    def setGauss(self,value, *args): #set the gaussian value from the scale widget
        if self.gaussTick.get() == 0:
            self.gaussTick.set(1)
            self.gaussEntry.configure(state='normal')
        self.gaussVal.set('%.2f' % float(value))
        self.apodPreview()

    def apodPreview(self, *args): #display the apodization preview
        lor = None
        gauss = None
        cos2 = None
        if self.lorTick.get() == 1:
            lor = safeEval(self.lorVal.get())
            self.lorVal.set(lor)
        if self.gaussTick.get() == 1:
            gauss = safeEval(self.gaussVal.get())
            self.gaussVal.set(gauss)
        if self.cos2Tick.get() == 1:
            cos2 = safeEval(self.cos2Val.get())
            self.cos2Val.set(cos2)
        self.current.apodPreview(lor,gauss,cos2)

    def stepLB(self,lorincr,gaussincr): #step linebroadening from < and > keys
        if lorincr!=0:
            self.lorScale.set(float(self.lorVal.get())+lorincr*self.lorstep)
        if gaussincr!=0:
            self.gaussScale.set(float(self.gaussVal.get())+gaussincr*self.gaussstep)

    def cancelAndClose(self):
        self.current.upd()
        self.current.showFid()
        self.window.destroy()

    def applyApodAndClose(self):
        lor = None
        gauss = None
        cos2 = None
        if self.lorTick.get() == 1:
            lor = safeEval(self.lorVal.get())
        if self.gaussTick.get() == 1:
            gauss = safeEval(self.gaussVal.get())
        if self.cos2Tick.get() == 1:
            cos2 = safeEval(self.cos2Val.get())
        self.parent.redoList = []
        self.parent.undoList.append(self.current.applyApod(lor,gauss,cos2))
        self.window.destroy()

#######################################################################################
class SizeWindow(Frame): #a window for changing the size of the current dimension
    def __init__(self, parent,current):
        #initialize variables for the widgets
        self.sizeVal = StringVar()
        self.sizeVal.set(str(current.data1D.shape[-1]))
        #create a new window
        Frame.__init__(self, parent)
        self.parent = parent
        self.current = current
        self.window = Toplevel(self)
        self.window.geometry('+0+0')
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancelAndClose)
        self.window.title("Set size")
        self.window.resizable(width=FALSE, height=FALSE)
        self.frame1 = Frame(self.window)
        self.frame1.grid(row=0)
        Label(self.frame1,text="Set size").grid(row=0,column=0,columnspan=2)
        self.sizeEntry = Entry(self.frame1,textvariable=self.sizeVal,justify="center")
        self.sizeEntry.bind("<Return>", self.sizePreview)
        self.sizeEntry.grid(row=1,column=0,columnspan=2)
        self.frame2 = Frame(self.window)
        self.frame2.grid(row=1)
        Button(self.frame2, text="Apply",command=self.applySizeAndClose).grid(row=0,column=0)
        Button(self.frame2, text="Cancel",command=self.cancelAndClose).grid(row=0,column=1)
 
    def sizePreview(self, *args): #display the size preview from the entry widget value
        size = int(round(safeEval(self.sizeVal.get())))
        if size < 1:
            size = 1
        self.sizeVal.set(str(size))
        self.current.setSizePreview(size)

    def cancelAndClose(self):
        self.current.upd()
        self.current.plotReset()
        self.current.showFid()
        self.window.destroy()

    def applySizeAndClose(self):
        size = int(round(safeEval(self.sizeVal.get())))
        if size < 1:
            size = 1
        self.parent.redoList = []
        self.parent.undoList.append(self.current.applySize(size))
        self.parent.sideframe.upd()
        self.window.destroy()

##########################################################################################
class SwapEchoWindow(Frame): #a window for changing the size of the current dimension
    def __init__(self, parent,current):
        Frame.__init__(self, parent)
        #initialize variables for the widgets
        self.posVal = StringVar()
        self.posVal.set(str(int(round(0.5*len(current.data1D)))))
        self.parent = parent
        self.current = current
        self.window = Toplevel(self)
        self.window.geometry('+0+0')
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancelAndClose)
        self.window.title("Swap echo")
        self.window.resizable(width=FALSE, height=FALSE)
        self.frame1 = Frame(self.window)
        self.frame1.grid(row=0)
        Label(self.frame1,text="Position").grid(row=0,column=0,columnspan=2)
        self.posEntry = Entry(self.frame1,textvariable=self.posVal,justify="center")
        self.posEntry.bind("<Return>", self.swapEchoPreview)
        self.posEntry.grid(row=1,column=0,columnspan=2)
        self.frame2 = Frame(self.window)
        self.frame2.grid(row=1)
        Button(self.frame2, text="Apply",command=self.applySwapEchoAndClose).grid(row=0,column=0)
        Button(self.frame2, text="Cancel",command=self.cancelAndClose).grid(row=0,column=1)
        #activate the peak picking
        self.current.peakPickFunc = lambda pos,self=self: self.pickedAndClose(pos) 
        self.current.peakPick = True
 
    def swapEchoPreview(self, *args): #preview the swap echo result from the entry widget
        pos = int(round(safeEval(self.posVal.get())))
        if pos > 0 and pos < (self.current.data1D.shape[-1]):
            self.current.setSwapEchoPreview(pos)

    def cancelAndClose(self):
        self.current.peakPickReset()
        self.current.upd()
        self.current.plotReset()
        self.current.showFid()
        self.window.destroy()

    def applySwapEchoAndClose(self):
        self.current.peakPickReset()
        pos = int(round(safeEval(self.posVal.get())))
        if pos > 0 and pos < (self.current.data1D.shape[-1]):
            self.parent.redoList = []
            self.parent.undoList.append(self.current.applySwapEcho(pos))
            self.parent.bottomframe.upd()
            self.window.destroy()
        else:
            print("not a valid index for swap echo")
        
    def pickedAndClose(self,pos): #apply directly if picked since another doesn't make pick doesn't make sense. find a good way to do both entry and picking in a proper way
        self.parent.redoList = []
        self.parent.undoList.append(self.current.applySwapEcho(pos[0]))
        self.parent.bottomframe.upd()
        self.window.destroy()

###########################################################################
class ShiftDataWindow(Frame): #a window for shifting the data
    def __init__(self, parent,current):
        Frame.__init__(self, parent)
        #initialize variables for the widgets
        self.shiftVal = StringVar()
        self.shiftVal.set("0")
        self.parent = parent
        self.current = current
        self.window = Toplevel(self)
        self.window.geometry('+0+0')
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancelAndClose)
        self.window.title("Shift data")
        self.window.resizable(width=FALSE, height=FALSE)
        self.frame1 = Frame(self.window)
        self.frame1.grid(row=0)
        Label(self.frame1,text="number of points to shift").grid(row=0,column=0,columnspan=2)
        self.posEntry = Entry(self.frame1,textvariable=self.shiftVal,justify="center")
        self.posEntry.bind("<Return>", self.shiftPreview)
        self.posEntry.grid(row=1,column=0,columnspan=2)
        self.frame2 = Frame(self.window)
        self.frame2.grid(row=1)
        Button(self.frame2, text="Apply",command=self.applyShiftAndClose).grid(row=0,column=0)
        Button(self.frame2, text="Cancel",command=self.cancelAndClose).grid(row=0,column=1)
 
    def shiftPreview(self, *args): #preview a shifted spectrum from the entry widget
        shift = int(round(safeEval(self.shiftVal.get())))
        self.current.setShiftPreview(shift)

    def cancelAndClose(self):
        self.current.upd()
        self.current.plotReset()
        self.current.showFid()
        self.window.destroy()

    def applyShiftAndClose(self):
        shift = int(round(safeEval(self.shiftVal.get())))
        self.parent.redoList = []
        self.parent.undoList.append(self.current.applyShift(shift))
        self.window.destroy()

#############################################################
class DCWindow(Frame): #a window for shifting the data
    def __init__(self, parent,current):
        Frame.__init__(self, parent)
        #initialize variables for the widgets
        self.minVal = StringVar()
        self.minVal.set("0")
        self.maxVal = StringVar()
        self.maxVal.set(str(current.data1D.shape[-1]))
        self.parent = parent
        self.current = current
        self.window = Toplevel(self)
        self.window.geometry('+0+0')
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancelAndClose)
        self.window.title("DC offset correction")
        self.window.resizable(width=FALSE, height=FALSE)
        self.frame1 = Frame(self.window)
        self.frame1.grid(row=0)
        Label(self.frame1,text="Start point").grid(row=0,column=0,columnspan=2)
        self.minEntry = Entry(self.frame1,textvariable=self.minVal,justify="center")
        self.minEntry.bind("<Return>", self.dcPreview)
        self.minEntry.grid(row=1,column=0,columnspan=2)
        Label(self.frame1,text="End point").grid(row=2,column=0,columnspan=2)
        self.maxEntry = Entry(self.frame1,textvariable=self.maxVal,justify="center")
        self.maxEntry.bind("<Return>", self.dcPreview)
        self.maxEntry.grid(row=3,column=0,columnspan=2)
        self.frame2 = Frame(self.window)
        self.frame2.grid(row=1)
        Button(self.frame2, text="Apply",command=self.applyDCAndClose).grid(row=0,column=0)
        Button(self.frame2, text="Cancel",command=self.cancelAndClose).grid(row=0,column=1)
        #pick function
        self.current.peakPickFunc = lambda pos,self=self: self.picked(pos) 
        self.current.peakPick = True

    def picked(self,pos,second=False): #pick a value alternating the first and second value determined by the second value.
        if second:
            dataLength = self.current.data1D.shape[-1]
            minimum=int(round(safeEval(self.minVal.get())))
            if minimum < 0:
                minimum = 0
            elif minimum > dataLength:
                minimum = dataLength
            self.minVal.set(str(minimum))
            maximum=pos[0]
            self.maxVal.set(str(maximum))
            self.current.peakPickFunc = lambda pos,self=self: self.picked(pos) 
            self.current.peakPick = True
            self.current.dcOffset(minimum,maximum)
        else:
            self.minVal.set(str(pos[0]))
            self.current.peakPickFunc = lambda pos,self=self: self.picked(pos,True) 
            self.current.peakPick = True

    def dcPreview(self, *args): #preview the dc offset correction
        dataLength = self.current.data1D.shape[-1]
        minimum = int(round(safeEval(self.minVal.get())))
        if minimum < 0:
            minimum = 0
        elif minimum > dataLength:
            minimum = dataLength
        self.minVal.set(str(minimum))
        maximum = int(round(safeEval(self.maxVal.get())))
        if maximum < 0:
            maximum = 0
        elif maximum > dataLength:
            maximum = dataLength
        self.maxVal.set(str(maximum))
        self.current.dcOffset(minimum,maximum)

    def cancelAndClose(self):
        self.current.peakPickReset()
        self.current.upd()
        self.current.plotReset()
        self.current.showFid()
        self.window.destroy()

    def applyDCAndClose(self):
        self.current.peakPickReset()
        dataLength = self.current.data1D.shape[-1]
        minimum = int(round(safeEval(self.minVal.get())))
        if minimum < 0:
            minimum = 0
        elif minimum > dataLength:
            minimum = dataLength
        maximum = int(round(safeEval(self.maxVal.get())))
        if maximum < 0:
            maximum = 0
        elif maximum > dataLength:
            maximum = dataLength
        self.parent.redoList = []
        self.parent.undoList.append(self.current.applydcOffset(minimum,maximum))
        self.window.destroy()

##########################################################################################
class XaxWindow(Frame): #a window for setting the xax of the current data
    def __init__(self, parent,current):
        Frame.__init__(self, parent)
        #initialize variables for the widgets
        self.val = StringVar()
        self.parent = parent
        self.current = current
        self.window = Toplevel(self)
        self.window.geometry('+0+0')
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self.cancelAndClose)
        self.window.title("User defined x-axis")
        self.window.resizable(width=FALSE, height=FALSE)
        self.frame1 = Frame(self.window)
        self.frame1.grid(row=0)
        Label(self.frame1,text="Expression for x-axis values").grid(row=0,column=0,columnspan=2)
        self.minEntry = Entry(self.frame1,textvariable=self.val,justify="center")
        self.minEntry.bind("<Return>", self.xaxPreview)
        self.minEntry.grid(row=1,column=0,columnspan=2)

        self.frame2 = Frame(self.window)
        self.frame2.grid(row=1)
        Button(self.frame2, text="Apply",command=self.applyXaxAndClose).grid(row=0,column=0)
        Button(self.frame2, text="Cancel",command=self.cancelAndClose).grid(row=0,column=1)

    def xaxPreview(self, *args):
        env = vars(np).copy()
        env['length']=int(self.current.data1D.shape[-1]) # so length can be used to in equations
        val=eval(self.val.get(),env)                # find a better solution, also add catch for exceptions          
        if isinstance(val,(list,np.ndarray)):
            if len(val)==self.current.data1D.shape[-1]:
                if all(isinstance(x,(int,float)) for x in val):
                    self.current.setXaxPreview(val)
                else:
                    print("Array is not all of int or float type")
            else:
                print("Length of input does not match length of data")
        else:
            print("Input is not a list or array")

    def cancelAndClose(self):
        self.current.upd()
        self.current.plotReset()
        self.current.showFid()
        self.window.destroy()

    def applyXaxAndClose(self):
        env = vars(np).copy()
        env['length']=int(self.current.data1D.shape[-1]) # so length can be used to in equations
        val=eval(self.val.get(),env)                # find a better solution, also add catch for exceptions
        if isinstance(val,(list,np.ndarray)):
            if len(val)==self.current.data1D.shape[-1]:
                if all(isinstance(x,(int,float)) for x in val):
                    self.current.setXax(val)
                    self.window.destroy()
                else:
                    print("Array is not all of int or float type")
            else:
                print("Length of input does not match length of data")
        else:
            print("Input is not a list or array")

#################################################################################    
#the main program
if __name__ == "__main__":
    root = Tk()
    mainWindow = Main1DWindow(root) #create an instance to control the main window
    mainWindow.pack(fill=BOTH,expand=1)
    mainWindow.rowconfigure(0, weight=1)
    mainWindow.grid_columnconfigure(0, weight=1)
    root.title("ssNake") 
    root.style = Style()
    root.style.theme_use("clam")
    root.attributes('-zoomed', True)
    root.mainloop()
