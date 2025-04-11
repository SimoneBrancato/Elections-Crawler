# What is Elections-Crawler?
Elections-Crawler is a web crawling system developed as part of the broader thesis project Sentivoter – A Framework for Cross-Media Data Collection and Processing Applied to the U.S. Elections.
The crawler is specifically designed to automatically collect data from the official Facebook pages of Kamala Harris and Donald Trump.

The system leverages Docker for deployment and uses the Selenium web automation framework to navigate and extract content from Facebook while ensuring flexibility and modularity. 
The collected data is then fed into a larger Spark-based processing architecture for cross-media analysis, which also includes data from other platforms such as YouTube for sentiment and emotion analysis.

All collected data is stored in a relational database including a historical indexing mechanism that allows for multiple scraping iterations of the same content to overcome the temporal limitations imposed by the platform. 
This feature is designed to track the evolution of user interactions over time.

### Requirements
Create a `.env` in the main directory with:
```env
FB_EMAIL_RETRIEVER=<your-email>
FB_PASSWORD_RETRIEVER=<your-password>

FB_EMAIL_HARRIS_1=<your-email>
FB_PASSWORD_HARRIS_1=<your-password>

FB_EMAIL_HARRIS_2=<your-email>
FB_PASSWORD_HARRIS_2=<your-password>

FB_EMAIL_TRUMP_1=<your-email>
FB_PASSWORD_TRUMP_1=<your-password>

FB_EMAIL_TRUMP_2=<your-email>
FB_PASSWORD_TRUMP_2=<your-password>
```

