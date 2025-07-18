
from typing import List
from app.lib.ai.model import PricePredictor, FinetuneBatch
from app.lib.utils.QueryLogger import QueryLogger


class Trainer:

    def __init__(self, model: PricePredictor, database: QueryLogger):
        self.model = model
        self.database = database

    def _gather_samples(self) -> List[FinetuneBatch.Sample]:
        samples = []
        with self.database as db:
            for row in db.select_samples():
                samples.append(
                    FinetuneBatch.Sample(
                        depot_from_id=row[0],
                        depot_to_id=row[1],
                        vehicle_id=row[2],
                        desired_value=row[3],
                    )
                )
        return samples

    def train(self):

        batch = FinetuneBatch.make_finetune_batch(self._gather_samples())

        loss = self.model.train(batch)[0]

        logger.debug(f'Loss function: {loss}')

        # TODO Save model weights

    def add_sample(self, calculation_id: str, desired_dependent_price: float) -> None:
        """
        Method parses calculation_dto to make desired value that is passed down
        to the database for further processing.
        :param calculation_id: 40 char sha1 hex id
        :param desired_dependent_price: float, User input. Sometimes it indicates
        price per tonn, sometimes per order. The purpose of this method is to
        determine which one case is applicable now and convert desired price to
        per km as the underhood model was trained on. Also, this price can be in
        different currencies.
        :return:
        """
        with self.database as db:
            dto = db.get_calculation_dto(calculation_id)

            # To make our task a little easier we compare dependent desired
            # price with that in available calculation_dto one
            # So we calculate ratio, then taking per_km_price and
            # changing it on the same amount
            current_dependent_price = dto.price_unstr
            ratio = desired_dependent_price / current_dependent_price
            current_price_per_km = dto.real_price
            desired_price_per_km = current_price_per_km * ratio

            db.sample_upsert(calculation_id, desired_price_per_km)
