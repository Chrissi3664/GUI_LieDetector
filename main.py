import serial
from scipy import signal
import numpy as np
import time
from datetime import datetime
import tkinter as tk
from tkinter.ttk import Frame
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use("TkAgg")
import pandas as pd

# Constants and global variables
com = 'COM6'        # COM Port 6
sample_time = 5     # [s]

MODE_GREEN_ONLY = True
# false: 17 samples per LED
# true: 50 samples, only green LED
# 50/3 = 16,6667

data_green = []
data_red = []
data_ir = []
data_SkinResistance = []
x = []



#################################
# Bandpass Filter
#################################

def butter_bandpass(lowcut, highcut, sample_rate, order):
    sos = signal.butter(order, [lowcut, highcut], btype='band', output='sos', fs=sample_rate)
    return sos

# butter_bandpass_filter(data_green, 0.6, 5, sample_rate, 10)
def butter_bandpass_filter(data, lowcut, highcut, sample_rate, order):
    sos = butter_bandpass(lowcut, highcut, sample_rate, order)
    y = signal.sosfiltfilt(sos, data)
    return y
#################################
# other functions
#################################

def Exit():
    exit()
    return

def ExportFigure(figure):
    date = datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
    figure.savefig('C:/Users/Christina/Desktop/Figure--' + date + '.png')
    return



def timeint(t):
    return t.second * 1000 + t.microsecond


def Receive():
    if len(box_TimeMeasure.get()) == 0:
        sample_time = 2
    else:
        sample_time = int(box_TimeMeasure.get())

    data_green = []
    data_red = []
    data_ir = []
    data_SkinResistance = []
    x = []

    # Start receiving data
    ser = serial.Serial(com, 115200, timeout=1)
    x_start = time.time()
    x_end = x_start + sample_time

    while time.time() < x_end:
        input = ser.readline().decode()
        if 'G' in input and '\n' in input:
            if MODE_GREEN_ONLY:
                data_green.append(int(input[input.find('G') + 1:input.rfind('O')]))
                data_SkinResistance.append(int(input[input.find('O') + 1:input.rfind('\n')]))
            if not MODE_GREEN_ONLY:
                data_green.append(int(input[input.find('G') + 1:input.rfind('R')]))
                data_red.append(int(input[input.find('R') + 1:input.rfind('I')]))
                data_ir.append(int(input[input.find('I') + 1:input.rfind('O')]))
                data_SkinResistance.append(int(input[input.find('O') + 1:input.rfind('\n')]))
    ser.close()

    sample_rate = len(data_green)/sample_time

    ppg_g_fil = butter_bandpass_filter(data_green, 0.6, 5, sample_rate, 10)
    peaks, _ = signal.find_peaks(ppg_g_fil, height=0.25, distance=(0.33 * sample_rate))
    df = pd.DataFrame(peaks)
    df.to_csv('file.csv', index=False)
    # print(type(peaks))
    ppg_arr = np.array(ppg_g_fil)


    #################################
    # Plot
    #################################
    boxanchor_x = 1
    boxanchor_y = 0.2

    figuresize_x = 10
    figuresize_y = 8

    figureres = 80

    if not MODE_GREEN_ONLY:
        print(data_red)
        print(data_ir)

    if MODE_GREEN_ONLY:
        figure = plt.Figure(figsize=(figuresize_x, figuresize_y), dpi=figureres)

        # plot 1: raw PPG signal
        ax1 = figure.add_subplot(311)
        ax1.set_title('Raw Photodiode Value')
        ax1.plot(data_green, color='green')
        ax1.set_ylabel('Raw Photodiode Value')
        ax1.legend(loc='right')

        # plot 2: bandpass filtered PPG signal
        ax2 = figure.add_subplot(312)
        ax2.set_title('Bandpass filtered photodiode value with peak detection')
        ax2.plot(ppg_arr, label='photodiode value')
        ax2.plot(peaks, ppg_arr[peaks], 'xr', label='detected heartbeats')
        ax2.set_ylabel('Photodiode Value')
        ax2.legend(loc='right', bbox_to_anchor=(boxanchor_x, boxanchor_y))

        # plot 3: resistance and conductance
        ax3 = figure.add_subplot(313)
        ax3.set_title('Skin Resistance')
        ax3.plot(data_SkinResistance, label='resistance', color='blueviolet')
        ax3.set_ylabel('Skin Resistance in Ohm')

        lines, labels = ax3.get_legend_handles_labels()
        ax3.legend(lines, labels, loc='right', bbox_to_anchor=(boxanchor_x, boxanchor_y))

        # styles for all plots
        axis = [ax1, ax2, ax3]
        for ax in axis:
            ax.minorticks_on()
            ax.grid(visible=True, which='major', color='gray', linestyle='-')
            ax.grid(visible=True, which='minor', color='lightgray', linestyle='--')
            ax.set_xlabel('Samples\nSamplerate = ' + str(round(sample_rate, 2)) + ' Hz')


        figure.subplots_adjust(hspace=1)
        line12 = plt.Line2D((.1, .9), (.63, .63), color="k", linewidth=.5)
        line23 = plt.Line2D((.1, .9), (.32, .32), color="k", linewidth=.5)
        figure.add_artist(line12)
        figure.add_artist(line23)

        canvas = FigureCanvasTkAgg(figure, root)
        canvas.get_tk_widget().grid(row=2, column=0, columnspan=3)
        canvas.draw_idle()


    print(len(data_SkinResistance))

    btn_ExportFig1 = tk.Button(root, text='Export Figure', command=lambda: ExportFigure(figure), height=buttonheight, width=buttonwidth)

    btn_ExportFig1.grid(row=3, column=0)

    return


#################################
# GUI
#################################
buttonheight = 1
buttonwidth = 20

inputwidth = 20

logo_resolution = 70


# GUI Code
root = tk.Tk()
root.title("Lie detector App")

# start_text = tk.StringVar()
# start_text.set("Start Measurement")

btn_Start = tk.Button(root, text='Start Measurement', command=lambda: Receive(), height=buttonheight, width=buttonwidth)
btn_Exit = tk.Button(root, text='Exit Application', command=lambda: Exit(), height=buttonheight, width=buttonwidth)

box_TimeMeasure = tk.Entry(root, width=inputwidth)

str_label = tk.StringVar()
str_label.set("Measuring time [s]")
label1 = tk.Label(root, textvariable=str_label, width=inputwidth)

# HAW Logo
logo = Image.open('HAW.jpg').resize((logo_resolution, logo_resolution)) # tuple(x,y)
logo = ImageTk.PhotoImage(logo)
logo_label = tk.Label(image=logo)
logo_label.image = logo


# place everything
btn_Start.grid(row=0, column=0, sticky="ew")
btn_Exit.grid(row=1, column=0, sticky="ew")
label1.grid(row=0, column=1)
box_TimeMeasure.grid(row=1, column=1)
logo_label.grid(row=0, column=2, rowspan=2, sticky="ew")




root.mainloop()



