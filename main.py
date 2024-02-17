import requests
from datetime import datetime, timedelta
from twilio.rest import Client

# You can change the stock and company name to anything that you're particularly interested in:
STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"
STOCK_API_KEY = "Enter your stock price API key (see www.alphavantage.co)"
NEWS_API_KEY = "Enter your news data API key from your news account (see news.api.org)"
TWILIO_ACC_SID = "Enter your twilio account SID"
TWILIO_AUTH_TOKEN = "Enter your twilio authentification token"
TWILIO_PHONE_NO = "Enter your twilio account's virtual phone number"
VERIFIED_PHONE_NO = "Enter your personal phone number that is verified by your twilio account"

stock_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "SOFI",
    "outputsize": "compact",
    "apikey": STOCK_API_KEY
}
news_parameters = {
    "q": COMPANY_NAME,
    "sortBy": "publishedAt",
    "language": "en",
    "apiKey": NEWS_API_KEY
}


# Finds the closing stock data for the latest day and the day before:
stock_response = requests.get(url="https://www.alphavantage.co/query", params=stock_parameters)
stock_response.raise_for_status()
stock_data = stock_response.json()["Time Series (Daily)"]

# To account for timezone differences of Singapore (my location) vs the East
# as well as since current day stock data would not have been updated yet:
days_before_present = 0
today_data = None

# If there is no stock data for today's date, this while loop continues until it can find the latest data for the stock:
while today_data is None:
    today_date = str(datetime.now() - timedelta(days_before_present)).split(" ")[0]
    yesterday_date = str(datetime.now() - timedelta(days_before_present + 1)).split(" ")[0]
    today_data = stock_data.get(today_date)
    yesterday_data = stock_data.get(yesterday_date)

    days_before_present += 1


today_closing = float(today_data["4. close"])
yesterday_closing = float(yesterday_data["4. close"])
percentage_change = (today_closing - yesterday_closing) / yesterday_closing * 100

# Only looks for news articles regarding the company if there is a significant percentage change:
if percentage_change < -5 or percentage_change > 5:
    news_response = requests.get(url="https://newsapi.org/v2/everything", params=news_parameters)
    news_response.raise_for_status()
    news_data = news_response.json()["articles"]

    # To account for if there are less than 3 articles returned regarding the company so that no index error occurs:
    if len(news_data) < 3:
        news_dict = {article["title"]: article["description"] for article in news_data}

    else:
        news_dict = {article["title"]: article["description"] for article in news_data[:3]}

    if percentage_change < 0:
        up_or_down = "🔻"
    else:
        up_or_down = "🔺"

    change = round(abs(percentage_change), 2)

    # Send separate messages for each news article if percentage increase/decrease was 5% or greater
    twilio_client = Client(TWILIO_ACC_SID, TWILIO_AUTH_TOKEN)

    for news_title in news_dict:
        message = twilio_client.messages \
            .create(
                body=f"{STOCK}: {up_or_down}{change}%\n"
                     f"Headline: {news_title}\n"
                     f"Brief: {news_dict.get(news_title)}",
                from_=TWILIO_PHONE_NO,
                to=VERIFIED_PHONE_NO
            )
