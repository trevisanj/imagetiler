import glob
import os, sys
from PIL import Image
import logging
import imageio
import numpy as np
import random
import copy
import operator
import sys
import scipy.misc
import a107


class ImgInfo(object):
    def __init__(self, im, index):
        self.im = im
        self.means = np.mean(im, (0, 1))  # mean R, G, B
        self.index = index

class TylerDurden:
    def __init__(self, input_filename, output_filename, thumbnails_dir, niter, interactive):
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.thumbnails_dir = thumbnails_dir
        self.niter = niter
        self.interactive = interactive


    def init(self):
        self.thumbnails = self.load_thumbs()
        self.nt = len(self.thumbnails)
        self.iim = Image.open(self.input_filename)

       
        self.available = list(range(len(self.thumbnails)))
        random.shuffle(self.available)

        # # PREPARES INPUT IMAGE
        # - resizes to have at least 2x the amount of thumbnails needed to fill the image without repetition
        # - crops it so that its width and height are exact multiples of the thumbail width/height

        # Thumbnail dimension (assumes all thumbnails have same dimensions and are square)
        self.tdim = self.thumbnails[0].im.shape[0]
    
        w, h = self.iim.size
        ntn = float(w * h) / self.tdim ** 2  # number of self.thumbnails needed
        if ntn > self.nt / 2:
            scale = np.sqrt(float(self.nt / 2) / ntn)
            a107.get_python_logger().info("Will rescale input image to scale={:2f} because number "
                "of thumbnails = {} and we need {}".format(scale, self.nt, ntn))
            self.iim.thumbnail([int(w * scale), int(h * scale)])
    
        # Crops reference so that its width and height are multiples of self.tdim
        w, h = self.iim.size
        self.iim = self.iim.crop([0, 0, int(w / self.tdim) * self.tdim, int(h / self.tdim) * self.tdim])
        self.width, self.height = self.iim.size
        # num rows, num cols
        self.nr, self.nc = int(self.height / self.tdim), int(self.width / self.tdim)

        self.A = np.asarray(self.iim)

        # Size of individual
        self.size = self.nr * self.nc
        print("Individual size: {}".format(self.size))

        # Mean RGB colors for reference image
        self.refmeans = np.zeros((self.nr, self.nc, 3))
        for i in range(self.nr):
            for j in range(self.nc):
                idx, jdx = i * self.tdim, j * self.tdim
                self.refmeans[i, j, :] = np.mean(self.A[idx:idx + self.tdim, jdx:jdx + self.tdim, :], (0, 1))
        self.refmeans = self.refmeans.reshape((self.size, 3))
        pass

    def run(self):
        self.ind = self.get_random_individual2()
        ii = 0

        if self.interactive:
            import matplotlib.pyplot as plt
            plt.ion()

        ii = 0

        for i in range(self.niter):
            self.improve2()
            self.improve3()
            print("Gen {:3d}; mark: {}".format(i, self.evaluate()))

            if self.interactive:
                im = self.make_image()/255

                if ii == 0:
                    xq = plt.imshow(im)
                    plt.tight_layout()
                else:
                    xq.set_data(im)
                input("porra")

                plt.show()

                ii += 1

        if self.interactive:
            plt.ioff()
            plt.show()

    def save(self):
        im = self.make_image()
        image = Image.fromarray(im)  # scipy.misc.toimage(im, cmin=0.0, cmax=255).save(filename_out)
        image.save(self.output_filename)
        # print("Just saved '{}'".format(self.output_filename))

    def evaluate(self):
        """The lower the better"""
        indmeans = self.get_indmeans()
        ret = np.mean((indmeans - self.refmeans) ** 2)
        # ret = reduce(operator.mul, dif, 1.)**(1./3)   # geometric mean of 3 colors
        return ret

    def get_random_individual2(self):
        """
        Returns random individual not repeating images

        **Designed for single call**
        """
        ret = [self.thumbnails[i] for i in self.available[:self.size]]
        # if len(ret) < size:
        #     raise RuntimeError(
        #         "Need more thumbnails (at least {}, but I have {})!".format(size, len(thumbs)))
        self.available = self.available[self.size:]
        return ret

    def load_thumbs(self):
        ret = []
        for i, fn in enumerate(glob.glob(os.path.join(self.thumbnails_dir, "*.jpg"))):
            im = imageio.imread(fn)
            ret.append(ImgInfo(im, i))
        return ret
    
    def get_indmeans(self):
        return np.array([t.means for t in self.ind])

    def make_image(self):
        # dtype must be 'uint8' or PIL won't save image properly
        im = np.zeros((self.height, self.width, 3), dtype='uint8')
        k = 0
        for i in range(self.nr):
            for j in range(self.nc):
                idx, jdx = i * self.tdim, j * self.tdim
                im[idx:idx + self.tdim, jdx:jdx + self.tdim, :] = self.ind[k].im
                k += 1
        return im
       
    def improve2(self):
        dif_ind = np.mean((self.get_indmeans()-self.refmeans)**2, 1)
        for i in range(self.size):
            iav = random.randint(0, len(self.available)-1)
            info = self.thumbnails[self.available[iav]]
    
            mark = np.mean((self.refmeans[i, :]-info.means)**2)
            if mark < dif_ind[i]:
                # takes available thumb
                del self.available[iav]
                # gives back thumb
                self.available.append(self.ind[i].index)
    
                self.ind[i] = info

    def improve3(self):
        """Swaps thumbnails if this represents an improvement"""
        dif_ind = np.mean((self.get_indmeans() - self.refmeans) ** 2, 1)
        for i in range(self.size):
            while True:
                j = random.randint(0, self.size-1)
                if i != j:
                    break

            mark0 = np.mean((self.refmeans[i, :]-self.ind[j].means)**2)
            mark1 = np.mean((self.refmeans[j, :]-self.ind[i].means)**2)
            if mark0+mark1 < dif_ind[i]+dif_ind[j]:
                temp = self.ind[i]
                self.ind[i] = self.ind[j]
                self.ind[j] = temp
