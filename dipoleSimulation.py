import numpy as np 
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from matplotlib.ticker import MaxNLocator
import imageio.v2 as imageio
import os
import PySimpleGUI as sg
import glob
import warnings

# Define constants
c = 299792458 # Speed of light in m/s
u0 = 4*np.pi*1e-7 # Permeability of free space in H/m

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
            [sg.Text('Wybór funkcji')],
            [sg.Text('Stworzyć plik mp4?')]]
    
    col2 = [[sg.InputText('1', key='current')],
            [sg.InputText('0.01', key='radius')],
            [sg.InputText('1', key='omega')],
            [sg.InputText('5', key='time')],
            [sg.InputText('1', key='axisLength')],
            [sg.Radio('30 FPS', 'fps', default=True, key='fps30'), sg.Radio('60 FPS', 'fps', key='fps60')],
            [sg.Radio('XY', 'plane', default=True, key='xy'),  sg.Radio('YZ', 'plane', key='yz')],
            [sg.OptionMenu(['Pole magnetyczne', 'Pole elektryczne'], 'Pole magnetyczne', key='function')],
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
        axisLength = float(values['axisLength'])
        fps = 30 if values['fps30'] else 60
        plane = 'XY' if values['xy'] else 'YZ'
        function = 'magnetic' if values['function'] == 'Pole magnetyczne' else 'electric'
        mp4 = values['mp4']
        
        if current < 0 or radius < 0 or omega < 0 or time < 0 or axisLength < 0:
            print('Wartości muszą być dodatnie!')
            return False

        return current, radius, omega, time, axisLength, fps, plane, function, mp4
    except ValueError:
        print('Wartości muszą być liczbami!')
        return False
    
def calculateFieldFunction():
    t = np.arange(0, (2 * np.pi)/omega, 1/fps)
    r = np.linspace(radius + 0.1, axisLength * np.sqrt(2), 100 * int(np.sqrt(axisLength)))
    if plane == "XY":
        theta = np.full(int(fps*time), np.pi/2)
    elif plane == "YZ":
        theta = np.linspace(0, 2*np.pi, 100)

    R, Theta, T = np.meshgrid(r, theta, t, indexing='ij')
    Thetap, Rp = np.meshgrid(theta, r)
    Y = Rp * np.sin(Thetap)
    Z = Rp * np.cos(Thetap)

    if function == "magnetic":
        B = (-1) * ((u0 * m0 * omega ** 2)/(4 * np.pi * c ** 2)) * (np.sin(Theta)/R) * np.cos(omega * (T-R/c))
        return B, Z, Y, t
    elif function == "electric":
        E = ((u0 * m0 * omega ** 2)/(4 * np.pi * c)) * (np.sin(Theta)/R) * np.cos(omega * (T-R/c))
        return E, Z, Y, t
    
def makePlot():
    ax.set_xlim(-axisLength, axisLength)
    ax.set_ylim(-axisLength, axisLength)
    ax.set_aspect('equal', adjustable='box')
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        if plane == "XY":
            c = ax.pcolormesh(Y[:, :, 0], Y[:, :, 0], fun_val[:, :, 0], cmap='hot')
        elif plane == "YZ":
            c = ax.pcolormesh(Y, Z, fun_val[:, :, 0], cmap='afmhot')
    plt.grid(True)
    plt.colorbar(c, label=f"{function.capitalize()} Field Value")
    plt.title('Function Z at t=0')

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
            print("Renderowanie klatek", i + 1, 'z', min(t.size, time*fps))
            window.refresh()
            c.set_array(fun_val[:, :, i].flatten())  # Update the color values
            plt.title(f'Function Z at t={t[i]:.2f}')
            plt.savefig(f'frames/frame{i}.png')

        images = []
        for i in range(0, min(len(t), time*fps)):
            images.append(imageio.imread(f'frames/frame{i}.png'))
        print("Tworzenie pliku mp4...")
        window.refresh()
        imageio.mimsave(f'{function}.mp4', images, fps=fps)
        print("Proces zakończony sukcesem, utworzono animację wideo MP4")
    
    else:
        for j in range(int(time/(2*np.pi/omega) + 1)):
            for i in range(1, len(t)):
                c.set_array(fun_val[:, :, i].flatten())  # Update the color values
                plt.title(f'Function Z at t={t[i] + j * (2*np.pi)/omega:.2f}')
                if t[i] + j * (2*np.pi)/omega >= time:
                    break
                plt.pause(0.01)  # Add a short pause for visualization
            if t[i] + j * (2*np.pi)/omega >= time:
                break
        plt.show()

if __name__ == '__main__':
    window = runGUI()
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            window.close()
            break
        if checkValues(values):
            current, radius, omega, time, axisLength, fps, plane, function, mp4 = checkValues(values)
            m0 = current*np.pi*radius**2

            fun_val, Z, Y, t = calculateFieldFunction()

            fig = plt.figure(figsize=(8, 8), dpi=100)
            ax = fig.add_subplot(111)

            makePlot()