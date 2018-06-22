import numpy as np
from os import listdir
from sys import exit
from itertools import chain, tee
from os.path import dirname, realpath

def gen_iter_paths(path_list):
    labels = np.zeros(len(listdir(path_list[0])))
    paths_iter = iter([path_list[0] + listdir(path_list[0])[i] for i in range(labels.size)])
    for idir in range(1, len(path_list)):
        file_names = listdir(path_list[idir])
        labels = np.append(labels, (idir) * np.ones(len(file_names)))
        files_tmp = iter([path_list[idir] + file_names[i] for i in range(len(file_names))])
        paths_iter = chain(paths_iter, files_tmp)
    np.savetxt(path + "/mnist/labels", labels)
    return paths_iter, labels

path = dirname(dirname(realpath(__file__)))
gen_iter_paths([path + "/mnist/training/" + str(i) for i in range(10)])