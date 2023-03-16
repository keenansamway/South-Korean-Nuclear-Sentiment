# SK-Nuclear-Sentiment
 A project looking into South Korean sentiment on nuclear issues


### Goals
- Look at how South Koreans think about a few nuclear related issues: Nuclear Power, Nuclear Weapons Proliferation
- Most previous reserach has focused on using news media articles and/or twitter data
- This project aims to bring YouTube, a very popular social media service, into the mix

### Previous Work
- Sentiment analysis of nuclear energy-related articles and their comments on a portal site in Rep. of Korea in 2010–2019 (https://linkinghub.elsevier.com/retrieve/pii/S1738573320306057)

- A Prototype System for Monitoring Emotion and Sentiment Trends Towards Nuclear Energy on Twitter Using Deep Learning (https://link.springer.com/10.1007/978-3-030-91669-5_36)


### Questions, Obstacles and Ideas
- Explore models trained on Korean language data
    - Sentiment analysis
    - Text embedding

- How to encode transcript documents into a vector representation?
    - TF-IDF (Term Frequency-Inverse Document Frequency)
    - Use Sentence-Transformers to encode 512 token chuncks, then average all of them (or the top-k) to obtain a final encoding for the document
    - Use a text summarization model to summarize the document and then encode that

- Can views and number of comments be taken into account?
    - Weigh all videos the same regardless of popularity
    - Weigh videos with more popularity higher than those with less

- Can we detect differences in the sentiment of the video and sentiment of the comments?
    - Positive vs negative sentiment of the video and comparison with comments
    - Embedding and clustering of comments

- Is there a way to detect whether comments are relevant to the topics in the video?
    - Potentially discard comments which are not related to the video topic
