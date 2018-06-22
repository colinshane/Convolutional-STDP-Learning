"""
__author__ = Nicolas Perez-Nieves
__email__ = nicolas.perez14@imperial.ac.uk

SDNN Implementation based on Kheradpisheh, S.R., et al. 'STDP-based spiking deep neural networks 
for object recognition'. arXiv:1611.01421v1 (Nov, 2016)
"""
from sklearn.neural_network import MLPClassifier
from SDNN_cuda import SDNN
from Classifier import Classifier
import numpy as np
from os.path import dirname, realpath
from math import floor

import time


def main():

    # Flags
    learn_SDNN = True  # This flag toggles between Learning STDP and classify features
    # or just classify by loading pretrained weights for the face/motor dataset
    if learn_SDNN:
        set_weights = False  # Loads the weights from a path (path_set_weigths) and prevents any SDNN learning
        save_weights = True  # Saves the weights in a path (path_save_weigths)
        save_features = True  # Saves the features and labels in the specified path (path_features)
    else:
        set_weights = True  # Loads the weights from a path (path_set_weigths) and prevents any SDNN learning
        save_weights = False  # Saves the weights in a path (path_save_weigths)
        save_features = True  # Saves the features and labels in the specified path (path_features)

    # ------------------------------- Learn, Train and Test paths-------------------------------#
    # Image sets directories
    path = dirname(dirname(realpath(__file__)))
    # spike_times_learn = [path + '/datasets/LearningSet/Face/', path + '/datasets/LearningSet/Motor/']
    # spike_times_train = [path + '/datasets/TrainingSet/Face/', path + '/datasets/TrainingSet/Motor/']
    # spike_times_test = [path + '/datasets/TestingSet/Face/', path + '/datasets/TestingSet/Motor/']
    spike_times_train = [path + "/mnist/training/" + str(i) for i in range(10)]
    spike_times_test =  [path + "/mnist/testing/" + str(i) for i in range(10)]

    # Results directories
    path_set_weigths = '../results/'
    path_save_weigths = '../results/'
    path_features = '../results/'

    # ------------------------------- SDNN -------------------------------#
    # SDNN_cuda parameters
    DoG_params = {'img_size': (28, 28), 'DoG_size': 7, 'std1': 1., 'std2': 2.}  # img_size is (col size, row size)
    total_time = 15
    network_params = [{'Type': 'input', 'num_filters': 1, 'pad': (0, 0), 'H_layer': DoG_params['img_size'][1],
                       'W_layer': DoG_params['img_size'][0]},
                      {'Type': 'conv', 'num_filters': 4, 'filter_size': 5, 'th': 10.},
                      {'Type': 'pool', 'num_filters': 4, 'filter_size': 7, 'th': 0., 'stride': 6},
                      {'Type': 'conv', 'num_filters': 20, 'filter_size': 17, 'th': 60.},
                      {'Type': 'pool', 'num_filters': 20, 'filter_size': 5, 'th': 0., 'stride': 5},
                      {'Type': 'conv', 'num_filters': 20, 'filter_size': 5, 'th': 2.}]

    weight_params = {'mean': 0.8, 'std': 0.01}

    max_learn_iter = [0, 10000, 0, 15000, 0, 20000, 0]
    stdp_params = {'max_learn_iter': max_learn_iter,
                   'stdp_per_layer': [0, 10, 0, 4, 0, 2],
                   'max_iter': sum(max_learn_iter),
                   'a_minus': np.array([0, .003, 0, .0003, 0, .0003], dtype=np.float32),
                   'a_plus': np.array([0, .004, 0, .0004, 0, .0004], dtype=np.float32),
                   'offset_STDP': [0, floor(network_params[1]['filter_size']),
                                   0,
                                   floor(network_params[3]['filter_size']),
                                   0,
                                   floor(network_params[5]['filter_size'])]}

    # Create network
    first_net = SDNN(network_params, weight_params, stdp_params, total_time,
                     DoG_params=DoG_params,
                     spike_times_train=spike_times_train, spike_times_test=spike_times_test, device='GPU')

    # Set the weights or learn STDP
    if set_weights:
        weight_path_list = [path_set_weigths + 'weight_' + str(i) + '.npy' for i in range(len(network_params) - 1)]
        first_net.set_weights(weight_path_list)
    else:
        first_net.train_SDNN()

    # Save the weights
    if save_weights:
        weights = first_net.get_weights()
        for i in range(len(weights)):
            np.save(path_save_weigths + 'weight_' + str(i), weights[i])

    # Get features
    X_train, y_train = first_net.train_features()
    X_test, y_test = first_net.test_features()

    # Save X_train and X_test
    if save_features:
        np.save(path_features + 'X_train', X_train)
        np.save(path_features + 'y_train', y_train)
        np.save(path_features + 'X_test', X_test)
        np.save(path_features + 'y_test', y_test)
        np.savetxt(path_features + 'X_train', X_train)
        np.savetxt(path_features + 'y_train', y_train)
        np.savetxt(path_features + 'X_test', X_test)
        np.savetxt(path_features + 'y_test', y_test)

    # X_train = np.load(path_features + 'X_train.npy')
    # y_train = np.load(path_features + 'y_train.npy')

    # X_test = np.load(path_features + 'X_test.npy')
    # y_test = np.load(path_features + 'y_test.npy')
    s = np.random.permutation(np.shape(X_train)[0])
    X_train, y_train = X_train[s], y_train[s]
    s1 = np.random.permutation(np.shape(X_test)[0])
    X_test, y_test = X_test[s1], y_test[s1]
    # print(y_train)
    # ------------------------------- Classify -------------------------------#
    classifier_params = {'C': 1.0, 'gamma': 'auto'}
    train_mean = np.mean(X_train, axis=0)
    train_std = np.std(X_train, axis=0)
    X_train -= train_mean
    X_test -= train_mean
    X_train /= (train_std + 1e-5)
    X_test /= (train_std + 1e-5)
   # svm = Classifier(X_train, y_train, X_test, y_test, classifier_params, classifier_type='SVM')
   # train_score, test_score = svm.run_classiffier()
    
    clf = MLPClassifier(solver='lbfgs', hidden_layer_sizes=(10))
    clf.fit(X_train, y_train)
    train_score = clf.score(X_train, y_train)
    test_score = clf.score(X_test, y_test)
    print('Train Score: ' + str(train_score))
    print('Test Score: ' + str(test_score))

    print('DONE')


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(end - start)