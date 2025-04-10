# Intersmartgroup API

## Overview

The **Intersmartgroup API** is designed to work seamlessly with the [Intersmartgroup website](https://intersmartgroup.com/). It includes two primary features:
1. **Freight cost calculator** – Calculates the cost of transportation based on origin, destination, route, and traffic load.
2. **Real-time tracking** – Allows for tracking of active freight shipments.

This API is written in **Python** using **Flask**, and integrates with several external services:
- **Google Places API** – For location data.
- **Google Geocoding API** – For converting addresses into geographic coordinates.
- **Google Matrix API** – For route and distance calculations.
- **SMS API** – For sending SMS notifications.

The backend is also powered by **Python Telegram Bot**, allowing fleet managers to interact with the system via Telegram. The API is deployed on a **uWSGI** production server with robust security measures in place.

The project leverages **machine learning** for cost calculation through the selection of a route congestion coefficient. This model is trained on a few parameters, and while it's not advanced, it provides meaningful results for the freight calculations.

The API is currently in **production** and provides tangible business value by optimizing transportation costs for daily operations.

## Features

- **Freight Cost Calculator**:
    - The user inputs origin and destination, and the API calculates the best route using public roads, estimates distance, and selects a congestion coefficient for competitive pricing.
    - Returns a set of parameters for visualization on the website's frontend.
    - Users can place an order directly via the website or through a Telegram bot.

- **Real-Time Freight Tracking**:
    - Allows fleet managers to track active shipments.
    - Management of fleet data (CRUD operations) is possible through the Telegram bot.

## Architecture

- **Python & Flask**: The backend of the API is written in Python, using the Flask framework.
- **Database**: **SQLite** is used for logging requests and caching to minimize costs associated with Google API calls.
- **Caching**: Caching is implemented to store frequently used data, reducing the number of calls to external APIs.
- **Machine Learning**: A lightweight ML model is used to determine route congestion coefficients for cost optimization.
- **SMS & Telegram Bot Integration**: For notifications and fleet management via the Python Telegram Bot framework.

## Usage

To interact with the API, follow the steps below:

1. **API Endpoints**:
   - `POST /calculate`: Send origin and destination to calculate the freight cost.
   - `GET /track`: Retrieve real-time tracking information of active shipments.

2. **Telegram Bot**:
   - Fleet managers and admins can use the bot for interacting with the active fleet and accessing freight data.

3. **Google API Integration**:
   - Google Places, Geocoding, and Matrix APIs are used to optimize route calculations and location data.

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
   python app.py

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