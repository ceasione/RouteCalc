from typing import List, Tuple
from app.lib.calc.loadables.vehicles import VEHICLES
from app.lib.calc.loadables.depotpark import DEPOTPARK
from random import SystemRandom
import numpy
from keras.api.utils import PyDataset
from keras import layers, models, Input
from keras.api.optimizers import Adam
from keras.api.models import load_model
from app import settings
from app.lib.calc.loadables.depotpark import Depot
from app.lib.calc.loadables.vehicles import Vehicle
from dataclasses import dataclass
# import matplotlib.pyplot as plt
# import seaborn as sns


class FinetuneBatch(PyDataset):
    def __init__(self, x_list, y_list, **kwargs):
        super().__init__(**kwargs)
        if len(x_list) != len(y_list):
            raise ValueError("x_set and y_set must have same length")
        self.x = x_list
        self.y = y_list
        self.batch_size = len(x_list)

    def __len__(self):
        # Return number of batches.
        # Little dataset -> one batch
        # Later we'll see
        return 1

    def __getitem__(self, idx):
        return numpy.array(self.x), numpy.array(self.y)

    @dataclass
    class Sample:
        depot_from_id: int
        depot_to_id: int
        vehicle_id: int
        desired_value: float

    @classmethod
    def make_finetune_batch(cls, samples: List[Sample]) -> 'FinetuneBatch':
        list_of_model_inputs = []
        list_of_model_outputs = []
        for sample in samples:
            input_vector = PricePredictor.vectorize_input(
                sample.depot_from_id,
                sample.depot_to_id,
                sample.vehicle_id
            )
            output_value = sample.desired_value

            list_of_model_inputs.append(input_vector)
            list_of_model_outputs.append(output_value)
        return cls(list_of_model_inputs, list_of_model_outputs)


class PricePredictor:

    def __init__(self, model=settings.AI_MODEL_LOC):
        self.model_loc = model
        self.model = load_model(self.model_loc)

    def _create(self):
        """
        This is a place the model were born at
        :return:
        """
        self.model = models.Sequential()
        self.model.add(Input(shape=(371,)))
        self.model.add(layers.Dense(8, activation='leaky_relu'))
        self.model.add(layers.Dense(4, activation='leaky_relu'))
        self.model.add(layers.Dense(2, activation='leaky_relu'))
        self.model.add(layers.Dense(1, activation='linear'))

        optimizer = Adam(learning_rate=0.01)
        self.model.compile(optimizer=optimizer, loss='mae')

    # def __test(self):
    #     weights, _ = self.model.layers[0].get_weights()
    #     plt.figure(figsize=(10, 6))
    #     sns.heatmap(weights, cmap='coolwarm')
    #     plt.title("Weights heatmap")
    #     plt.xlabel("Output Neurons")
    #     plt.ylabel("Input Features")
    #     plt.show()
    #
    #     for i in range(100):
    #         x_analytical, y_analytical = BatchGenerator().get_one_case()
    #         y_predicted = self.model.predict(x_analytical)
    #         print(y_predicted)
    #         print(y_analytical)

    @staticmethod
    def vectorize_input(place_from_id: int, place_to_id: int, vehicle_id: int) -> List[float]:
        """
        The model accepting linear array of 0.0 or 1.0. For example 00001000..00010000..0100
        First 182 values represents field of possible starting Depots
        Second 182 values is for ending Depots
        And then there is 7 values to choose a vehicle
        Total 182+182+7=371. That is the input of the model. The values are binary: 0 or 1
        :param place_from_id: ID of Starting Depot
        :param place_to_id: ID of Ending Depot
        :param vehicle_id: ID of Vehicle
        :return: model_input_vector
        """
        array = []
        for i in range(0, 182):
            if place_from_id == i:
                array.append(1.0)
            else:
                array.append(0.0)
        for i in range(0, 182):
            if place_to_id == i:
                array.append(1.0)
            else:
                array.append(0.0)
        for i in range(0, 7):
            if vehicle_id == i:
                array.append(1.0)
            else:
                array.append(0.0)
        return array

    def train(self, dataset: PyDataset):
        history = self.model.fit(dataset, epochs=1, verbose=1)

        # def plot(_history, title='Loss func'):
        #     plt.plot(_history.history['loss'], label='Loss')
        #     plt.title(title)
        #     plt.xlabel('Epoch')
        #     plt.ylabel('Loss (MSE)')
        #     plt.legend()
        #     plt.grid(True)
        #     plt.show()
        #
        # plot(history)

        return history.history['loss']

    def save_model(self):
        self.model.save(self.model_loc)

    def predict(self, dpt_from_id: int, dpt_to_id: int, vehicle_id: int) -> float:
        """
        Makes predictions on route cost.
        param dpt_from: Starting Depot id
        param dpt_to: Ending Depot id
        param vehicle: Chosen Vehicle id
        :return: Approx price of 1 kilometer of the route
        """
        x = numpy.array([self.vectorize_input(dpt_from_id, dpt_to_id, vehicle_id)])
        y = self.model.predict(x)
        return float(y[0][0])


ML_MODEL = PricePredictor()
