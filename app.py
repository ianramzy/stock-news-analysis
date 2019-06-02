from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)


@app.route('/')
def student():
    return render_template("input.html")


@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        result = request.form
        ticker = result.get('Name')
        print(ticker)
        analysis = str(ave_sentiment(result.get('Name')))
        print(analysis)
        links = get_articles(ticker)
        links = links[:3]
        links = [links[0][1], links[1][1], links[2][1]]
        otherHalf = 100 - int(analysis)
        return render_template("output.html", analysis=analysis, ticker=ticker, links=links, sentance=sentance, otherHalf=otherHalf)


if __name__ == '__main__':
    app.run(debug=True)


def get_articles(ticker):
    articles = []
    source = "https://www.nasdaq.com/symbol/" + ticker + "/news-headlines"
    for i in range(1):
        if i == 0:
            news = source
        else:
            news = source + "?page=" + str(i)
        url = requests.get(news)
        data = url.text
        soup = BeautifulSoup(data, 'html.parser')
        for link in soup.find_all('a'):
            current_link = link.get('href')
            if 'article' == current_link[23:30] and current_link not in articles:
                publish_date = str(link.parent.parent.find('small'))[31:41]
                publish_date = publish_date.strip(" ").split("/")
                if publish_date != ['']:
                    # date_num = int(publish_date[2]) * 10000 + int(publish_date[0]) * 100 + int(publish_date[1])
                    articles.append([1, current_link])
    print(str(len(articles)) + " articles found")
    return articles


def scrape_news_text(source):
    data = requests.get(source).text
    news_soup = BeautifulSoup(data, 'html.parser')
    paragraphs = [par.text for par in news_soup.find_all('p')]
    paragraphs = paragraphs[2:-6]
    news_text = '\n'.join(paragraphs)
    write_to_file(news_text)
    return news_text


def azure_sentiment(text):
    documents = {'documents': [
        {'id': '1', 'text': text}
    ]}
    azure_key = 'd38ac31a3b2c4e0982d3bc540251a162'
    azure_endpoint = 'https://canadacentral.api.cognitive.microsoft.com/text/analytics/v2.0'
    assert azure_key
    sentiment_azure = azure_endpoint + '/sentiment'

    headers = {"Ocp-Apim-Subscription-Key": azure_key}
    response = requests.post(sentiment_azure, headers=headers, json=documents)
    sentiments = response.json()
    sentiments = sentiments['documents'][0]['score']
    return sentiments


def replace(text):
    list_of_words = text.split(" ")
    bad_list = ["bear", "bearish", "underperform", "underperforming", "sell", "selling", "sold", "decrease",
                "decreasing", "falling", "fall", "fell", "down", "lose", "lost", "losses", "losing", "downturn",
                "short", "shorting", "downside", "risky", "decline", "declining", "fear", "fears", "sell-off"]
    good_list = ["bull", "bullish", "overperform", "overperforming", "buy", "buying", "bought", "increase",
                 "increasing", "rising", "rise", "rised", "up", "gain", "gains", "gained", "profit", "profited","profitable", "profiting", "upturn", "upside"]
    list_of_words = ["bad" if word in bad_list else word for word in list_of_words]
    list_of_words = ["good" if word in good_list else word for word in list_of_words]
    list_of_words = " ".join(list_of_words)
    return list_of_words


def freq_chart(list_of_words):
    list_of_words = map(lambda x: x.lower(), list_of_words)
    list_of_words = sorted(list_of_words)
    list_of_words = remove_common_words(list_of_words)
    global sentance
    sentance = ' '.join(list_of_words)
    print(sentance)


def remove_common_words(listOfWords):
    commonWords = ["a", "about", "all", "also", "it", "the", "to", "of", "and", "in", "is", "for", "with", "that",
                   "has", "its", "as", "on", "this", "at", "will", "are", ".", "be", "an", "by", ",", "'", "from",
                   "have", "or", "than", "stock", "stocks", "said", "he", "not", "can", "i", "they", "when", "some",
                   "their", "we", "it's", "more", "was", "but", "one", "just", "so", "which", "these", "if", "they're",
                   "their", "could", "think", "that's", "there", "you", "get", "market", "very", "been", "year",
                   "other", "his", "right", "even", "any", "**", "percent", "company", "after", "shares", "next",
                   "investor's", "investors", "last", "trade", "price", "business", "zacks", "company's", "here", "inc",
                   "per", "click", "new", "--", "our", "fool", "each", "", "nasdaq", "(", ")", "were", "current",
                   "those", "-", "believe", "financial", "share", "percent.", "*", "", "motley", "over", "nasdaq:",
                   "percent,", "index", "would", "total", "them", "much", "my", "still", "into", "had", "since", "500", "s&p", "friday", "shares", "nasdaq", "trading", "day", "time", "to", "like","pct"]
    cleanList = []
    for word in listOfWords:
        if word not in commonWords:
            cleanList.append(word)
    return cleanList


def ave_sentiment(ticker):
    articles = get_articles(ticker)
    full_text = ""
    sentiment = 0
    for i in range(len(articles)):
        full_text = full_text + replace(scrape_news_text(articles[i][1]))
        print("Downloaded [" + str(i + 1) + "/" + str(len(articles)) + "]")
    write_to_file(full_text)
    freq_chart(full_text.split())

    breaks = int(len(full_text) / 5000)

    for i in range(breaks - 1):
        a = i * 5000
        b = (i + 1) * 5000
        sentiment = sentiment + azure_sentiment(full_text[a:b])
        print(sentiment / (i + 1))
    sentiment = sentiment + azure_sentiment(full_text[breaks * 5000:])
    sentiment = sentiment / breaks
    sentiment = sentiment * 100
    sentiment = int(round(sentiment))
    return sentiment


def write_to_file(text):
    file = open("testfile.txt", "w")
    file.write(text)
    file.close()


# while True:
#     user_input = input("Stock to perform sentiment analysis:")
#     print("Average sentiment: " + str(ave_sentiment(user_input)))

