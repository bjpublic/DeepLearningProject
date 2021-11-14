import numpy as np
import pyqtgraph as pg
import pyaudio
from PyQt5 import QtCore, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import librosa
import torch


SAMPLING_RATE = 22050
CHUNK_SIZE = 22050
form_class = uic.loadUiType("22.ui")[0]


def feature_engineering_mel_spectrum(signal, sampling_rate, n_mels):
    cur_frame_temp = signal
    mel_spectrum_temp = librosa.feature.melspectrogram(
        y=cur_frame_temp,
        sr=sampling_rate,
        n_mels=n_mels,
        n_fft=2048,
        hop_length=512,
    )
    mel_spectrum_temp = librosa.core.power_to_db(mel_spectrum_temp)
    feature_vector = mel_spectrum_temp
    feature_vector = feature_vector[np.newaxis, :,:, np.newaxis]
    return feature_vector

class MicrophoneRecorder():
    def __init__(self, signal):
        self.signal = signal
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLING_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )

    def read(self):
        data = self.stream.read(CHUNK_SIZE, False)
        y = np.fromstring(data, 'float32')
        self.signal.emit(y)


    def close(self):
        print('멈춤')
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


class MyWindow(QMainWindow, form_class):
    read_collected = QtCore.pyqtSignal(np.ndarray)
    def __init__(self, model):
        super(MyWindow, self).__init__()
        self.setupUi(self)
        self.read_collected.connect(self.update)

        self.model = model

        # Bargraph
        pg.setConfigOptions(background='w', foreground='k')

        # hbox = QHBoxLayout()
        self.pw1 = pg.PlotWidget(title="BarGraph")
        self.pw1.showGrid(x=True, y=True)

        self.graph_box.addWidget(self.pw1)
        # self.setLayout(hbox)
        self.pw1.setGeometry(4, 1, 10, 5)  # x, y, width, height

        ticks = [list(zip(range(2), ('Environmental sound', 'Scream sound')))]
        xax = self.pw1.getAxis('bottom')
        xax.setTicks(ticks)
        self.show()


    def update(self, chunk):
        x = np.arange(2)

        feature_vector = feature_engineering_mel_spectrum(chunk, SAMPLING_RATE, 64)
        feature_vector = torch.tensor(feature_vector).float()
        feature_vector = feature_vector.squeeze(3).unsqueeze(1)
        y_softmax = float(
            torch.sigmoid(self.model(feature_vector)).detach().numpy()
        )

        if y_softmax > 0.5:
            pixmap = QPixmap("img/scream.png")
            self.label_5.setPixmap(QPixmap(pixmap))
        else:
            pixmap = QPixmap("img/normal.png")
            self.label_5.setPixmap(QPixmap(pixmap))

        self.pw1.clear()
        barchart = pg.BarGraphItem(
            x=x, height=[1 - y_softmax, y_softmax], width=1, brush=(159, 191, 229)
        )
        self.pw1.addItem(barchart)