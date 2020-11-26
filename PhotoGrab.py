import os
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Union

import click
import numpy as np
from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile
from skimage.metrics import structural_similarity


class PhotoGrab:
    def __init__(self, photo_dir: str = None, target_dir: str = None):
        home = Path.home()

        if self._path_exists(photo_dir):
            self.photo_dir = Path(photo_dir)
        else:
            self.photo_dir = home.joinpath("appdata", 'local', 'packages',
                                           'Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy',
                                           'localstate', 'assets')

        if self._path_exists(target_dir):
            self.target_dir = Path(target_dir)
        else:
            self.target_dir = home.joinpath('pictures', 'saved pictures')

        self.existing_images = []
        for i in self.target_dir.iterdir():
            if i.suffix == '.jpg':
                with Image.open(i) as img:
                    self.existing_images.append(self.grayscale(img))

    def run(self):
        # copy those which are greater than 250kb
        photos = [p for p in self.photo_dir.iterdir()
                  if p.stat().st_size > 250000 and p.is_file()]

        # take those whose width are greater than height (landscape pictures)
        # with ProcessPoolExecutor() as pool:
        #     to_copy = pool.map(self._flag_photo_for_copy, photos)
        to_copy = self._progress_bar_map(self._flag_photo_for_copy, photos)

        date = datetime.now().strftime("%Y-%m%d")
        count = 0

        for image_path in to_copy:
            if image_path is None:
                continue

            count += 1
            shutil.copy2(image_path, self.target_dir.joinpath(f'{date}_{count}.jpg').as_posix())

        click.echo(f'Copied a total of {count} photos')
        return count

    @staticmethod
    def _progress_bar_map(fn, photos):
        results = []
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(fn, i) for i in photos]

            with click.progressbar(as_completed(futures),
                                   length=len(photos),
                                   label="Copying images") as bar:
                for f in bar:
                    results.append(f.result())

        return results

    def _flag_photo_for_copy(self, photo: Path):
        with Image.open(photo) as img:  # type: JpegImageFile
            width, height = img.size
            if width < height:
                return None

            gray = self.grayscale(img)
            for exist in self.existing_images:
                if exist.size != gray.size:
                    continue
                if structural_similarity(gray, exist, multichannel=True) > 0.9:
                    return None

            return photo

    @staticmethod
    def _path_exists(path: str):
        return path is not None and os.path.exists(path)

    @staticmethod
    def grayscale(img: Union[JpegImageFile, np.ndarray]) -> np.ndarray:
        # formula: https://en.wikipedia.org/wiki/Grayscale#Luma_coding_in_video_systems
        return np.array(img).dot([0.299, 0.587, 0.114])
