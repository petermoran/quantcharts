# -*- coding: utf-8 -*-
#
# Licensed under the terms of the MIT License
# Copyright (c) 2015 Pierre Raybaut

"""
Simple example illustrating Qt Charts capabilities to plot curves with
a high number of points, using OpenGL accelerated series
"""

from PyQt5.QtChart import QChart, QChartView, QLineSeries, QScatterSeries
from PyQt5.QtGui import QPolygonF, QPainter
from PyQt5.QtWidgets import QMainWindow

import numpy as np


options = {
    "antialias": True,
    "opengl": True,
}


def series_to_polyline(xdata, ydata):
    """Convert series data to QPolygon(F) polyline

    This code is derived from PythonQwt's function named
    `qwt.plot_curve.series_to_polyline`"""
    size = len(xdata)
    polyline = QPolygonF(size)
    pointer = polyline.data()
    dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
    pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
    memory = np.frombuffer(pointer, dtype)
    memory[:(size-1)*2+1:2] = xdata
    memory[1:(size-1)*2+2:2] = ydata
    return polyline


def series_to_polystep(xdata, ydata):
    """Convert series data to QPolygon(F) polyline

    This code is derived from PythonQwt's function named
    `qwt.plot_curve.series_to_polyline`"""
    nx = len(xdata)
    size = 2 * nx - 1
    polyline = QPolygonF(size)
    pointer = polyline.data()
    dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
    pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
    memory = np.frombuffer(pointer, dtype)
    # memory[:(size-1)*2+1:2] = xdata
    # memory[1:(size-1)*2+2:2] = ydata
    memory[:(size-1)*2+1:2][::2] = xdata
    memory[1:(size-1)*2+2:2][::2] = ydata
    memory[:(size-1)*2+1:2][1::2] = xdata[1:]
    memory[1:(size-1)*2+2:2][1::2] = ydata[:-1]
    return polyline


class MouseTracker:
    def __init__(self):
        self._total_dx = 0
        self._total_dy = 0

        self._x = None
        self._y = None

    def start(self, event):
        self._x = event.x()
        self._y = event.y()

    def track(self, event):
        x = event.x()
        y = event.y()
        dx = x - self._x
        dy = y - self._y
        self._x = x
        self._y = y
        self._total_dx += dx
        self._total_dy += dy
        return dx, dy

    def totals(self):
        return self._total_dx, self._total_dy

    def reset(self):
        self._total_dx = 0
        self._total_dy = 0


class TestChart(QChart):
    def __init__(self):
        super(TestChart, self).__init__()

        self._x_min = None
        self._x_max = None

        self._y_min = None
        self._y_max = None

    def createDefaultAxes(self):
        super(TestChart, self).createDefaultAxes()

        axis_x = self.axisX()
        axis_y = self.axisY()

        for axis in [axis_x, axis_y]:
            axis.setGridLineVisible(True)
            axis.setGridLineColor(Qt.lightGray)
            axis.setLinePenColor(Qt.gray)

        self._x_min = axis_x.min()
        self._x_max = axis_x.max()

        self._y_min = axis_y.min()
        self._y_max = axis_y.max()


class TestChartView(QChartView):
    def __init__(self, chart, parent=None):
        super(TestChartView, self).__init__(chart, parent)

        if options["antialias"]:
            self.setRenderHint(QPainter.Antialiasing)

        self._mouse_tracker = MouseTracker()

        self._disable_rubber_band()
        self._pan_active = False
        self._zoom_active = False

    def _disable_rubber_band(self):
        self._rubber_band_active = False
        self.setRubberBand(QChartView.NoRubberBand)

    def _enable_rubber_band(self):
        self._rubber_band_active = True
        self.setRubberBand(QChartView.RectangleRubberBand)

    def mousePressEvent(self, event):
        # enable pan on left-click, zoom on shift + left-click
        if event.button() == Qt.LeftButton:
            if event.modifiers() == Qt.ShiftModifier:
                self._enable_rubber_band()
            else:
                self._mouse_tracker.start(event)
                self._pan_active = True

        elif event.button() == Qt.RightButton:
            self._mouse_tracker.start(event)
            self._zoom_active = True

        super(TestChartView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            chart = self.chart()

            axisX = chart.axisX()
            axisX.setRange(chart._x_min, chart._x_max)

            axisY = chart.axisY()
            axisY.setRange(chart._y_min, chart._y_max)

        super(TestChartView, self).mouseReleaseEvent(event)

        if self._rubber_band_active:
            self._disable_rubber_band()

        self._pan_active = False
        self._zoom_active = False

    def mouseMoveEvent(self, event):
        if self._pan_active:
            dx, dy = self._mouse_tracker.track(event)
            self.chart().scroll(-dx, dy)

        elif self._zoom_active:
            dx, dy = self._mouse_tracker.track(event)

            for delta, axis in zip([dx, -dy], [self.chart().axisX(), self.chart().axisY()]):
                t0, tf = axis.min(), axis.max()
                delta = np.sign(delta) * min(abs(delta), 10)
                shift = (tf - t0) * delta * 0.01
                axis.setMin(t0 + shift)
                axis.setMax(tf - shift)

        super(TestChartView, self).mouseMoveEvent(event)


class TestWindow(QMainWindow):
    def __init__(self, parent=None):
        super(TestWindow, self).__init__(parent=parent)
        global options
        self.ncurves = 0
        self.chart = TestChart()
        self.chart.legend().hide()
        self.view = TestChartView(self.chart)
        self.setCentralWidget(self.view)

    def set_title(self, title):
        self.chart.setTitle(title)

    def add_data(self, xdata, ydata, color=None, **kwargs):
        global options
        curve = QLineSeries()
        # pen = curve.pen()
        # if color is not None:
        #     pen.setColor(color)
        # pen.setWidthF(1)
        # curve.setPen(pen)
        if color is not None:
            curve.setColor(color)
        curve.setUseOpenGL(options["opengl"])
        # curve.append(series_to_polyline(xdata, ydata))
        curve.replace(series_to_polystep(xdata, ydata))
        self.chart.addSeries(curve)
        self.chart.createDefaultAxes()
        self.ncurves += 1

    def add_scatter(self, xdata, ydata, color=None, **kwargs):
        global options
        curve = QScatterSeries()
        curve.setMarkerShape(QScatterSeries.MarkerShapeCircle)
        # pen = curve.pen()
        # if color is not None:
        #     pen.setColor(color)
        # pen.setWidthF(1)
        # curve.setPen(pen)
        if color is not None:
            curve.setColor(color)
        curve.setUseOpenGL(options["opengl"])
        curve.append(series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)
        self.chart.createDefaultAxes()
        self.ncurves += 1


if __name__ == '__main__':
    print("loading data")
    import h5py

    time = data["recvTimestamp"]  - data["recvTimestamp"][0]
    time = time * 1e-9 / 86400
    bid = data["bidPrice0"]
    ask = data["askPrice0"]

    lp = data["tradePrice"]
    side = data["tradeAggSide"]

    mb = side == b'B'
    ms = side == b'S'

    print("plotting")

    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    app = QApplication(sys.argv)

    window = TestWindow()

    npoints = 10000
    # xdata = np.linspace(0., 10., npoints)
    # window.add_data(xdata, np.sin(xdata), color=Qt.red)
    # window.add_data(xdata, np.cos(xdata), color=Qt.blue)
    window.add_data(time, bid, color=Qt.blue)
    window.add_data(time, ask, color=Qt.red)
    window.add_scatter(time[mb], lp[mb], color=Qt.blue)
    window.add_scatter(time[ms], lp[ms], color=Qt.red)
    window.set_title("Simple example with %d curves of %d points "
                     "(OpenGL Accelerated Series)"
                     % (window.ncurves, npoints))
    window.setWindowTitle("Simple performance example")
    window.show()
    window.resize(500, 400)

    sys.exit(app.exec_())
