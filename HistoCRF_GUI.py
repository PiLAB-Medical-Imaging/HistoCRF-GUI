# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 15:16:11 2026

@author: Pilab
"""

from PIL import Image
import os
import sys
from PyQt6.QtCore import Qt, QPointF, pyqtSignal

from PyQt6.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QPen,
    QColor,
)

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QListWidget,
    QLabel,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
)

OPENSLIDE_PATH = "D:/workshop_histoCRF/openslide-bin-4.0.0.13-windows-x64/openslide-bin-4.0.0.13-windows-x64/bin"
if hasattr(os, 'add_dll_directory'):
    # Windows
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
else:
    import openslide


def pil_to_qimage(img):
    img = img.convert("RGB")

    data = img.tobytes()

    qimg = QImage(data, img.width, img.height, img.width * 3,
                  QImage.Format.Format_RGB888)

    return qimg.copy()


class MiniMap(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(150, 150)

        self.thumbnail = None

        self.slide_w = 1
        self.slide_h = 1

        self.viewport_rect = None

        self.viewer = None

    def set_data(self, thumbnail, slide_w, slide_h, viewport_rect):
        self.thumbnail = thumbnail
        self.slide_w = slide_w
        self.slide_h = slide_h
        self.viewport_rect = viewport_rect

        self.update()

    def paintEvent(self, event):

        if self.thumbnail is None:
            return

        painter = QPainter(self)

        painter.fillRect(self.rect(), QColor(30, 30, 30))

        thumb = self.thumbnail.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        xoff = (self.width() - thumb.width()) // 2
        yoff = (self.height() - thumb.height()) // 2

        painter.drawPixmap(xoff, yoff, thumb)

        if self.viewport_rect is None:
            return

        sx = thumb.width() / self.slide_w
        sy = thumb.height() / self.slide_h

        vx = self.viewport_rect.left() * sx
        vy = self.viewport_rect.top() * sy

        vw = self.viewport_rect.width() * sx
        vh = self.viewport_rect.height() * sy

        painter.setPen(QPen(QColor(255, 0, 0), 1))

        painter.drawRect(int(xoff + vx), int(yoff + vy), int(vw), int(vh))

    def mousePressEvent(self, event):
        self.jump_to(event.pos())

    def mouseMoveEvent(self, event):
        self.jump_to(event.pos())

    def jump_to(self, pos):

        if self.thumbnail is None:
            return

        thumb = self.thumbnail.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        xoff = (self.width() - thumb.width()) // 2
        yoff = (self.height() - thumb.height()) // 2

        x = pos.x() - xoff
        y = pos.y() - yoff

        if x < 0 or y < 0:
            return

        sx = self.slide_w / thumb.width()
        sy = self.slide_h / thumb.height()

        slide_x = x * sx
        slide_y = y * sy

        if self.viewer is not None:

            self.viewer.centerOn(slide_x, slide_y)
            self.viewer.update_visible_region()


class SVSView(QGraphicsView):

    clicked = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.slide = None

        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        self.current_scale = 1.0

        self.last_request = None

        self.minimap = MiniMap(self)
        self.minimap.viewer = self
        self.minimap.move(10, 10)
        self.minimap.raise_()

    def load_slide(self, slide):

        self.slide = slide

        w, h = slide.dimensions

        self.scene.setSceneRect(0, 0, w, h)

        # Create overview thumbnail once
        self.thumbnail = slide.get_thumbnail((4000, 4000))

        self.thumbnail_qpixmap = QPixmap.fromImage(
            pil_to_qimage(self.thumbnail))

        self.update_visible_region()

    def wheelEvent(self, event):

        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8

        self.current_scale *= factor

        self.scale(factor, factor)

        self.update_visible_region()

    def resizeEvent(self, event):

        super().resizeEvent(event)

        self.minimap.move(self.width() - self.minimap.width() - 10, 10)

        self.update_visible_region()

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.MouseButton.RightButton:

            scene_pos = self.mapToScene(event.pos())

            self.clicked.emit(int(scene_pos.x()), int(scene_pos.y()))

        super().mouseReleaseEvent(event)

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self.update_visible_region()

    def choose_level(self):

        if self.slide is None:
            return 0

        zoom = self.transform().m11()

        best_level = 0
        # if zoom < 0.2:
        #     best_level = 2
        if zoom < 0.5:
            best_level = 1

        return best_level

    def update_visible_region(self):

        if self.slide is None:
            return

        zoom = self.transform().m11()

        if zoom < 0.2:

            slide_w, slide_h = self.slide.dimensions

            thumb_w = self.thumbnail.width

            scale_x = slide_w / thumb_w

            self.pixmap_item.setPixmap(self.thumbnail_qpixmap)

            self.pixmap_item.setPos(0, 0)

            self.pixmap_item.setScale(scale_x)

            viewport_rect = (self.mapToScene(self.viewport().rect()
                                             ).boundingRect())

            self.minimap.set_data(self.thumbnail_qpixmap, slide_w, slide_h,
                                  viewport_rect)

            return

        viewport_rect = self.viewport().rect()

        scene_rect = self.mapToScene(viewport_rect).boundingRect()

        slide_w, slide_h = self.slide.dimensions

        x = max(0, int(scene_rect.left()))
        y = max(0, int(scene_rect.top()))

        w = min(slide_w - x, int(scene_rect.width()))
        h = min(slide_h - y, int(scene_rect.height()))

        if w <= 0 or h <= 0:
            return

        level = self.choose_level()

        ds = self.slide.level_downsamples[level]

        request = (x, y, w, h, level)

        if request == self.last_request:
            return

        self.last_request = request

        level_size = (max(1, int(w / ds)), max(1, int(h / ds)),)

        region = self.slide.read_region((x, y), level, level_size)

        region = region.convert("RGB")

        qimg = pil_to_qimage(region)

        pixmap = QPixmap.fromImage(qimg)

        self.pixmap_item.setPixmap(pixmap)

        self.pixmap_item.setPos(x, y)

        self.pixmap_item.setScale(ds)

        viewport_rect = (self.mapToScene(
            self.viewport().rect()).boundingRect())

        self.minimap.set_data(self.thumbnail_qpixmap, slide_w, slide_h,
                              viewport_rect)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("HistoCRF Viewer")

        self.resize(1600, 1000)

        root = QWidget()

        self.setCentralWidget(root)

        layout = QHBoxLayout(root)

        left = QVBoxLayout()

        self.open_btn = QPushButton("Open SVS")

        self.coords = QListWidget()

        self.coord_label = QLabel("Coordinates: (right click)")

        left.addWidget(self.open_btn)
        left.addWidget(self.coord_label)
        left.addWidget(self.coords)

        self.viewer = SVSView()

        layout.addLayout(left, 1)
        layout.addWidget(self.viewer, 5)

        self.open_btn.clicked.connect(self.open_slide)

        self.viewer.clicked.connect(self.on_click)

    def on_click(self, x, y):

        self.coords.addItem(f"X={x}  Y={y}")

    def open_slide(self):

        file, _ = QFileDialog.getOpenFileName(self, "Open SVS", "", "*.svs")

        if not file:
            return

        slide = openslide.OpenSlide(file)
        self.viewer.load_slide(slide)


def main():

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
