from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTransform
from PyQt6.QtQuick import QQuickImageProvider


class ThumbnailProvider(QQuickImageProvider):
    def __init__(self):
        super(ThumbnailProvider, self).__init__(QQuickImageProvider.ImageType.Image)
        self.thumbnails = {}

    def add_to_collection(self, cidx, img, type):
        img_id = f'{cidx:05d}_{len(self.collection_thumbnails(cidx)):05d}'
        self.thumbnails[img_id] = {'image': img, 'segment_idx': cidx, 'type': type}

        if type == 'gaze':
            symbol = u"\U0001F441"
        elif type == 'move':
            symbol = u"\U000021F5"
        else:
            symbol = ''

        #cnt_type = len([t for t in self.thumbnails.values() if t['type'] == type])
        #label = f'{symbol} {cnt_type:02d}'

        cnt_type = len([t for t in self.thumbnails.values() if t['type'] == type and t['segment_idx'] == cidx])
        label = f'{symbol}{cnt_type:02d}'
        return img_id, label

    def requestImage(self, img_id_comp, requested_size):
        img_id, rot_angle = img_id_comp.split('#')
        img = self.thumbnails[img_id]['image']

        if requested_size.width() > 0 and requested_size.height() > 0:
            img = img.scaled(requested_size, Qt.KeepAspectRatio)

        img = img.transformed(QTransform().rotate(int(rot_angle)))

        return img, img.size()

    def collection_thumbnails(self, segment_idx):
        return [img_id for img_id, values in self.thumbnails.items() if values['segment_idx'] == segment_idx]

