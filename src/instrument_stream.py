import time
import random


class InstrumentStream():
	"""
	Instrument price stream generator.

	It randomly generates events in the form:
	{ "id": 1, "price": 12.34, "timestamp": 12345678 }

	Attributes:
		prices: current prices of the generated instruments
		instrument_num: number of generated instruments
		epoch_between_events: elapsed seconds between events to conform the desired time throughput rate
		time_between_epochs: seconds between events to conform to the desired event throughput rate
	"""

	PRICE_INIT = 10
	PRICE_MIN = 1
	GAUSSIAN_UPDATE = (0, 1)

	def __init__(self, instrument_num=10, events_per_min=5000, elapsed_min_per_min=50):
		"""
		Initialize a InstrumentStream that will generate:
			a number of events per real world minute
		
		While simulating
			a number of elapsed minutes per real world minute
		"""

		self.prices = [self.PRICE_INIT] * instrument_num
		self.instrument_num = instrument_num
		self.time_between_events = 60.0 / events_per_min
		self.epoch_between_events = elapsed_min_per_min * self.time_between_events

	def __new_sample__(self):
		"""Randomly samples a new ticker and its next price update from a Gaussian distribution"""

		ticker = random.randint(0, self.instrument_num-1)
		change = random.normalvariate(*self.GAUSSIAN_UPDATE)
		return ticker, change

	def __update_price__(self, ticker, change):
		"""Updates the price of a ticker by an absolute amount"""

		self.prices[ticker] = max(self.PRICE_MIN, self.prices[ticker] + change)
		return self.prices[ticker]

	def read(self):
		"""Generates events respecting the desired throughput rate"""

		epoch = int(time.time())
		while True:
			epoch += self.epoch_between_events
			sample = self.__new_sample__()
			price = self.__update_price__(*sample)

			yield dict(id=sample[0], price=price, timestamp=epoch)
			time.sleep(self.time_between_events)


if __name__ == '__main__':
	stream = InstrumentStream()
	for event in stream.read():
		# SimilarityStock(event)
		print(event)

# time python3 api/instrument_stream.py | head -n 5000 > test.txt
# should be around ~1m runtime with events separated by 3000 seconds (~50m)
