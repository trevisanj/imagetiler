from PIL import Image
import glob
import os
import a107
import argparse
import numpy as np


__all__ = ["image_resize_square", "Bank", "BankCommands", "BankConsole"]


def image_resize_square(image, side):
    """Resizes image to fit in square of [side]x[side]."""
    w, h = image.size
    if w > h:
        w_ = side
        h_ = int(side * h / w)
    else:
        h_ = side
        w_ = int(side * w / h)
    ret = image.resize((w_, h_))
    return ret

def image_resize(image, scale):
    if scale != 1.:
        w, h = image.size
        ret = image.resize((int(w*scale), int(h*scale)))
        return ret
    return image

def put_border(image):
    """
    Enlarges image so that it can be rotated without any piece of the original contents escaping
    """

    w, h = image.size
    newdim = int(np.sqrt(2*max(w, h)**2))

    ret = Image.new("RGBA", (newdim, newdim), (255, 255, 255, 0))
    ret.paste(image, ((newdim - w) // 2, (newdim - h) // 2), image)

    return ret


class Bank:
    @property
    def bank(self):
        if len(self.timeline) > 0:
            return self.timeline[self.i]
        return []

    def __init__(self, data_dir):
        self.i = 0
        self.timeline = []
        self.data_dir = data_dir

    def __refresh_i(self):
        if self.i >= len(self.timeline):
            self.i = len(self.timeline) - 1
        if self.i < 0: self.i = 0

    def timeline_append(self, bank):
        # Eliminates redos
        while self.i < len(self.timeline)-1:
            self.timeline.pop()

        self.timeline.append(bank)

        # Copies metadata, i.e., in this case, filename
        if len(self.timeline) > 1:
            for i0, i1 in zip(self.timeline[0], bank):
                i1.filename = i0.filename

        self.i = len(self.timeline)-1
        self.__refresh_i()

    def timeline_left(self):
        self.i -= 1
        self.__refresh_i()

    def timeline_right(self):
        self.i += 1
        self.__refresh_i()

    def load(self):
        a = []
        for fn in glob.glob(os.path.join(self.data_dir, "*")):
            try:
                a.append(Image.open(fn, "r"))
            except OSError:
                pass
        self.timeline_append(a)

    def resize_square(self, side):
        """
        Resizes to fit in square of [side]x[side].
        """
        self.timeline_append([image_resize_square(image, side) for image in self.bank])

    def resize(self, scale):
        self.timeline_append([image_resize(image, scale) for image in self.bank])

    def resize_same_area(self, mima=0.5):
        # f1[i] = sqrt(A1[i])
        # A1[i] = A0[i]*K[i]
        # K[i] = Aref*k[i]
        # k[i] = 1/A0[i]

        mima = float(mima)

        # if not (0 <= mima <= 1.):
        #     raise ValueError("Argument 'mima' must be within [0, 1]")
        areas = [np.sum(np.asarray(o)[:,:,-1] > 0) for o in self.bank]
        if np.any(areas == 0):
            raise ValueError("Cannot resze_same_area() with any area=0")
        Aref = (max(areas)-min(areas))*mima+min(areas)
        k = [1/a for a in areas]
        f = [np.sqrt(Aref*x) for x in k]
        ret = []
        for img, factor in zip(self.bank, f):
            w, h = img.size
            ret.append(img.resize((int(w*factor), int(h*factor))))
        self.timeline_append(ret)

    def put_border(self):
        ret = [put_border(image) for image in self.bank]
        self.timeline_append(ret)

    def save(self):
        d = a107.new_filename(self.data_dir)
        os.mkdir(d)
        ret = {"data_dir": d,
               "filenames": []}
        for img in self.bank:
            _, fn = os.path.split(img.filename)
            newpath = os.path.join(d, fn)
            img.save(newpath)
            ret["filenames"].append(newpath)
        return ret



class BankCommands(a107.ConsoleCommands):
    def undo(self):
        pass

    def redo(self):
        self.console.bank.timeline_right()

    def undo(self):
        self.console.bank.timeline_left()

    def resize_square(self, side):
        self.console.bank.resize_square(int(side))

    def resize(self, scale):
        """Resizes to scale factor."""
        self.console.bank.resize(scale)

    def resize_same_area(self, mima=0.5):
        """
        Resizes all images so that all their non-transparent area measure the same

        Args:
            mima: [0, 1] factor meaning if will resample from minimum or maximum area
        """
        self.console.bank.resize_same_area(mima)

    def report0(self):
        ob = self.console.bank
        return {"num_images": len(ob.bank),
                "num_moments": len(ob.timeline),
                "i": ob.i,
                "data_dir": ob.data_dir}

    def report1(self):
        rows = []
        header = ["#", "filename", "width", "height", "mode"]
        for i, image in enumerate(self.console.bank.bank):
            rows.append([i, image.filename, *image.size, image.mode])
        return rows, header

    def load(self):
        return self.console.bank.load()

    def save(self):
        return self.console.bank.save()

    def put_border(self):
        """Enlarges images so that they can be rotated"""
        return self.console.bank.put_border()


class BankConsole(a107.Console):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, cmd=BankCommands(), **kwargs)
        self.bank = Bank(self.data_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,  formatter_class=a107.SmartFormatter)
    parser.add_argument('data_dir', type=str, help='Bank directory')

    args = parser.parse_args()

    console = BankConsole(slug="bankk", data_dir=args.data_dir)
    console.run()


