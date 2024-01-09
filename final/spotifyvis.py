"""
nschierm CS439 Final Project
Spotify Data Visualizer

A user will be able to give their own spotify data and see different
ways to visualize their taste.

Started 11/5/2023 10:40 PM

"""

import os
import argparse
import pandas as pd
import sys
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import math
import matplotlib as mpl
import numpy as np
import mplcursors
from matplotlib.lines import Line2D
from pandas.plotting import parallel_coordinates
import datetime as dt


# Subclass QMainWindow to customize application's main window
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QFileDialog, QWidget, QGridLayout, QComboBox, QTabWidget, QSpinBox, QLabel, QVBoxLayout, QHBoxLayout, QDialog, QCheckBox
from PyQt6.QtCore import pyqtSlot

def validate_args(args):

    assert os.path.exists(args.filename), "Incorrect filename!"

class Main(QMainWindow):
    def __init__(self):
        super().__init__()

        #self.setGeometry(2450, -70, 1200, 600) # Might want to change this while presenting so it shows up correctly?
        self.setGeometry(100, 100, 1250, 600)
        self.setWindowTitle("Spotify Data Visualizer -- nschierm")
        #data_frame = pd.read_csv(args.filename)

        df = pd.read_csv(args.filename, encoding='ISO-8859-1') # Use a certain type of encoding bc some vals were messed up

        print(df)
        # Convert 'streams' column to numeric if needed
        df['streams'] = pd.to_numeric(df['streams'], errors='coerce')
        df['released_year'] = pd.to_numeric(df['released_year'], errors='coerce')
        self.df = df # So that I can reference the df in functions


        """
        Bar Chart
        """
        bar_widget = QWidget(self)
        bar_grid_layout = QGridLayout()
        
        self.bar_figure = Figure()
        bar_canvas = FigureCanvas(self.bar_figure)
        bar_grid_layout.addWidget(bar_canvas, 0, 0, 3, 4)
        self.ax = self.bar_figure.add_subplot(111)
        aggregated_df = df.groupby('released_year')['streams'].sum().reset_index()
        bars = self.ax.bar(aggregated_df['released_year'], aggregated_df['streams'])
        self.cursor = mplcursors.cursor(bars, hover=True)
        self.cursor.connect("add", lambda sel: sel.annotation.set_text(f"{sel.target[1]:,.0f} streams"))

        self.years_box = QSpinBox(self)
        self.years_box.setRange(aggregated_df['released_year'].min(), aggregated_df['released_year'].max()) # This is nice, has a built-in min/max detection
        self.years_box.setAlignment(Qt.AlignmentFlag.AlignBottom)
        bar_grid_layout.addWidget(self.years_box, 3, 1, 1, 1)
        self.years_box.valueChanged.connect(self.update_bar_chart)
        self.min_text = QLabel(self)
        self.min_text.setText("Minimum Year:")
        #self.min_text.setAlignment(Qt.AlignmentFlag.AlignRight)
        bar_grid_layout.addWidget(self.min_text, 4, 1, 1, 1)
        

        

        self.years_box_2 = QSpinBox()
        self.years_box_2.setRange(aggregated_df['released_year'].min()+1, aggregated_df['released_year'].max())
        self.years_box_2.setValue(aggregated_df['released_year'].max())
        self.years_box_2.setAlignment(Qt.AlignmentFlag.AlignBottom)
        bar_grid_layout.addWidget(self.years_box_2, 3, 2, 1, 1)
        self.years_box_2.valueChanged.connect(self.update_bar_chart)
        self.max_text = QLabel(self)
        self.max_text.setText("Maximum Year:")
        bar_grid_layout.addWidget(self.max_text, 4, 2, 1, 1)

        
        bar_widget.setLayout(bar_grid_layout)

        """
        Scatter Plot
        
        """
        scatter_widget = QWidget(self)
        scatter_grid = QGridLayout()

        self.scatter_figure = Figure()
        self.scatter_canvas = FigureCanvas(self.scatter_figure)
        scatter_grid.addWidget(self.scatter_canvas, 0, 0, 6, 6)
        self.scatter_ax = self.scatter_figure.add_subplot(111)

        df['random_x'] = np.random.rand(len(df))
        df['key'] = df['key'].fillna('Z') # Maybe change this to say not specified
        #df['key'] = df['key'].dropna
        keys = df['key']

        cmap = plt.get_cmap('Paired', len(np.unique(keys)))
        

        # Assign a unique color to each key
        self.key_colors = [cmap(np.where(np.unique(keys) == key)[0][0]) for key in keys]

        # Determine conditions for red, green, and gray
        self.red_condition = (self.df['in_apple_charts'] < self.df['in_spotify_charts']) & (self.df['in_apple_charts'] != 0) # The one that has a lower number is better since it's a ranking
        self.green_condition = (self.df['in_apple_charts'] > self.df['in_spotify_charts']) & (self.df['in_spotify_charts'] != 0)

        self.scatter_ax.scatter(df['valence_%'], df['energy_%'], c=self.key_colors)
        self.appl_spot_button = QPushButton("Compare Spotify and Apple Data", self)
        self.appl_spot_button.clicked.connect(self.toggle_button_text)
        scatter_grid.addWidget(self.appl_spot_button, 6, 5, 1, 1)

        x = QLabel(self)
        x.setText("X:")
        x.setAlignment(Qt.AlignmentFlag.AlignRight)
        x.setStyleSheet("font-size: 17px")
        y = QLabel(self)
        y.setText("Y:")
        y.setStyleSheet("font-size: 17px")
        y.setAlignment(Qt.AlignmentFlag.AlignRight)
        num_pts = QLabel(self)
        num_pts.setText("Number of Points:")
        num_pts.setStyleSheet("font-size: 16px")
        num_pts.setAlignment(Qt.AlignmentFlag.AlignRight)
        scatter_grid.addWidget(x, 6, 0, 1, 1)
        scatter_grid.addWidget(y, 6, 2, 1, 1)
        scatter_grid.addWidget(num_pts, 5, 4, 1, 1)



        self.x_axis = QComboBox(self)
        self.y_axis = QComboBox(self)
        self.qcombo_options = ['released_year', 'in_spotify_playlists', 'in_spotify_charts', 'streams', 'bpm', 'danceability_%', 
                          'valence_%', 'energy_%', 'acousticness_%', 'instrumentalness_%', 'liveness_%', 'speechiness_%']
        for row_name in self.qcombo_options:
            self.x_axis.addItem(row_name)
            self.y_axis.addItem(row_name)
        # Set default values to not just be the same (would result in corr=1 just straight line)
        self.x_axis.setCurrentText('valence_%')
        self.y_axis.setCurrentText('energy_%')
        
        scatter_grid.addWidget(self.x_axis, 6, 1, 1, 1)
        scatter_grid.addWidget(self.y_axis, 6, 3, 1, 1)
        self.x_axis.currentTextChanged.connect(self.update_scatter)
        self.y_axis.currentTextChanged.connect(self.update_scatter)

        self.num_pts = QSpinBox(self)
        self.num_pts.setRange(10, len(df.index))
        self.num_pts.setValue(len(df.index))
        scatter_grid.addWidget(self.num_pts, 5, 5, 1, 1)
        self.num_pts.valueChanged.connect(self.update_scatter)

        self.colorblind_box = QCheckBox("Colorblind Mode", self)
        scatter_grid.addWidget(self.colorblind_box, 5, 1, 1, 1)
        self.colorblind_box.clicked.connect(self.colorblind)
        self.colorblind_box.setVisible(False) # Initialize to not visible since I only want this for the spotify apple comparison
          

        

        self.scatter_ax.set_xlabel(self.x_axis.currentText())
        self.scatter_ax.set_ylabel(self.y_axis.currentText())
        self.add_tab2_legend()
        mplcursors.cursor(self.scatter_ax, hover=True).connect("add", lambda sel: sel.annotation.set_text(f"Song Title: {self.df['track_name'][sel.index]}\nArtist Name: {self.df['artist(s)_name'][sel.index]}"))

        
        
        scatter_widget.setLayout(scatter_grid)

        """
        User's Spotify Data
        """
        user_widget = QWidget(self)
        self.user_grid_layout = QGridLayout()
        user_label = QLabel(self)
        user_label.setText("Select the .csv with your 1-year spotify history:")
        self.user_grid_layout.addWidget(user_label, 0, 1, 1, 1)
        
        self.fname = None
        btn = QPushButton(self)
        btn.setText("Open file dialog")
        btn.clicked.connect(self.open_dialog)
        self.user_grid_layout.addWidget(btn, 1, 1, 2, 2)

        if self.fname is not None:
            print(self.fname)

        user_widget.setLayout(self.user_grid_layout)

        """
        Similarity
        """

        similarity_widget = QWidget(self)
        similarity_grid = QGridLayout()

        self.parallel_fig = Figure()
        parallel_canvas = FigureCanvas(self.parallel_fig)
        self.par_ax = self.parallel_fig.add_subplot(111)
        
        #parallel_coordinates_df = self.df[['key', 'danceability_%', 'valence_%', 'energy_%', 'acousticness_%', 'instrumentalness_%', 'liveness_%', 'speechiness_%', 'track_name']].copy()
        parallel_coordinates_df = self.df[['key', 'danceability_%', 'valence_%', 'energy_%', 'acousticness_%', 'instrumentalness_%', 'liveness_%', 'speechiness_%']].copy()
        

        similarity_widget = ParallelCoordinatesWidget(parallel_coordinates_df, self) # need to use another class to be able to embed it into the overall project, or else I would've had to make it manually
        similarity_grid.addWidget(similarity_widget, 0, 0, 2, 4)

        # Update the parallel coordinates plot when needed
        similarity_widget.update_parallel_coordinates(parallel_coordinates_df.head(50), target_column='key')

        #TODO: Inject Taylor Swift / Harry Styles Button?
        #TODO: Would be cool to add the rectangle select here

        #similarity_widget.setLayout(similarity_grid)


        """
        Put all the programs into their 'tabs'
        """

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        tabwidget = QTabWidget()
        tabwidget.addTab(bar_widget, "Song History")
        tabwidget.addTab(scatter_widget, "Scatter Plot")
        tabwidget.addTab(user_widget, "User Data")
        tabwidget.addTab(similarity_widget, "Similarity")
        grid_layout.addWidget(tabwidget, 0, 0)

        # Initialize the Bar Chart by updating it once
        self.update_bar_chart()
    
    @pyqtSlot()
    def open_dialog(self):
        self.fname = QFileDialog.getOpenFileName(
            self,
            "Open File",
            #"${HOME}", Change this back for final upload
            "D:/Users/Nick/Downloads/2023/Purdue/Fall 2023/CS439/my_spotify_data/MyData/",
            "Comma Separated Value (*.csv)",
        )
        print(self.fname[0])

        try:
            self.user_df = pd.read_csv(self.fname[0])
            #print(self.user_df)
            self.preprocess_user_data() #Thinking of adding this later on if I want to put it to github, for now I think I just need to use manually preprocessed data
            
            self.init_user_barchart()

        except FileNotFoundError:
            return  

    def update_bar_chart(self):
        if self.cursor:
            self.cursor.remove()
            
    
        minyearval = self.years_box.value()
        maxyearval = self.years_box_2.value()
        if (maxyearval <= minyearval):
            self.years_box_2.setValue(minyearval + 1)
            return

        filtered_years = self.df[(self.df['released_year'] >= minyearval) & (self.df['released_year'] <= maxyearval)]

        self.ax.clear()

        aggregated_df = filtered_years.groupby('released_year')['streams'].sum().reset_index()
        most_popular_artists = filtered_years.loc[filtered_years.groupby('released_year')['streams'].idxmax()][['released_year', 'artist(s)_name']]
        bars = self.ax.bar(most_popular_artists['released_year'], filtered_years.groupby('released_year')['streams'].sum())
        self.ax.set_xlabel("Year")

        # Create a new cursor with hover=True and connect it to display the number of streams, artist, and year on hover
        self.cursor = mplcursors.cursor(bars, hover=True)
        self.cursor.connect("add", lambda sel: sel.annotation.set_text(f"Year: {round(sel.target[0])}\nStreams: {sel.target[1]:,.0f}\nMost Popular Artist: {most_popular_artists[most_popular_artists['released_year'] == round(sel.target[0])]['artist(s)_name'].values[0]}"))

        self.ax.set_yticks(np.linspace(0, aggregated_df['streams'].max(), num=5))
        self.ax.get_yaxis().get_major_formatter().set_scientific(False)
        self.ax.set_ylabel("Streams")
        self.bar_figure.canvas.draw()

    def colorblind(self):
        # Assign colors based on conditions
        if self.colorblind_box.isChecked():
            self.spot_appl_color_list = ['darkblue', 'orange']
        else:
            self.spot_appl_color_list = ['green', 'red']
        self.spot_appl_colors = np.where(self.red_condition, self.spot_appl_color_list[1], np.where(self.green_condition, self.spot_appl_color_list[0], 'gray'))
        self.appl_spot_button.setText("Compare Spotify and Apple Data") # Change text then update so that the view doesn't change
        self.toggle_button_text()

    def toggle_button_text(self):
        current_text = self.appl_spot_button.text()
        self.scatter_ax.clear()
        self.x_axis.clear()
        self.y_axis.clear()
        

        if current_text == "Compare Spotify and Apple Data":
            self.appl_spot_button.setText("Look at just Spotify Data")
            self.colorblind_box.setVisible(True)

            # Assign colors based on conditions
            if self.colorblind_box.isChecked():
                self.spot_appl_color_list = ['darkblue', 'orange']
            else:
                self.spot_appl_color_list = ['green', 'red']
            self.spot_appl_colors = np.where(self.red_condition, self.spot_appl_color_list[1], np.where(self.green_condition, self.spot_appl_color_list[0], 'gray'))

            
            spotify_apple_list = ['in_spotify_playlists', 'in_spotify_charts', 'in_apple_playlists', 'in_apple_charts']
            for my_item in spotify_apple_list:
                self.x_axis.addItem(my_item)
                self.y_axis.addItem(my_item)
            # Set default values to not just be the same (would result in corr=1 just straight line)
            self.x_axis.setCurrentText('in_spotify_playlists')
            self.y_axis.setCurrentText('in_apple_playlists')
            
            self.scatter_ax.clear() # need to have this here again because adding the names above updates the text...

            self.scatter_ax.scatter(self.df['in_apple_playlists'], self.df['in_spotify_playlists'], c=self.spot_appl_colors)
            self.scatter_ax.set_xlabel("in apple playlists")
            self.scatter_ax.set_ylabel("in spotify playlists")
            
            self.update_scatter()
            
            self.scatter_ax.legend(handles = [
                Line2D([0], [0], label='Ranked \nhigher in \nApple \nCharts', marker = 'o', markersize = 10, linestyle = '', color=self.spot_appl_color_list[1]),
                Line2D([0], [0], label='Ranked \nhigher in \nSpotify \nCharts', marker = 'o', markersize = 10, linestyle = '', color=self.spot_appl_color_list[0]),
                Line2D([0], [0], label='Not\nranked in\neither\nApple or\nSpotify\nCharts', marker = 'o', markersize = 10, linestyle = '', color='grey')],
                title = "Spotify vs\nApple", bbox_to_anchor = (1, 1), loc = "upper left",)


            #self.scatter_ax.set_xticks(np.linspace(0, self.df['in_apple_charts'].max()), num=5)
            #self.scatter_ax.set_yticks(np.linspace(0, self.df['in_spotify_charts'].max()), num=5)
                 
        elif current_text == "Look at just Spotify Data":
            self.appl_spot_button.setText("Compare Spotify and Apple Data")
            self.colorblind_box.setVisible(False)
            for row_name in self.qcombo_options:
                self.x_axis.addItem(row_name)
                self.y_axis.addItem(row_name)
            self.update_scatter()
            self.add_tab2_legend()

            
        
        self.scatter_figure.canvas.draw()

    def update_scatter(self):

        if(self.x_axis.currentText() == '' or self.y_axis.currentText() == ''): #Added both x and y because when changing the QSpinBox options it counted as changing text lol
            return # since switching between the apple/spotify and just spotfiy view changes the text, this function would run and crash, so this prevents that
        
        self.scatter_figure.clear()
        self.scatter_ax = self.scatter_figure.add_subplot(111)
        
        
        if self.appl_spot_button.text() == "Look at just Spotify Data":
            colormap = self.spot_appl_colors
            self.scatter_ax.scatter(self.df[self.x_axis.currentText()].head(self.num_pts.value()), self.df[self.y_axis.currentText()].head(self.num_pts.value()), c=colormap[:self.num_pts.value()])
            #mplcursors.cursor(self.scatter_ax, hover=True).connect("add", lambda sel: sel.annotation.set_text(f"Song Title: {self.df['track_name'][sel.index]}\nArtist Name: {self.df['artist(s)_name'][sel.index]}\n"
            #                                                                                                  f"Spotify Ranking: {self.df['in_spotify_charts'][sel.index]}\nApple Ranking: {self.df['in_apple_charts'][sel.index]}"))
            mplcursors.cursor(self.scatter_ax, hover=True).connect("add", lambda sel: sel.annotation.set_text(
            f"Song Title: {self.df['track_name'][sel.index]}\n"
            f"Artist Name: {self.df['artist(s)_name'][sel.index]}\n"
            f"Spotify Ranking: {'Not ranked' if self.df['in_spotify_charts'][sel.index] == self.df['in_spotify_charts'].min() else self.df['in_spotify_charts'][sel.index]}\n"
            f"Apple Ranking: {'Not ranked' if self.df['in_apple_charts'][sel.index] == self.df['in_apple_charts'].min() else self.df['in_apple_charts'][sel.index]}"
            ))
            self.scatter_ax.legend(handles = [
                Line2D([0], [0], label='Ranked \nhigher in \nApple \nCharts', marker = 'o', markersize = 10, linestyle = '', color=self.spot_appl_color_list[1]),
                Line2D([0], [0], label='Ranked \nhigher in \nSpotify \nCharts', marker = 'o', markersize = 10, linestyle = '', color=self.spot_appl_color_list[0]),
                Line2D([0], [0], label='Not\nranked in\neither\nApple or\nSpotify\nCharts', marker = 'o', markersize = 10, linestyle = '', color='grey')],
                title = "Spotify vs\nApple", bbox_to_anchor = (1, 1), loc = "upper left",)

        else:
            colormap = self.key_colors
            self.scatter_ax.scatter(self.df[self.x_axis.currentText()].head(self.num_pts.value()), self.df[self.y_axis.currentText()].head(self.num_pts.value()), c=colormap[:self.num_pts.value()])
            mplcursors.cursor(self.scatter_ax, hover=True).connect("add", lambda sel: sel.annotation.set_text(f"Song Title: {self.df['track_name'][sel.index]}\nArtist Name: {self.df['artist(s)_name'][sel.index]}"))
            
            self.add_tab2_legend()

        #mplcursors.cursor(self.scatter_ax, hover=True).connect("add", lambda sel: sel.annotation.set_text(f"Song Title: {self.df['track_name'][sel.index]}\nArtist Name: {self.df['artist(s)_name'][sel.index]}"))


        self.scatter_ax.set_xlabel(self.x_axis.currentText())
        self.scatter_ax.set_ylabel(self.y_axis.currentText())
        self.scatter_canvas.draw()
        
        #self.scatter_figure.draw_without_rendering()

    def add_tab2_legend(self):

        paired=mpl.colormaps['Paired']
        self.scatter_ax.legend(handles = [
            Line2D([0], [0], label='A', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[0]),
            Line2D([0], [0], label='A#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[1]),
            Line2D([0], [0], label='B', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[2]),
            Line2D([0], [0], label='C#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[3]),
            Line2D([0], [0], label='D', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[4]),
            Line2D([0], [0], label='D#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[5]),
            Line2D([0], [0], label='E', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[6]),
            Line2D([0], [0], label='F', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[7]),
            Line2D([0], [0], label='F#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[8]),
            Line2D([0], [0], label='G', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[9]),
            Line2D([0], [0], label='G#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[10]),
            Line2D([0], [0], label='No key \nspecified', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[11])
        ], title = "Song key", bbox_to_anchor = (1, 1), loc = "upper left",)
        #mplcursors.cursor(self.scatter_ax, hover=True).connect("add", lambda sel: sel.annotation.set_text(f"Song Title: {self.df['track_name'][sel.index]}\nArtist Name: {self.df['artist(s)_name'][sel.index]}"))

    def preprocess_user_data(self):
        self.user_df = self.user_df.drop(self.user_df.columns[0], axis=1)
        self.user_df[['date', 'time']] = self.user_df['endTime'].str.split(' ', expand=True)
        self.user_df['date'] = pd.to_datetime(self.user_df['date'])
        self.user_df['weekday'] = self.user_df['date'].dt.day_name()
        self.user_df['month'] = self.user_df['date'].dt.month_name()
        self.user_df['minsPlayed'] = self.user_df['msPlayed'] / 60000
        self.user_df['skipped'] = self.user_df['minsPlayed'] < 0.5


        print(self.user_df)
        #assert(False)
        
    def init_user_barchart(self):
        self.mins_listened = []
        # print(self.user_df)
        for i in reversed(range(self.user_grid_layout.count())):
            self.user_grid_layout.itemAt(i).widget().setParent(None)
        self.user_bar_figure = Figure()
        self.user_bar_canvas = FigureCanvas(self.user_bar_figure)
        self.user_grid_layout.addWidget(self.user_bar_canvas, 0, 0, 3, 4)
        self.user_ax = self.user_bar_figure.add_subplot(111)
        self.user_ax.set_xlabel("Days of Week")
        self.user_ax.set_ylabel("Minutes Listened")

        #print(self.user_df[['date','weekday','minsPlayed']])
        #self.days = ['Sun', 'Mon','Tues','Wed','Thurs','Fri','Sat']
        self.days = ['Sunday', 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']

        # Remove any local downloads, this is because spotify can't distinguish between 
        # your local files, so it just lumps them into one 'Unknown ...' which can skew data 
        self.user_df = self.user_df[self.user_df['artistName'] != 'Unknown Artist']
        self.no_skips_df = self.user_df[self.user_df['skipped'] == False].copy() # Does NOT include skipped songs, where skipped songs are <.5 mins played
        mins=self.no_skips_df.groupby('weekday')['minsPlayed'].sum().reindex(self.days)

        grouped_df = self.no_skips_df.groupby(['weekday', 'artistName'])['minsPlayed'].sum()

        # Find the index (artistName) corresponding to the maximum 'minsPlayed' for each 'weekday'
        self.top_artists_grouped = grouped_df.groupby('weekday').idxmax().reindex(self.days)
        #print(self.top_artists_grouped)

        # Update the colors of the bars
        self.update_colors()
        
        #print(top_artists_colors)
        self.user_ax.bar(self.days, mins, color=self.top_artists_colors)

        
        self.data_options = QComboBox(self)
        list = ['Days of Week','Months of Year', 'Most Listened to Artist', 'Most Listened to Track', 'Most Skipped Artist', 'Most Skipped Track']
        self.data_options.addItems(list)

        self.data_options.currentTextChanged.connect(self.update_user_barchart)
        self.user_grid_layout.addWidget(self.data_options, 4, 1, 1, 2)

        self.check = QCheckBox(self)
        self.check.setText('Include Skipped Songs')
        self.user_grid_layout.addWidget(self.check, 4, 0, 1, 1)
        self.check.clicked.connect(self.update_user_barchart)
        
    def update_user_barchart(self):
        self.user_ax.clear()
        #self.user_bar_figure.clear()
        if self.check.isChecked(): # Checked for include skipped songs = use FULL df
            current_df = self.user_df
        if not self.check.isChecked(): # No skipped songs = smaller df
            current_df = self.no_skips_df
        if self.cursor:
            self.cursor.remove()
        
        if hasattr(self, 'cbar'):
            self.cbar.remove()
            delattr(self, 'cbar')  # Remove the attribute to create a new colorbar next time
        
            # Not sure why I have to recreate the entire figure but it removes the .2, .4, ..., 1 labels from both axes
            self.user_bar_figure = Figure()
            self.user_bar_canvas = FigureCanvas(self.user_bar_figure)
            self.user_grid_layout.addWidget(self.user_bar_canvas, 0, 0, 3, 4)
            self.user_ax = self.user_bar_figure.add_subplot(111)
        
        
        #TODO: Might be cool to add a hover event that displays the most listened to song per day / month, and most popular time?
        if self.data_options.currentText() == "Days of Week":
            mins=current_df.groupby('weekday')['minsPlayed'].sum().reindex(self.days)
            self.user_ax.set_xlabel("Days of Week")
            self.user_ax.set_ylabel("Minutes Listened")
            grouped_df = current_df.groupby(['weekday', 'artistName'])['minsPlayed'].sum()
            self.top_artists_grouped = grouped_df.groupby('weekday').idxmax().reindex(self.days)
            self.update_colors()
            self.user_ax.bar(self.days, mins, color=self.top_artists_colors)

            


        elif self.data_options.currentText() == "Months of Year":
            months = [ "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            mins = current_df.groupby('month')['minsPlayed'].sum().reindex(months)
            self.user_ax.set_xlabel("Months of Year")
            self.user_ax.set_ylabel("Minutes Listened")
            grouped_df = current_df.groupby(['month', 'artistName'])['minsPlayed'].sum()
            self.top_artists_grouped = grouped_df.groupby('month').idxmax().reindex(months)
            self.update_colors()
            self.user_ax.bar(months, mins, color=self.top_artists_colors)

            current_df['time'] = pd.to_datetime(current_df['time'])
            current_df['hour'] = current_df['time'].dt.hour

            # Group by 'month' and the extracted 'hour', then get the count for each group
            monthly_hourly_counts = current_df.groupby(['month', 'hour']).size().reset_index(name='count')

            # Display the frequency of the most popular time songs were listened to each month

            for month in monthly_hourly_counts['month'].unique():
                monthly_data = monthly_hourly_counts[monthly_hourly_counts['month'] == month]
                most_popular_hour = monthly_data.loc[monthly_data['count'].idxmax(), 'hour']
                #print(f"Month: {month}, Most Popular Hour: {most_popular_hour}, Frequency: {monthly_data['count'].max()}")
            
            #self.cursor = mplcursors.cursor(self.user_ax, hover=True)
            #self.cursor.connect("add", lambda sel: sel.annotation.set_text(f"{sel.index}"))
        
        elif self.data_options.currentText() == "Most Listened to Artist":
            
            top10 = pd.value_counts(current_df['artistName']).head(10)
            self.update_colors()
            self.user_ax.set_xlabel("Artist Name")
            self.user_ax.set_ylabel("Number of Times Played")
            

            # Find the index of the most played track for each artist
            most_played_track = self.user_df.groupby(['artistName', 'trackName']).size().reset_index(name='count')
            most_played_idx = most_played_track.groupby('artistName')['count'].idxmax()

            # Create a new DataFrame with the most played song for each artist
            most_played_songs = most_played_track.loc[most_played_idx, ['artistName', 'trackName', 'count']]

            self.mins_listened = [current_df[current_df['artistName'] == artist]['minsPlayed'].sum() for artist in top10.index]
          
            self.update_colorbar()

            self.user_ax.bar(top10.index, top10.values, color=self.colorbar_colors)
            self.user_ax.set_xticks(top10.index)
            self.user_ax.set_xticklabels(top10.index, rotation=18, ha='right')

            self.cursor = mplcursors.cursor(self.user_ax, hover=True)
            self.cursor.connect("add", lambda sel: sel.annotation.set_text(f"Most Streamed Song: {most_played_songs[most_played_songs['artistName'] == top10.index[sel.index]].iloc[0]['trackName']}"
                                                                           f"\nMinutes Listened to Artist: {round(current_df[current_df['artistName'] == top10.index[sel.index]]['minsPlayed'].sum(),2)}")) 

        elif self.data_options.currentText() == "Most Listened to Track":

            top10 = pd.value_counts(current_df['trackName']).head(10)
            self.update_colors() # This doesn't do anything and needs to be changed to something meaningful
            self.user_ax.set_xlabel("Track Name")
            self.user_ax.set_ylabel("Number of Times Played")
            
            
            # Find the index of the most played track for each artist
            most_played_track = self.user_df.groupby(['artistName', 'trackName']).size().reset_index(name='count')
            most_played_idx = most_played_track.groupby('trackName')['count'].idxmax()

            # Create a new DataFrame with the most played song for each artist
            most_played_songs = most_played_track.loc[most_played_idx, ['artistName', 'trackName', 'count']]


            self.mins_listened = [current_df[current_df['trackName'] == val]['minsPlayed'].sum() for val in top10.index]
          
            self.update_colorbar()

            self.user_ax.bar(top10.index, top10.values, color=self.colorbar_colors)
            self.user_ax.set_xticks(top10.index)
            self.user_ax.set_xticklabels(top10.index, rotation=18, ha='right')
            
            self.cursor = mplcursors.cursor(self.user_ax, hover=True)
            self.cursor.connect("add", lambda sel: sel.annotation.set_text(f"Song Artist: {most_played_songs[most_played_songs['trackName'] == top10.index[sel.index]].iloc[0]['artistName']}"
                                                                           f"\nMinutes Listened to Song: {round(current_df[current_df['trackName'] == top10.index[sel.index]]['minsPlayed'].sum(),2)}"))
 
        elif self.data_options.currentText() == "Most Skipped Artist":
            
            top_skipped_artists = self.user_df.groupby(['artistName', 'skipped']).size().unstack().fillna(0)[True].sort_values(ascending=False).head(10)
            self.user_ax.set_xlabel("Artist Name")
            self.user_ax.set_ylabel("Number of Times Skipped")

            #self.mins_listened = [self.user_df[self.user_df['artistName'] == artist]['minsPlayed'].sum() for artist in top_skipped_artists.index]
            self.mins_listened = [self.user_df[(self.user_df['artistName'] == artist) & (self.user_df['skipped'] == True)]['minsPlayed'].sum() for artist in top_skipped_artists.index]

            self.update_colorbar()

            self.user_ax.bar(top_skipped_artists.index, top_skipped_artists.values, color = self.colorbar_colors)
            self.user_ax.set_xticks(top_skipped_artists.index)
            self.user_ax.set_xticklabels(top_skipped_artists.index, rotation=14, ha='right')  

            most_played_track = self.user_df[self.user_df['skipped'] == True].groupby(['artistName', 'trackName', 'skipped']).size().reset_index(name='count')
            most_played_idx = most_played_track.groupby('artistName')['count'].idxmax()
            most_skipped_songs = most_played_track.loc[most_played_idx, ['artistName', 'trackName', 'count']]


            self.cursor = mplcursors.cursor(self.user_ax, hover=True)
            #NOTE: DO NOT HOVER OVER 21 SAVAGE'S MOST SKIPPED SONG, OR DROP IT SOMEHOW!
            self.cursor.connect("add", lambda sel: sel.annotation.set_text(f"Most Skipped Song: {most_skipped_songs[most_skipped_songs['artistName'] == top_skipped_artists.index[sel.index]].iloc[0]['trackName']}"
                                                                           f"\nMins Listened to Artist before Skipping: {round(self.mins_listened[sel.index],2)}"))
                                                                           #f"\nMinutes Listened to Artist: {round(self.user_df[self.user_df['artistName'] == top_skipped_artists.index[sel.index] & (self.user_df['skipped'] == True)]['minsPlayed'].sum(),2)}"))

        elif self.data_options.currentText() == "Most Skipped Track":
            top_skipped_tracks = self.user_df.groupby(['trackName', 'skipped']).size().unstack().fillna(0)[True].sort_values(ascending=False).head(10)
            self.user_ax.set_xlabel("Track Name")
            self.user_ax.set_ylabel("Number of Times Skipped")

            self.mins_listened = [self.user_df[(self.user_df['trackName'] == track) & (self.user_df['skipped'] == True)]['minsPlayed'].sum() for track in top_skipped_tracks.index]

            self.update_colorbar()

            self.user_ax.bar(top_skipped_tracks.index, top_skipped_tracks.values, color = self.colorbar_colors)
            self.user_ax.set_xticks(top_skipped_tracks.index)
            self.user_ax.set_xticklabels(top_skipped_tracks.index, rotation=14, ha='right')

            most_played_track = self.user_df[self.user_df['skipped'] == True].groupby(['trackName', 'artistName', 'skipped']).size().reset_index(name='count')
            most_played_idx = most_played_track.groupby('trackName')['count'].idxmax()
            most_skipped_artists = most_played_track.loc[most_played_idx, ['trackName', 'artistName', 'count']]

            self.cursor = mplcursors.cursor(self.user_ax, hover=True)
            self.cursor.connect("add", lambda sel: sel.annotation.set_text(f"Artist of Song: {most_skipped_artists[most_skipped_artists['trackName'] == top_skipped_tracks.index[sel.index]].iloc[0]['artistName']}"
                                                                           f"\nTotal Mins Listened to Song before Skipping: {round(self.mins_listened[sel.index],2)}"))
            

        self.user_bar_figure.canvas.draw()
            

        # print(self.data_options.currentIndex()) this is interesting at least lol

    def update_colors(self):
        # Extract the artist names from the index    
        self.top_artists = self.top_artists_grouped.apply(lambda x: x[1])
        
        #print(top_artists)
        
        # Map the colors to the artist names
        cmap = mpl.colormaps['Paired']
        self.color_dict = dict(zip(self.top_artists.unique(), [cmap(i) for i in range(len(self.top_artists.unique()))]))
        self.top_artists_colors = self.top_artists.map(self.color_dict)

        # This is for top artists and top tracks, maybe moving it to a different function could be good idk

        

        self.update_user_legend()

    def update_colorbar(self):
        cmap = mpl.cm.Blues(np.linspace(0,1,17))
        cmap = mpl.colors.ListedColormap(cmap[10:,:-1])
        
        norm = mpl.colors.Normalize(vmin=min(self.mins_listened), vmax=max(self.mins_listened))
        self.colorbar_colors = [cmap(norm(value)) for value in self.mins_listened]
     
        self.cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap), ax=self.user_ax, orientation='vertical')
        self.cbar.set_label('Minutes Listened')

        ticks = np.linspace(min(self.mins_listened), max(self.mins_listened), 8)
        self.cbar.set_ticks(ticks)
        self.cbar.set_ticklabels([f'{int(value)} mins' for value in ticks])
        self.user_ax.legend(handles=[]) # Turn off the legend

    def update_user_legend(self):
        legend_handles = [plt.Rectangle((0, 0), 1, 1, color=self.color_dict[artist]) for artist in self.top_artists.unique()]
        legend_labels = self.top_artists.unique()
        self.user_ax.legend(legend_handles, legend_labels, title='Artists')

    
class ReorderColumnsDialog(QDialog):
    def __init__(self, current_order=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reorder Columns")

        self.layout = QVBoxLayout(self)
        self.dropdowns_layout = QHBoxLayout()
        attribute_list = ['danceability_%', 'valence_%', 'energy_%', 'acousticness_%', 'instrumentalness_%', 'liveness_%', 'speechiness_%' ]

        self.current_order = current_order
        self.dropdowns = [QComboBox(self) for _ in range(len(attribute_list))]

        for i, attribute in enumerate(attribute_list):
            
            for j in range((len(attribute_list))):
                self.dropdowns[j].addItem(attribute)
                #TODO: Bonus feature, make all the dropdowns dislay their current attribute and add the rest -- would look prettier
                
            self.dropdowns_layout.addWidget(self.dropdowns[i])

        self.layout.addLayout(self.dropdowns_layout)
        self.num_lines = QSpinBox(self)
        self.num_lines.setRange(10, 953)
        self.num_lines.setValue(250) # default value that looks "good enough"
        self.layout.addWidget(self.num_lines)

        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)

    def get_new_order(self):
        return [dropdown.currentText() for dropdown in self.dropdowns]
    
    def get_num_lines(self):
        return self.num_lines.value()


class ParallelCoordinatesWidget(QWidget):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df

        self.parallel_fig = Figure()
        self.parallel_canvas = FigureCanvas(self.parallel_fig)
        self.par_ax = self.parallel_fig.add_subplot(111)

        layout = QVBoxLayout()
        layout.addWidget(self.parallel_canvas)
        

        self.rearrange_btn = QPushButton("Rearrange order", self)
        self.rearrange_btn.clicked.connect(self.rearrange)
        layout.addWidget(self.rearrange_btn)

        

        self.setLayout(layout)

    def update_parallel_coordinates(self, df, target_column):
        self.par_ax.clear()

        #h = df[['key', 'danceability_%', 'valence_%', 'energy_%', 'acousticness_%', 'instrumentalness_%', 'liveness_%', 'speechiness_%']].copy()

        
        lines = parallel_coordinates(df, target_column, ax=self.par_ax, colormap='Paired')
        
        paired=mpl.colormaps['Paired']
        self.par_ax.legend(handles = [
            Line2D([0], [0], label='A', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[0]),
            Line2D([0], [0], label='A#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[1]),
            Line2D([0], [0], label='B', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[2]),
            Line2D([0], [0], label='C#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[3]),
            Line2D([0], [0], label='D', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[4]),
            Line2D([0], [0], label='D#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[5]),
            Line2D([0], [0], label='E', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[6]),
            Line2D([0], [0], label='F', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[7]),
            Line2D([0], [0], label='F#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[8]),
            Line2D([0], [0], label='G', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[9]),
            Line2D([0], [0], label='G#', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[10]),
            Line2D([0], [0], label='No key \nspecified', marker = 'o', markersize = 10, linestyle = '', color=paired.colors[11])
        ], title = "Song key", bbox_to_anchor = (1, 1), loc = "upper left",)

        # cursor = mplcursors.cursor(lines, hover=True)
        # cursor.connect("add", lambda sel: sel.annotation.set_text(f"Track Name: {df['track_name'][1]}"))
        #cursor = mplcursors.cursor(lines, hover=True)

        def on_hover(sel):
            print(sel.target.index)
            print(sel)
            print(f"Track Name: {df['track_name'][0]}")
            return
            index = sel.target.index # Get the index of the hovered line
            track_name = df.at[index, 'track_name']  # Get the track name using the index
            sel.annotation.set_text(f"Track Name: {track_name}")

        #cursor.connect("add", on_hover)

        self.parallel_canvas.draw()
    def rearrange(self):
        dialog = ReorderColumnsDialog(current_order=self.df.columns)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            new_order = dialog.get_new_order()
            
            new_order.append('key')

            new_df = self.df.head(dialog.get_num_lines())[new_order]
            #new_df = self.df.head(30)[new_order]
            


            # Update the parallel coordinates plot
            self.plot_widget = self.update_parallel_coordinates(new_df, 'key')
            #self.plot_widget.set_axis_off()

            # Update the layout
            #self.layout.replaceWidget(self.layout.itemAt(0).widget(), self.plot_widget)

            #self.update_parallel_coordinates(self.df, target_column='key')


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename')
    #parser.add_argument('-s', '--streamhistory')

    if len(sys.argv) != 3:
     assert(False), "Number of args is not 1! Please pass -f <spotify kaggle file>."

    args = parser.parse_args()
  
    validate_args(args)

    app = QApplication(sys.argv)
    main_gui = Main()
    main_gui.show()
    sys.exit(app.exec())

    


