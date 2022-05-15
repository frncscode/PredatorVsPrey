import numpy as np
import math
import random

def sigmoid(x):
    y = 1 / (1 + math.e ** -x)
    return y

def softmax(x):
    e = np.exp(x)
    return e / e.sum()

# Base Class
class Layer:
    def __init__(self):
        self.input = None
        self.output = None
    
    # computes the output Y of layer for a given X
    def forward_propagation(self, input):
        raise NotImplementedError

# Fully Connected layer
class FCLayer(Layer):
    # input_size = number of input neurones
    # output_size = number of output neurones
    def __init__(self, input_size, output_size):
        self.weights = np.random.rand(input_size, output_size) - 0.5
        self.bias = np.random.rand(1, output_size) - 0.5

    # returns output for a given input
    def forward_propagation(self, input_data):
        self.input = input_data
        self.output = np.dot(self.input, self.weights) + self.bias
        return self.output

# Activation Layer
class ActivationLayer(Layer):
    def __init__(self, activation):
        self.activation = activation
    
    # returns the activated input
    def forward_propagation(self, input_data):
        self.input = input_data
        self.output = self.activation(self.input)
        return self.output

class Network:
    def __init__(self):
        self.layers = []
        self.loss = None
        self.loss_prime = None
    
    # add layer to network
    def add(self, layer):
        self.layers.append(layer)

    # predict output for given input
    def predict(self, input_data):
        # sample dimensions

        output = input_data
        for layer in self.layers:
            output = layer.forward_propagation(output)
        return output
        