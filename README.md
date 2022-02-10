## Stock-Similarity 
Simple collaborative recommendation for product similarity estimation.


### Setup

**Prerequisites**

Built with Python 3.9, but should work with other > Python 3.6 versions.
```
pip install virtualenv
virtualenv <name>
source <name>/bin/activate
pip install -r requirements.txt
```

Please run below in the same order

**DB Setup**

DB: `Recommendations`, Table (Initial): `UserInstruments`, Other tables: `UserItemSimilarity`, `ItemSimilarity`
```
python model_db.py
```
Tech used: SQLAlchemy (SQLite)

**Data Generation**

While running below, wait for 5 mins, as we need price history of 5 mins.
```
python tests/generate_data.py
```
Uses the provided `instrument_stream.py` to generate input data to DB & flat-file 

Output: `data/` dir

**Training**

```
python src/train_similarity_stocks.py
```
Both approaches are implemented:
* Item-based collaborative filtering: Model is based on item cosine distances
* User-based collaborative filtering: Model is based on item euclidean distance

Reason: Collaborative Filtering with cosine similarity can be in memory, and is fast in making simple arithmetic operations.
To avoid the downside of having a sparse matrix, we can select on the required columns.
Clustering (eg. KNN) may not be scalable for 100M users hitting 10 times daily.

Tech used: sklearn, pandas etc.

### API
```
python app.py
```
Will generate an IP which you can pass to the endpoints below.

**Endpoints**:

`/add/request` : To manually add new user or instrument entry (instead of through `instrument_stream`)

`/instruments/<int:instrid>` : Retrieves the last 5minutes of price history with minutely resolution

`/instruments/similar/<string:userid>` : Returns the 10 user-recommended stocks, given a `userid`

`/instruments/similar/<int:instrid>` : Returns the 10 most similar stocks, given an `instrument-id`

```
http://<ip>:5000//instruments/similar/<instrid>
http://<ip>:5000//instruments/similar/<user_id>
```
or using `curl` ...

Example:

1. Add new user:
```
curl http://<ip>:5000/add/request --request POST --header "Content-Type: application/json" --data '{"userid": "ABC", "price": "10.273", "timestamp": "1629061628", "instrid": 4}'
```
Output:
```
{
  "resp": {
    "instrid": 4,
    "price": "10.273",
    "timestamp": "1629061628",
    "userid": "ABC"
  }
}
```
2. Retrain model (To get scores for new user or instrument):
```
python train_similarity_stocks.py
```

3. Price history from last 5 minutes for an instrument:
```
curl http://<ip>:5000/instruments/4
```
Output:
```
{
  "2021-08-16 23:32:00": {
    "instrid": 4,
    "price_close": 30.720722747311438,
    "price_high": 30.95552569216846,
    "price_low": 28.130188131072263,
    "price_open": 28.130188131072263
  },
  "2021-08-16 23:33:00": {
    "instrid": 4,
    "price_close": 32.625519076821135,
    "price_high": 33.75415083166951,
    "price_low": 30.651110731017894,
    "price_open": 30.651110731017894
  },
  "2021-08-16 23:34:00": {
    "instrid": 4,
    "price_close": 35.080199941493284,
    "price_high": 35.518648971117905,
    "price_low": 29.955314672154707,
    "price_open": 29.955314672154707
  },
  "2021-08-16 23:35:00": {
    "instrid": 4,
    "price_close": 36.45158436457821,
    "price_high": 37.229010165569015,
    "price_low": 34.065298396096324,
    "price_open": 34.60302781982425
  },
  "2021-08-16 23:36:00": {
    "instrid": 4,
    "price_close": 41.49435434250442,
    "price_high": 41.49435434250442,
    "price_low": 34.69979107925532,
    "price_open": 34.69979107925532
  }
}
```

4. Item-based similarity
```
curl http://<ip>:5000/instruments/similar/4
```
Output:
```
{
  "predicted_items": [
    "0",
    "5",
    "6",
    "2",
    "7",
  ]
}
```


5. User-based similarity
```
curl http://<ip>:5000/instruments/similar/ABC
```
Output:
```
{
  "predicted_items": [
    "4",
    "5",
    "1",
    "7",
    "3",
    "6",
    "8",
    "2",
    "9",
    "0"
  ]
}
```


Tech used: Flask

### Follow-up Questions
1. How would you change the system to support 50k instruments each streaming one or more quotes every second?
   - Streaming service/Message Broker like Kafka (on-prem) or Kinesis (AWS/Cloud), along with an online Feature store/Cache like Redis, to deliver predictions at low latency
   
2. Which changes are needed, so your code could support 100M daily active users hitting each endpoint 10 times/day?
   Tech: Load Balancer & HTTP Servers, eg. Nginx
   We can create multiple instances of the prediction service, use a load balancer to split traffic, and send the traffic to the appropriate copy of your service. 
   In practice, there are two common methods:
      - Deploying containerized applications/services on auto-scaling clusters such as Kubernetes (on-prem) or ECS (AWS/Cloud)
      - Or use a serverless option like AWS Lambda. (Fully-managed, but meant for lightweight serving only, not heavy transformations)
   
3. What would you put in place to make the sure the system, and the model are working as expected?
   - Test cases: Cross-Validation, A/B Testing, Canary deployment, Verifying labelling, regular training & evaluation sets, Hyper-parameter tuning
   - Versioning (Source code & Data), eg. DVC
   - Data Quality checks, eg. Great Expectations
   - Logging & Monitoring, eg. CloudWatch (AWS), Graphana, Prometheus, ELK
   - Deployment, pipelines & Infra: IaC (eg. Terraform), CI/CD (eg. GitHub workflows), Containers (eg. Docker)
   
4. How would you evaluate and improve the Similarity model?
   - Coverage: percent of items in the training data, the model is able to recommend on a test set.
   - Personalization: to assess if a model recommends many of the same items to different users. It is the dissimilarity (1- cosine similarity) between user’s lists of recommendations. A high personalization score would indicate the user’s recommendations are different, meaning the model is offering a personalized experience to each user.
   - Intra-list similarity: average cosine similarity of all items in a list of recommendations. This calculation uses features of the recommended items to calculate the similarity. 
   - For improving: 
     - Remove popular items from the training data, Reduce noise
     - Scale item ratings by the user’s value, such as average transaction value. This can help a model learn to recommend items that lead to loyal or high-value customers.
