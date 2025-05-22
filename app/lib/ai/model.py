
from app.lib.calc.vehicles import VEHICLES
from app.lib.calc.depotpark import DEPOTPARK
import app.lib.calc.calc_itself as calc_itself
import sqlite3
import json
from random import SystemRandom
import numpy
from keras.api.utils import Sequence
from keras import layers, models, Input
import matplotlib.pyplot as plt
from keras.api.optimizers import Adam
from keras.api.models import load_model
import seaborn as sns
from app import settings
from app.lib.calc.depotpark import Depot
from app.lib.calc.vehicles import Vehicle


class BatchGenerator(Sequence):
    def __init__(self, batch_size=1500, batches_qty=30, **kwargs):
        super().__init__(**kwargs)
        self.batch_size = batch_size
        self.batches_qty = batches_qty
        self.rnd = SystemRandom()

    def __len__(self):
        # Return number of batches.
        return self.batches_qty

    def __getitem__(self, idx):
        self._gen_batch(DEPOTPARK.park, DEPOTPARK.park, VEHICLES, self.batch_size)
        batch_x, batch_y = self._gen_batch(DEPOTPARK.park, DEPOTPARK.park, VEHICLES, self.batch_size)
        return numpy.array(batch_x), numpy.array(batch_y)

    def get_one_case(self):
        """Makes a batch with one sample inside for testing purposes
        :return: Single sample batch
        """
        batch_x, batch_y = self._gen_batch(DEPOTPARK.park, DEPOTPARK.park, VEHICLES, 1)
        return numpy.array(batch_x), numpy.array(batch_y)

    def _gen_batch(self, _from_list, _to_list, _vehicles, batch_size):
        """Generates mini-batches for model training randomizing the lists of the available Depots and Vehicles
        :param _from_list: Starting Depots list
        :param _to_list: Ending Depots list
        :param _vehicles: Vehicles list
        :param batch_size: Number of samples in a batch
        :return: x and y corresponding values in a lists
        """
        x_arr = []
        y_arr = []
        for i in range(batch_size):
            depot_from = self.rnd.choice(_from_list)
            depot_to = self.rnd.choice(_to_list)
            vehicle = self.rnd.choice(_vehicles)
            x, y = self._evaluate(depot_from, depot_to, vehicle)
            x_arr.append(x)
            y_arr.append(y)
            # self._store(depot_from.id, depot_to.id, vehicle.id, y)
        return x_arr, y_arr

    def _evaluate(self, _from: Depot, _to: Depot, _vehicle: Vehicle):
        """Evaluates route cost to produce x, y pair where x is an input to the model and
        y is a desired output out of the model
        :param _from: Starting Depot
        :param _to: Ending Depot
        :param _vehicle: Chosen Vehicle
        :return: x is a list of 371 elements, y is a desired float
        """
        x = PricePredictor.vectorize_input(_from.id, _to.id, _vehicle.id)
        request = self.craft_request(_from, _to, _vehicle)
        calculation = calc_itself.calculate_route_reduced(request)
        y = calculation['price'] * calculation['currency_rate']
        return x, y

    @staticmethod
    def craft_request(_from: Depot, _to: Depot, _veh: Vehicle):
        """Internal method to exploit internal analitycal calculator needed to generate bulk of data.
        It makes a json-like request (dict) that calculator can process to avoid refactoring calculator itself.
        param _from: Starting Depot obj
        param _to: Ending Depot obj
        param _veh: Chosen Vehicle obj
        :return: crafted dict that is ready to be processed by the calc
        """

        return {'intent':   'acquire',
                'from':     {'name_short': None,
                             'name_long': None,
                             'lat': _from.lat,
                             'lng': _from.lng,
                             'countrycode': _from.state.iso_code},
                'to':       {'name_short': None,
                             'name_long': None,
                             'lat': _to.lat,
                             'lng': _to.lng,
                             'countrycode':  _to.state.iso_code},
                'transport_id': _veh.id,
                'phone_number': None,
                'locale': None,
                'url': None,
                'ip': None}

    @staticmethod
    def __extract_sqlite_data():
        """This method should be used in future for fine tune on real calculation data"""
        cx = sqlite3.connect("/home/oliver/Projects/TF_Experiments/data/QueryLog.sqlite")
        cu = cx.cursor()
        counter = 0
        for row in cu.execute('select "query" from "queries"'):
            try:
                obj = json.loads(row[0])
                # calc_itself.calculate_route()
                counter += 1
            except json.decoder.JSONDecodeError:
                pass
        print(f'Total: {counter}')


class PricePredictor:

    def __init__(self, model=settings.PRICE_PREDICTOR_MODEL):
        self.model_loc = model
        self.model = load_model(self.model_loc)

    def __create(self):
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

    def __test(self):
        weights, _ = self.model.layers[0].get_weights()
        plt.figure(figsize=(10, 6))
        sns.heatmap(weights, cmap='coolwarm')
        plt.title("Weights heatmap")
        plt.xlabel("Output Neurons")
        plt.ylabel("Input Features")
        plt.show()

        for i in range(100):
            x_analytical, y_analytical = BatchGenerator().get_one_case()
            y_predicted = self.model.predict(x_analytical)
            print(y_predicted)
            print(y_analytical)

    @classmethod
    def vectorize_input(cls, _from, _to, _veh):
        """
        The model accepting linear array of 0.0 or 1.0. For example 00001000..00010000..0100
        First 182 values represents field of possible starting Depots
        Second 182 values is for ending Depots
        And then there is 7 values to choose a vehicle
        Total 182+182+7=371. That is the input of the model. The values are binary: 0 or 1
        :param _from: ID of Starting Depot
        :param _to: ID of Ending Depot
        :param _veh: ID of Vehicle
        :return: model_input_vector
        """
        array = []
        for i in range(0, 182):
            if _from == i:
                array.append(1.0)
            else:
                array.append(0.0)
        for i in range(0, 182):
            if _to == i:
                array.append(1.0)
            else:
                array.append(0.0)
        for i in range(0, 7):
            if _veh == i:
                array.append(1.0)
            else:
                array.append(0.0)
        return array

    def train(self, x_batch, y_batch):
        history = self.model.fit(BatchGenerator(), epochs=40)

        def plot(_history, title='Loss func'):
            plt.plot(_history.history['loss'], label='Loss')
            plt.title(title)
            plt.xlabel('Epoch')
            plt.ylabel('Loss (MSE)')
            plt.legend()
            plt.grid(True)
            plt.show()

        # plot(history)
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


def test():
    rnd = SystemRandom()
    dpt_from = rnd.choice(DEPOTPARK.park)
    dpt_to = rnd.choice(DEPOTPARK.park)
    vehicle = rnd.choice(VEHICLES)
    value = ML_MODEL.predict(dpt_from, dpt_to, vehicle)
    if isinstance(value, float):
        print(f'TEST OK Value is float and equal {value}')
    else:
        print(f'TEST FAIL Value is not float: {str(type(value))} = {str(value)}')
