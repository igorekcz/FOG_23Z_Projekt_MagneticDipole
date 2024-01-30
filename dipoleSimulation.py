import numpy as np 
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import os
import PySimpleGUI as sg
import glob
import warnings
from matplotlib.colors import SymLogNorm


# Define constants
c = 299792458 # Speed of light in m/s
u0 = 4*np.pi*1e-7 # Permeability of free space in H/m

global windowClosed
windowClosed = False

# Define functions

def runGUI():
    sg.theme('DarkAmber')   # Add a touch of color

    col1 = [[sg.Text('Amplituda prądu [A]')],
            [sg.Text('Promień pętli [m]')],
            [sg.Text('Pulsacja [rad/s]')],
            [sg.Text('Czas symulacji [s]')],
            [sg.Text('Długość osi [j]')],
            [sg.Text('Klatki na sekundę [fps]')],
            [sg.Text('Wybór funkcji')],
            [sg.Text('Skala logarytmiczna')],
            [sg.Text('Stworzyć plik mp4?')]]
    
    col2 = [[sg.InputText('10', key='current')],
            [sg.InputText('0.01', key='radius')],
            [sg.InputText('1', key='omega')],
            [sg.InputText('5', key='time')],
            [sg.InputText('1', key='axisLength')],
            [sg.Radio('30 FPS', 'fps', default=True, key='fps30'), sg.Radio('60 FPS', 'fps', key='fps60')],
            [sg.OptionMenu(['Pole magnetyczne (XZ)', 'Pole elektryczne (XZ)', 'Pole magnetyczne (XY)', 'Pole elektryczne (XY)'], 'Pole magnetyczne (XZ)', key='function')],
            [sg.Checkbox('Tak', default=False, key='log')],
            [sg.Checkbox('Tak', default=False, key='mp4')]]
    
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
        time = int(values['time'])
        axisLength = int(values['axisLength'])
        fps = 30 if values['fps30'] else 60
        function = 'magneticXZ' if values['function'] == 'Pole magnetyczne (XZ)' else 'electricXZ' if values['function'] == 'Pole elektryczne (XZ)' else 'magneticXY' if values['function'] == 'Pole magnetyczne (XY)' else 'electricXY'
        log = values['log']
        mp4 = values['mp4']
        
        if current < 0 or radius < 0 or omega < 0 or time < 0 or axisLength < 0:
            print('Wartości muszą być dodatnie!')
            return False

        return current, radius, omega, time, fps, function, mp4, axisLength, log
    except ValueError:
        print('Wartości muszą być liczbami!')
        return False
    
def calculateFieldFunction():
    t = np.arange(0, (2 * np.pi)/omega, 1/fps)
    r = np.linspace(radius + 0.1, axisLength * np.sqrt(2), 300)
    theta = np.linspace(0, 2*np.pi, 360)

    R, Theta, T = np.meshgrid(r, theta, t, indexing='ij')
    Thetap, Rp = np.meshgrid(theta, r)
    Y = Rp * np.sin(Thetap)
    X = Rp * np.cos(Thetap)

    if function == "magneticXZ":
        B = (-1) * ((u0 * m0 * omega ** 2)/(4 * np.pi * c ** 2)) * (np.sin((np.pi - np.abs(Theta - np.pi)))/R) * np.cos(omega * (T-R/c))
        return B, X, Y, t
    elif function == "electricXZ":
        E = ((u0 * m0 * omega ** 2)/(4 * np.pi * c)) * (np.sin((np.pi - np.abs(Theta - np.pi)))/R) * np.cos(omega * (T-R/c))
        return E, X, Y, t
    elif function == "magneticXY":
        B = (-1) * ((u0 * m0 * omega ** 2)/(4 * np.pi * c ** 2)) * (1/R) * np.cos(omega * (T-R/c))
        return B, X, Y, t
    elif function == "electricXY":
        E = ((u0 * m0 * omega ** 2)/(4 * np.pi * c)) * (1/R) * np.cos(omega * (T-R/c))
        return E, X, Y, t
    
def makePlot():
    ax.set_xlim(-axisLength, axisLength)
    ax.set_ylim(-axisLength, axisLength)
    ax.set_aspect('equal', adjustable='box')
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        if log:
            c = ax.pcolormesh(Y, X, fun_val[:, :, 0],
                        norm=SymLogNorm(linthresh=0 + fun_val.max()/100, linscale=0.1, vmin=fun_val.min(), vmax=fun_val.max()),
                        cmap='twilight', shading='auto')
            cbar = plt.colorbar(c, label=f"{function[0:-2].capitalize()} Field Value", format="%.2e")
            
            # We set the ticks manually because the SymLogNorm class doesn't seem to have a way to set the ticks automatically
            order_of_magnitude = int(0 - np.log10(fun_val.max())) + 1
            ticks = [fun_val.min()] + [-10**i for i in range(-order_of_magnitude, -order_of_magnitude - 3, -1)] + [0] + [10**i for i in range(-order_of_magnitude, -order_of_magnitude - 3, -1)] + [fun_val.max()]
            cbar.set_ticks(ticks)
        else:
            c = ax.pcolormesh(Y, X, fun_val[:, :, 0], cmap='twilight', shading='auto', vmin=fun_val.min(), vmax=fun_val.max())
            plt.colorbar(c, label=f"{function[0:-2].capitalize()} Field Value")
    plt.grid(True)
    if function == "magneticXZ" or function == "electricXZ":
        plt.xlabel('X [m]')
        plt.ylabel('Z [m]')
        if function == "magneticXZ":
            plt.title('Magnetic field function at t=0')
        elif function == "electricXZ":
            plt.title('Electric field function at t=0')
    elif function == "electricXY" or function == "magneticXY":
        plt.xlabel('X [m]')
        plt.ylabel('Y [m]')
        if function == "magneticXY":
            plt.title('Magnetic field function at t=0')
        elif function == "electricXY":
            plt.title('Electric field function at t=0')

    if mp4:
        try:
            current_directory = os.getcwd() 
            final_directory = os.path.join(current_directory, r'frames')
            if not os.path.exists(final_directory):
                os.makedirs(final_directory)
        except OSError:
            print("Nie udało się stworzyć folderu")

        files = glob.glob('frames/*.png')  # Delete old frames
        for f in files:
            os.remove(f)

        plt.savefig('frames/frame0.png')

        for i in range(1, min(len(t), time*fps)):
            print("Renderowanie klatek", i, 'z', min(t.size, time*fps) - 1)
            window.refresh()
            c.set_array(fun_val[:, :, i].flatten())  # Update the color values
            if function == "magneticXZ" or function == "magneticXY":
                plt.title(f'Magnetic field function at t={t[i]:.2f}')
            elif function == "electricXZ" or function == "electricXY":
                plt.title(f'Electric field function at t={t[i]:.2f}')
            plt.savefig(f'frames/frame{i}.png')
        
        plt.close()

        images = []
        for i in range(0, min(len(t), time*fps)):
            images.append(imageio.imread(f'frames/frame{i}.png'))
        print("Tworzenie pliku mp4...")
        window.refresh()
        imageio.mimsave(f'{function}.mp4', images, fps=fps)
        print("Proces zakończony sukcesem, utworzono animację wideo MP4")
    
    else:
        global windowClosed
        fig.canvas.mpl_connect('close_event', on_close)
        for j in range(int(time/(2*np.pi/omega) + 1)):
            for i in range(1, len(t)):
                c.set_array(fun_val[:, :, i].flatten())  # Update the color values
                if function == "magneticXZ" or function == "magneticXY":
                    plt.title(f'Magnetic field function at t={t[i] + j * (2*np.pi)/omega:.2f}')
                elif function == "electricXZ" or function == "electricXY":
                    plt.title(f'Electric field function at t={t[i] + j * (2*np.pi)/omega:.2f}')
                if t[i] + j * (2*np.pi)/omega >= time or windowClosed:
                    break
                plt.pause(0.01)  # Add a short pause for visualization
            if t[i] + j * (2*np.pi)/omega >= time or windowClosed:
                plt.close()
                break
        plt.show()
        windowClosed = False

def on_close(event):
    global windowClosed
    windowClosed = True

if __name__ == '__main__':
    window = runGUI()
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            window.close()
            exit()
        if checkValues(values):
            current, radius, omega, time, fps, function, mp4, axisLength, log = checkValues(values)
            m0 = current*np.pi*radius**2

            fun_val, X, Y, t = calculateFieldFunction()

            fig = plt.figure(figsize=(8, 8), dpi=100)
            ax = fig.add_subplot(111)

            makePlot()