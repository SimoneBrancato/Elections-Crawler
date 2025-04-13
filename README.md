<div align="center">
  <img src="https://github.com/user-attachments/assets/3a5cbc1c-68bc-4eed-afec-4ba10484c801" alt="ChatGPT Image" width="400"/>
</div>


## What is Elections-Crawler?
Elections-Crawler is a web crawling system developed as part of the broader thesis project Sentivoter – A Framework for Cross-Media Data Collection and Processing Applied to the U.S. Elections.
The crawler is specifically designed to automatically collect data from the official Facebook pages of Kamala Harris and Donald Trump.

The system leverages Docker for deployment and uses the Selenium web automation framework to navigate and extract content from Facebook while ensuring flexibility and modularity. 
The collected data is then fed into a larger Spark-based processing architecture for cross-media analysis, which also includes data from other platforms such as YouTube for sentiment and emotion analysis.

All collected data is stored in a relational database including a historical indexing mechanism that allows for multiple scraping iterations of the same content to overcome the temporal limitations imposed by the platform. 
This feature is designed to track the evolution of user interactions over time.


## Prerequisites

- **Docker/Docker Compose:** Ensure you have a fully functional [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installation on your local computer.
- **Environment Variables:** Create a `.env` file in the main directory with structure:
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

## Project Architecture

The project consists of a network of containers that collaborate by reading from and writing to a single MySQL container that serves as the database. The Harris Retriever and Trump Retriever containers are responsible for retrieving the timestamp of the last tracked post from the database, then accessing the respective Facebook pages of the two candidates and storing the links of new posts based on that timestamp.

After that, the various analyzer containers will fetch the post links from the database according to a parameterized delay. This delay is used to scrape posts from the last 24 hours, and then again after 5, 10, and 15 days to track the evolution of interactions over time.

For each post, the number of retrieved comments is limited to avoid platform blocks, while still accessing the top comments by popularity.

All containers are launched once per day by restarting containers, which allow the project to run as a daemon. Once collected, the data can be exported and analyzed within dedicated data pipelines.



<div align="center">
  <img src="https://github.com/user-attachments/assets/9c7d976f-b5e7-4669-b1c4-dd4d70518a42" alt="FC"/>
</div>





## Contacts
- **E-Mail:** simonebrancato18@gmail.com
- **LinkedIn:** [Simone Brancato](https://www.linkedin.com/in/simonebrancato18/)
- **GitHub:** [Simone Brancato](https://github.com/SimoneBrancato)



