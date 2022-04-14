from baselines.topic_model import TopicModel
from baselines.cetopic import CETopic
import pandas as pd
from simcse import SimCSE
import gensim.corpora as corpora
from gensim.models.coherencemodel import CoherenceModel


class CETopicTM(TopicModel):
    def __init__(self, dataset, topic_model, k, dim_size, word_select_method, embedding, seed):
        super().__init__(dataset, topic_model, k)
        print(f'Initialize CETopicTM with k={k}, embedding={embedding}')
        self.dim_size = dim_size
        self.word_select_method = word_select_method
        self.embedding = embedding
        self.seed = seed
        
        # make sentences and token_lists
        token_lists = self.dataset.get_corpus()
        self.sentences = [' '.join(text_list) for text_list in token_lists]

        # use SimCSE
        self.simCSE_embeddings = None
        if 'simcse' in embedding.lower():
            simCSE_model = SimCSE(embedding)
            self.simCSE_embeddings = simCSE_model.encode(self.sentences)
            self.simCSE_embeddings = self.simCSE_embeddings.cpu().detach().numpy()
            print(self.simCSE_embeddings.shape)
            self.model = CETopic(nr_topics=k, 
                                 dim_size=self.dim_size, 
                                 word_select_method=self.word_select_method, 
                                 seed=self.seed)
        else:
            self.model = CETopic(embedding_model=embedding, 
                                 nr_topics=k, 
                                 dim_size=self.dim_size, 
                                 word_select_method=self.word_select_method, 
                                 seed=self.seed)        
    
    
    def train(self):
        if self.simCSE_embeddings is not None:
            self.topics = self.model.fit_transform(self.sentences, self.simCSE_embeddings)
        else:
            self.topics = self.model.fit_transform(self.sentences)
    
    
    def evaluate(self):
        td_score = self._calculate_topic_diversity()
        cv_score, npmi_score = self._calculate_cv_npmi(self.sentences, self.topics)
        
        return td_score, cv_score, npmi_score
    
    
    def get_topics(self):
        return self.model.get_topics()
    
    
    def _calculate_topic_diversity(self):
        topic_keywords = self.model.get_topics()

        bertopic_topics = []
        for k,v in topic_keywords.items():
            temp = []
            for tup in v:
                temp.append(tup[0])
            bertopic_topics.append(temp)  

        unique_words = set()
        for topic in bertopic_topics:
            unique_words = unique_words.union(set(topic[:10]))
        td = len(unique_words) / (10 * len(bertopic_topics))

        return td


    def _calculate_cv_npmi(self, docs, topics): 

        doc = pd.DataFrame({"Document": docs,
                        "ID": range(len(docs)),
                        "Topic": topics})
        documents_per_topic = doc.groupby(['Topic'], as_index=False).agg({'Document': ' '.join})
        cleaned_docs = self.model._preprocess_text(documents_per_topic.Document.values)

        vectorizer = self.model.vectorizer_model
        analyzer = vectorizer.build_analyzer()

        words = vectorizer.get_feature_names()
        tokens = [analyzer(doc) for doc in cleaned_docs]
        dictionary = corpora.Dictionary(tokens)
        corpus = [dictionary.doc2bow(token) for token in tokens]
        topic_words = [[words for words, _ in self.model.get_topic(topic)] 
                    for topic in range(len(set(topics))-1)]

        coherence_model = CoherenceModel(topics=topic_words, 
                                      texts=tokens, 
                                      corpus=corpus,
                                      dictionary=dictionary, 
                                      coherence='c_v')
        cv_coherence = coherence_model.get_coherence()

        coherence_model_npmi = CoherenceModel(topics=topic_words, 
                                      texts=tokens, 
                                      corpus=corpus,
                                      dictionary=dictionary, 
                                      coherence='c_npmi')
        npmi_coherence = coherence_model_npmi.get_coherence()

        return cv_coherence, npmi_coherence 
    