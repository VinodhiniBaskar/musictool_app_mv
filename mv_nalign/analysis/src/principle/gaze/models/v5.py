from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import ReLU
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import Dense
from tensorflow.keras.regularizers import l2


###############################################
from tensorflow.keras import Input, Model         #! 
from tensorflow.keras.layers import concatenate   #!

IMG_SIZE = 224
L2 = l2(0.001)
input_shape1 = (IMG_SIZE, IMG_SIZE, 3)
input_shape2 = (6,)


def create_model_first(input_shape):
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

    # Block #4: third CONV => RELU => CONV => RELU => POOL
    # layer set
    model.add(Conv2D(128, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(Conv2D(128, (3, 3), kernel_initializer="he_normal", padding="same"))
    model.add(ReLU())
    model.add(BatchNormalization(axis=chan_dim))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    
    model.add(Flatten())

    return model


def create_merged_model(model, input_shape):
    inputs = Input(shape=input_shape)
    merged_layers = concatenate([model.output,inputs])
    
    x = Dense(64, kernel_initializer="he_normal", activation='relu')(merged_layers)
    x = BatchNormalization()(x)
    x = Dropout(0.5)(x)
    x = Dense(1, kernel_initializer="he_normal", activation='sigmoid')(x)
    
    merged_model = Model([model.input, inputs], [x])
    #merge d_model.compile(loss = 'binary_crossentropy', optimizer = 'adam', metrics = ['accuracy'])
    return merged_model
    
    
def create_model():
    model1 = create_model_first(input_shape1)
    return create_merged_model(model1, input_shape2), IMG_SIZE
