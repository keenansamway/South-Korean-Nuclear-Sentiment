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


### Key Terms
- 핵무기 - nuclear weapon
- 전술핵무기 - tactical nuclear weapon
- 핵확산 - nuclear proliferation
- 핵개발 - nuclear development
- 핵무장 - nuclear armament
- 핵무장론 - theory of nuclear armament
- 독자 핵무장 - independent nuclear armament
- 한국 핵무장 - korean nuclear armament
- 핵우산 - nuclear umbrella
- 핵 잠재력 - nuclear potential
- 핵 보유, 핵 보유국, 핵무기 보유국 - a nuclear power, a nuclear weapons state
- 핵확산방지조약, NPT - Nuclear Non-Proliferation Treaty
- NPT 탈퇴 - withdrawal from NPT

- 한미동맹 - US-ROK Alliance
- 한미상호방위조약 - US-ROK Mutual Defense Treaty

- 한국, 대한민국 - South Korea, Republic of Korea
- 미국 - USA

- 더불어민주당 - Democratic Party (Liberal)
- 국민의힘 - People Power Party (Conservative)


## TODO

- Look further into topics 0, 1, 2 for further analysis
- Topic model the video titles and/or descriptions
- Compare video topics with their comment topics
