import numpy as np 
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from matplotlib.ticker import MaxNLocator
import imageio.v2 as imageio
import os
import PySimpleGUI as sg

# Define constants
c = 299792458 # Speed of light in m/s
u0 = 4*np.pi*1e-7 # Permeability of free space in H/m
acc = 100 # Accuracy of calculations

# Define functions

def runGUI():
    sg.theme('DarkAmber')   # Add a touch of color

    col1 = [[sg.Text('Amplituda prądu [A]')],
            [sg.Text('Promień pętli [m]')],
            [sg.Text('Pulsacja [rad/s]')],
            [sg.Text('Czas symulacji [s]')],
            [sg.Text('Długość osi [j]')],
            [sg.Text('Klatki na sekundę [fps]')],
            [sg.Text('Wybór płaszczyzny')],
            [sg.Text('Wybór funkcji')]]
    
    col2 = [[sg.InputText('1', key='current')],
            [sg.InputText('0.01', key='radius')],
            [sg.InputText('1', key='omega')],
            [sg.InputText('5', key='time')],
            [sg.InputText('10', key='axisLength')],
            [sg.Radio('30 FPS', 'fps', default=True, key='fps30'), sg.Radio('60 FPS', 'fps', key='fps60')],
            [sg.Radio('XY', 'plane', default=True, key='xy'),  sg.Radio('YZ', 'plane', key='yz')],
            [sg.OptionMenu(['Pole magnetyczne', 'Pole elektryczne'], 'Pole magnetyczne', key='function')]]
    
    layout = [[sg.Text('Symulacja dipola magnetycznego')],
                [sg.Column(col1), sg.Column(col2)],
                [sg.Button('Start')],
                [sg.Output(size=(80, 10))]]
    
    window = sg.Window('Symulator pól E-M dipola', layout, element_justification='c')
    return window

def checkValues(values):
    try:
        current = float(values['current'])
        radius = float(values['radius'])
        omega = float(values['omega'])
        time = float(values['time'])
        axisLength = float(values['axisLength'])
        fps = 30 if values['fps30'] else 60
        plane = 'XY' if values['xy'] else 'YZ'
        function = 'magnetic' if values['function'] == 'Pole magnetyczne' else 'electric'
        
        if current < 0 or radius < 0 or omega < 0 or time < 0 or axisLength < 0:
            print('Wartości muszą być dodatnie!')
            return False

        return current, radius, omega, time, axisLength, fps, plane, function
    except ValueError:
        print('Wartości muszą być liczbami!')
        return False
    
def calculateFieldFunction(m0, omega, time, fps, axisLength, plane, function):
    t = np.arange(0, time, 1/fps)
    r = np.linspace(radius + 0.1, axisLength * np.sqrt(2), int(fps*time))
    if plane == "XY":
        theta = np.pi/2
    elif plane == "YZ":
        theta = np.linspace(0, 2*np.pi, int(fps*time))
    
    R, Theta, T = np.meshgrid(r, theta, t, indexing='ij')
    Y = R * np.sin(Theta)
    Z = R * np.cos(Theta)

    if function == "magnetic":
        B = (-1) * ((u0 * m0 * omega ** 2)/(4 * np.pi * c ** 2)) * (np.sin(Theta)/R) * np.cos(omega * (T-R/c))
        return B, R, Theta, Z, Y, t
    elif function == "electric":
        E = ((u0 * m0 * omega ** 2)/(4 * np.pi * c)) * (np.sin(Theta)/R) * np.cos(omega * (T-R/c))
        return E, R, Theta, Z, Y, t
    
def makeFrame(fun_val, Y, Z, axisLength, plane, function, i):
    ax.set_xlim(-axisLength, axisLength)
    ax.set_ylim(-axisLength, axisLength)
    ax.set_aspect('equal', adjustable='box')
    if plane == "XY":
        c = ax.contourf(Y[:, :, 0], Y[:, :, 0], fun_val[:, :, 0], cmap='hot')
    elif plane == "YZ":
        c = ax.pcolormesh(Y[:, :, 0], Z[:, :, 0], fun_val[:, :, 0], cmap='hot')
    plt.grid(True)
    plt.title('Function Z at t=0')
    plt.colorbar(c, label=f"{function.capitalize()} Field Value")
    for j in range(1, len(t)):
        c.set_array(fun_val[:, :, j].flatten())  # Update the color values
        plt.title(f'Function Z at t={t[j]:.2f}')
        plt.pause(0.01)  # Add a short pause for visualization
    plt.show()

if __name__ == '__main__':
    window = runGUI()
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            window.close()
            break
        if checkValues(values):
            current, radius, omega, time, axisLength, fps, plane, function = checkValues(values)
            m0 = current*np.pi*radius**2

            fun_val, R, Theta, Z, Y, t = calculateFieldFunction(m0, omega, time, fps, axisLength, plane, function)

            fig = plt.figure(figsize=(8, 8), dpi=100)
            ax = fig.add_subplot(111)
            makeFrame(fun_val, Y, Z, axisLength, plane, function, 5)