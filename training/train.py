'''
    File name: train.py
    Author: Rui Monteiro
    Date created: 20/10/2018
    Date last modified: 21/11/2018
    Python Version: 3.6

Train:
 > python train.py --dataset dataset --model pilldex.model --labelbin lb.pickle

Check training process in Tensorboard:
 > tensorboard --logdir=logs/ --port=8101
'''
from keras.preprocessing.image import ImageDataGenerator
from keras.optimizers import Adam
from keras.preprocessing.image import img_to_array
from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from imutils import paths
import numpy as np
import argparse
import random
import pickle
import cv2
import os
from keras import backend as K
import importlib
from keras.callbacks import TensorBoard


def set_keras_backend(backend):
    print("A acertar o backend e libertar memória da grafica")
    if K.backend() != backend:
        os.environ['KERAS_BACKEND'] = backend
        importlib.reload(K)
        assert K.backend() == backend
    if backend == "tensorflow":
        K.get_session().close()
        cfg = K.tf.ConfigProto()
        cfg.gpu_options.allow_growth = True
        #cfg.gpu_options.allocator_type = 'BFC'
        K.set_session(K.tf.Session(config=cfg))
        K.clear_session()

def get_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--dataset", required=True,
                    help="path to input dataset (i.e., directory of images)")
    ap.add_argument("-m", "--model", required=True,
                    help="path to output model")
    ap.add_argument("-l", "--labelbin", required=True,
                    help="path to output label binarizer")
    ap.add_argument("-p", "--plot", type=str, default="plot.png",
                    help="path to output accuracy/loss plot")
    args = vars(ap.parse_args())

    return args


def print_history_accuracy(history):
    plt.plot(history.history['acc'])
    plt.plot(history.history['val_acc'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()

def print_history_loss(history):
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()        


def load_dataset(img_dims):

    args = get_arguments()
    # initialize the image dimensions
    data = []
    labels = []

    # Shuffle data.
    print("[INFO] loading images...")
    imagePaths = sorted(list(paths.list_images(args["dataset"])))
    print(imagePaths)
    random.seed(42)
    random.shuffle(imagePaths)

    # loop over the input images
    for imagePath in imagePaths:
        # load the image, pre-process it, and store it in the data list.
        print(imagePath)
        image = cv2.imread(imagePath)
        image = cv2.resize(image, (img_dims[1], img_dims[0]))
        image = img_to_array(image)
        data.append(image)

        # extract the class label from the image path and update the
        # labels list
        label = imagePath.split(os.path.sep)[-2]
        labels.append(label)      

    # Scale the raw pixel intensities to the range [0, 1].
    data = np.array(data, dtype="float") / 255.0
    labels = np.array(labels)
    print("[INFO] data matrix: {:.2f}MB".format(
        data.nbytes / (1024 * 1000.0)))
    
    # Binarize the labels.
    lb = LabelBinarizer()
    labels = lb.fit_transform(labels)

    # 80% for training, 20% for validation.
    (trainX, testX, trainY, testY) = train_test_split(data, labels, test_size=0.2, random_state=42)

    return trainX, testX, trainY, testY, lb

def compile_train_model(data_augmentation):
    
    args = get_arguments()
    # Hyperparameters.
    EPOCHS = 150
    INIT_LR = 2e-5
    BS = 32
    IMAGE_DIMS = (96, 96, 3)
    trainX, testX, trainY, testY, lb = load_dataset(IMAGE_DIMS)

    # Initialize the model.
    print("[INFO] compiling model...")
    model = models.build(width=IMAGE_DIMS[1],
                         height=IMAGE_DIMS[0],
                         depth=IMAGE_DIMS[2],
                         classes=len(lb.classes_))
   

    opt = Adam(lr=INIT_LR,
               decay=INIT_LR / EPOCHS)

    model.compile(loss="categorical_crossentropy",
                  optimizer=opt,
                  metrics=["accuracy"])

    tensorboard = TensorBoard(log_dir='Log/', histogram_freq=0,
                              write_graph=True, write_images=False)

    if not data_augmentation:
        print('Not using data augmentation.')
        print("[INFO] training network...")
        hist = model.fit(trainX, trainY, 
                         batch_size=BS,
                         nb_epoch=EPOCHS,
                         validation_data=(testX, testY),
                         callbacks=[tensorboard],
                         shuffle=True)
    else:
        print('Using real-time data augmentation.')
        # This will do preprocessing and real-time data augmentation:
        aug = ImageDataGenerator(rotation_range=25,
                                 width_shift_range=0.1,
                                 height_shift_range=0.1,
                                 shear_range=0.2,
                                 zoom_range=0.2,
                                 horizontal_flip=True,
                                 fill_mode="nearest")
 
        print("[INFO] training network...")
        datagen.fit(trainX)
        # Fit the model on the batches generated by datagen.flow().
        print(trainX.shape[0])
        hist = model.fit_generator(gen_data.flow(trainX,
                                                 trainY,
                                                 batch_size=BS,
                                                 ),
                                  validation_data = (testX, testY),
                                  steps_per_epoch= trainX.shape[0] // BS,
                                  epochs=EPOCHS,
                                  verbose=1,
                                  callbacks=[tensorboard],
                                  )

    print_history_accuracy(hist)
    print_history_loss(hist)

    # save the model to disk
    print("[INFO] serializing network...")
    model.save(args["model"])

    # save the label binarizer to disk
    print("[INFO] serializing label binarizer...")
    f = open(args["labelbin"], "wb")
    f.write(pickle.dumps(lb))
    f.close()

    #   Avaliação   final   com os  casos   de  teste  - Evaluate
    scores  =   model.evaluate(testX,  testY, verbose=1)  
    print('Scores:  ',  scores) 
    print("Accuracy:    %.2f%%" %   (scores[1]*100))    
    print("Erro modelo:    %.2f%%" %   (100-scores[1]*100))
    
 def main():
    set_keras_backend("tensorflow")
    args = get_arguments()
    compile_train_model(data_augmentation=True)

if __name__ == '__main__':
    main()