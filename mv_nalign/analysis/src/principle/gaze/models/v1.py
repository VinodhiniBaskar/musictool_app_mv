from keras.models import Sequential
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv2D
from keras.layers.convolutional import MaxPooling2D
from keras.layers.advanced_activations import ReLU
from keras.layers.core import Activation
from keras.layers.core import Flatten
from keras.layers.core import Dropout
from keras.layers.core import Dense

IMG_SIZE = 224


def create_model():
    model = Sequential()

    input_shape = (IMG_SIZE, IMG_SIZE, 3)
    chan_dim = -1

    # Block #1: first CONV => RELU => CONV => RELU => POOL
    # layer set
    model.add(Conv2D(32, (3, 3), padding="same", kernel_initializer="he_normal", input_shape=input_shape))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(Conv2D(32, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    # Block #2: second CONV => RELU => CONV => RELU => POOL
    # layer set
    model.add(Conv2D(32, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(Conv2D(32, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    # Block #3: third CONV => RELU => CONV => RELU => POOL
    # layer set
    model.add(Conv2D(32, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(Conv2D(32, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    # Block #4: third CONV => RELU => CONV => RELU => POOL
    # layer set
    model.add(Conv2D(64, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(Conv2D(64, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    # Block #4: third CONV => RELU => CONV => RELU => POOL
    # layer set
    model.add(Conv2D(64, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(Conv2D(64, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    # Block #4: third CONV => RELU => CONV => RELU => POOL
    # layer set
    model.add(Conv2D(64, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(Conv2D(64, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    # Block #5: first set of FC => RELU layers
    model.add(Flatten())
    model.add(Dense(64, kernel_initializer="he_normal"))
    model.add(ReLU())
    model.add(BatchNormalization())
    model.add(Dropout(0.5))

    # Block #7: sigmoid classifier
    model.add(Dense(1, kernel_initializer="he_normal"))
    model.add(Activation("sigmoid"))

    return model, IMG_SIZE