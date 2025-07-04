# Intersmartgroup API

## Overview

The **Intersmartgroup API** is designed to work seamlessly with the [intersmartgroup.com website](https://intersmartgroup.com/). It includes two primary features:
1. **Route planner** - Plan a route vehicle should pass to complete an order. Taking in account our depotpark limited capabilities. (Can be tweaked on your depotpark size)
2. **Freight cost calculator** – Calculates the cost of transportation based on origin, destination, route, and traffic load.

This API is written in **Python** using **Flask**, and integrates with several external services:
- **Google Places API** – For location data.
- **Google Geocoding API** – For converting addresses into geographic coordinates.
- **Google Matrix API** – For route and distance calculations.
- **SMS API** – For sending SMS notifications.

The adminpage is powered by **Python Telegram Bot**, allowing fleet managers to interact with the system via Telegram Bot. 

The API is deployed on a **uWSGI** production server with robust security measures in place.

The project leverages **machine learning** for cost calculation through the selection of a depot-to-depot route coefficient. This model consists of a few parameters (~3000), and while it's not advanced, it provides meaningful results for the given goal.

The API is currently in **production** and provides tangible value for business by making transportation costs instant and clear.

## Features

- **Freight Cost Calculator**:
    - The user inputs origin and destination, and the API calculates the best route using public roads, estimates distance, and selects a depot-to-depot route coefficient for competitive pricing.
    - Returns a set of parameters for visualization on the website's frontend.
    - Notices fleet managers of every calculation (to finetune the model) and provide credentials for marketing team to reach the client. 
    - Client can place an order directly via the website. Fleet managers will be extra notified.

## Architecture

- **Python & Flask**: The backend of the API is written in Python, using the Flask framework.
- **Database**: **SQLite** is used for logging requests and caching to minimize costs associated with Google API calls.
- **Caching**: Caching is implemented to store frequently used data, reducing the number of calls to external APIs.
- **Machine Learning**: A lightweight ML model is used to determine route congestion coefficients for cost optimization.
- **SMS & Telegram Bot Integration**: For notifications and fleet management via the Python Telegram Bot framework.

## Usage

To interact with the API, follow the steps below:
**API Endpoints**:
   - `POST /calculate`: Send origin and destination to calculate the freight cost.
     To make a calculationn do a POST rquest to that endpoint with certain json
     ```
        {'intent': 'acquire',

         'from': {
             'name_short': 'any_string',
             'name_long': 'any_string',
             'lat': 49.227717,
             'lng': 31.852233,
             'countrycode': 'UA'},

         'to': {
             'name_short': 'any_string',
             'name_long': 'any_string',
             'lat': 50.5089112,
             'lng': 26.2566443,
             'countrycode': 'UA'},

         'transport_id': 1,  # One of the -> GET /get-available-vehicles
         'phone_number': '',
         'locale': 'uk_UA',
         'url': 'referrer'}
        ```
   - `GET /get-available-vehicles`: Retrieve list of available transport types.
   

## Installation

To set up the project locally, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/intersmart-group-api.git
   
2. Navigate to the project folder:

   ```bash
   cd intersmart-group-api

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
4. Run the application:
   ```bash
   python3 -m app.main

## Contributing

We welcome suggestions and contributions to improve the project. If you'd like to contribute, please follow these steps:

- Fork the repository.

- Create a feature branch (git checkout -b feature-name).

- Commit your changes (git commit -am 'Add new feature').

- Push to the branch (git push origin feature-name).

- Create a new Pull Request.

If you find bugs or have suggestions, please open an Issue.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

If you have any questions, feel free to reach out via email ceasione@gmail.com

2025