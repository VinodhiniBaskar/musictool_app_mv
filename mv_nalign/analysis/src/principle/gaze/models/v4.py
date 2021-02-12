from keras.applications.resnet_v2 import ResNet50V2

IMG_SIZE = 224


def create_model():
    model = ResNet50V2(input_shape=(IMG_SIZE, IMG_SIZE, 3), weights=None, classes=1, classifier_activation='sigmoid')
    return model, IMG_SIZE