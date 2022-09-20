import Spotify
import requests
import time
    
    ##Add get users playlists

#'41b2b6de6f4cb2cff560a2b1adf5d5278f3ead41'
#'d96af876-ae4d-4ec0-a06c-36ac6f961754_amzn_1'

#h.transfer_playback('41b2b6de6f4cb2cff560a2b1adf5d5278f3ead41')


from PyQt5 import uic, QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsScene, QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QObject, QThread, pyqtSignal

import sys

class UpdateTimer(QObject):

    oneSecond = pyqtSignal() #used for slider update
    tenSecond = pyqtSignal() #used for updating entire scene

    

    def run(self):
        count = 0
        while True:
            count += 1
            time.sleep(1)
            self.oneSecond.emit()
            if count >= 5:
                self.tenSecond.emit()
                count=0

    def stop(self):
        self._isRunning = False
    

class Ui(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(Ui, self).__init__()

        uic.loadUi('C:\\Users\\anuhg\\Documents\\summer_projects\\2022\\Application\\venv\\Lib\\site-packages\\qt5_applications\\Qt\\bin\\GUI.ui', self)
        
        self.h = Spotify.Spotify_API()

        self.h.get_Authorization()

        self.h.get_AccessToken()
        
        self.updateSong()
        self.refresh()



        self.SongPicture = self.findChild(QtWidgets.QGraphicsView, 'SongPicture')
        
        self.SongSlider = self.findChild(QtWidgets.QSlider, 'SongSlider')


        self.SongName = self.findChild(QtWidgets.QLabel, 'SongName')
        
        self.ControlGroup = self.findChild(QtWidgets.QGroupBox, 'MediaControllers')
        
        self.PrevB = self.findChild(QtWidgets.QPushButton, 'PrevB')
        self.PauseB = self.findChild(QtWidgets.QPushButton, 'PauseB')
        self.PlayB = self.findChild(QtWidgets.QPushButton, 'PlayB')
        self.NextB = self.findChild(QtWidgets.QPushButton, 'NextB')

        self.ExitB = self.findChild(QtWidgets.QPushButton, 'ExitB')

        self.RefreshB = self.findChild(QtWidgets.QPushButton, 'RefreshB')

        self.RepeatB = self.findChild(QtWidgets.QPushButton, 'RepeatB')
        self.AddToPlaylistB = self.findChild(QtWidgets.QPushButton, 'Playlists')

        self.Playlists = self.findChild(QtWidgets.QComboBox, 'Playlists')
        self.DeviceSlider = self.findChild(QtWidgets.QComboBox, 'DeviceSlider')

        self.VolumeW = self.findChild(QtWidgets.QScrollBar, 'VolumeW')

        #Logic

        #threads
        self.thread = QThread()
        self.timer = UpdateTimer()
        self.timer.moveToThread(self.thread)

        self.thread.started.connect(self.timer.run)
        self.timer.oneSecond.connect(self.updateSongSlider)
        self.timer.tenSecond.connect(self.updateSong)
        


        self.NextB.clicked.connect(self.NextSong)
        self.PauseB.clicked.connect(self.PauseSong)
        self.PlayB.clicked.connect(self.PlaySong)
        self.PrevB.clicked.connect(self.PrevSong)
        self.RepeatB.clicked.connect(self.RepeatSong)
        self.RefreshB.clicked.connect(self.refresh)

        self.VolumeW.sliderReleased.connect(self.VolumeChange)

        self.SongSlider.sliderReleased.connect(self.SeekPos)

        self.DeviceSlider.currentIndexChanged.connect(self.ChangeDevice)

        self.thread.start()
        self.ExitB.clicked.connect(lambda: self.timer.stop())
        self.ExitB.clicked.connect(self.stop_thread)
        
        

        self.show()

    def stop_thread(self):
        self.timer.stop()
        self.thread.quit()
        self.thread.wait()

    def updateSong(self):#updates all song attribute things like pic and name
        self.h.get_current_track()

        self.SongName.setText(self.h.Current_Track)

        scene = QGraphicsScene()
        image = QImage()
        image.loadFromData(requests.get(self.h.Current_Track_Image_url).content)
        image_Label = QLabel()
        image_Label.setPixmap(QPixmap(image))
        scene.addWidget(image_Label)
        self.SongPicture.setScene(scene)
        self.SongPicture.show()

        self.SongSlider.setRange(0,self.h.Current_Track_duration)
        self.SongSlider.setValue(self.h.Current_Track_position)


    def refresh(self):
        self.h.get_Device_Names()

        self.DeviceSlider.clear()
    
        current = self.h.current_Device

        for Device in self.h.Device_IDs:
            for keys, ids in Device.items():
                self.DeviceSlider.addItem(keys)

        try:
            self.DeviceSlider.setCurrentIndex(self.h.Device_IDs.index(current))
        except:
            pass

    def updateSongSlider(self):
        val = self.SongSlider.value()+1000
        self.SongSlider.setValue(val)

        if val >= self.h.Current_Track_duration:
            self.updateSong()

    def SeekPos(self):
        self.h.Seek_position(self.SongSlider.value())


    def PrevSong(self):
        self.h.prev_playback()
        self.updateSong()

    def PauseSong(self):
        self.h.pause_playback()

    def PlaySong(self):
        self.h.play_playback()

    def NextSong(self):
        self.h.skip_playback()
        self.updateSong()

    def RepeatSong(self):
        self.h.repeat_song()
        self.updateSong()

    def AddToPlaylist(self):
        #self.h.add_to_playlist()
        return None

    def VolumeChange(self):#broken try again later
        print(self.VolumeW.value())
        self.h.Set_Volume(self.VolumeW.value())

    def ChangeDevice(self, index):

        for key, ids in self.h.Device_IDs[index].items():
            self.h.transfer_playback(ids)



app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()

##PROBS ADD SCROLL FOR LONG SONG NAMES