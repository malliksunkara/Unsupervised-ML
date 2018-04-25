import elasticsearch
from elasticsearch.helpers import streaming_bulk
from sklearn.datasets import fetch_20newsgroups
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
import numpy as np
from HW2 import DATA_DIR

n_features = 1000
n_top_words = 20
dataset = fetch_20newsgroups(data_home=DATA_DIR,
                             remove=('headers', 'footers', 'quotes'))
data_samples = dataset.data
tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2,
                                max_features=n_features,
                                stop_words='english')
tf = tf_vectorizer.fit_transform(data_samples).todense()


def print_top_words(model, feature_names, n_top_words):
    for topic_idx, topic in enumerate(model.components_):
        message = "Topic #%d: " % topic_idx
        index = topic.argsort()[:-n_top_words - 1:-1]
        message += " ".join([feature_names[i] + " " + str(topic[i] / topic.sum()) for i in index])
        print(message)


# for k in [10, 20, 50]:
#     nmf = NMF(n_components=k, random_state=1,
#               alpha=.1, l1_ratio=.5).fit(tf)
#     lda = LatentDirichletAllocation(n_components=k, learning_method='online')
#     lda.fit(tf)
#     print("\nTopics in NMF model:")
#     tf_feature_names = tf_vectorizer.get_feature_names()
#     # print_top_words(nmf, tf_feature_names, n_top_words)
#     print("\nTopics in LDA model:")
#     print_top_words(lda, tf_feature_names, n_top_words)


def reindex():
    import elasticsearch
    es = elasticsearch.Elasticsearch(http_auth=('elastic', 'elastic'))
    from elasticsearch.helpers import streaming_bulk
    actions = []
    lda = LatentDirichletAllocation(n_components=20, learning_method='online')
    lda.fit(tf)
    topic_actions = []
    for topic_idx, topic in enumerate(lda.components_):
        message = "Topic #%d: " % topic_idx
        index = topic.argsort()[:-10 - 1:-1]
        message += " ".join([tf_vectorizer.get_feature_names()[i] + " " + str(topic[i] / topic.sum()) for i in index])
        topic_actions.append({
            '_op_type': 'index',
            '_index': 'topic',
            '_type': 'topic',
            '_id': topic_idx,
            'topic_id': topic_idx,
            'top_words': message,
        })

    for (res, j) in streaming_bulk(client=es, raise_on_exception=True, raise_on_error=True,
                                   actions=topic_actions):
        print (res, j)

    # for i, data in enumerate(data_samples):
    #     x = lda.transform(tf[i])[0]
    #     ind = np.argpartition(x, -5)[-5:]
    #     prob = x[ind]
    #     mesg = ''
    #     for j in range(5):
    #         mesg += "{0}:{1}, ".format(str(ind[j]), str(prob[j]))
    #     structured_json_body = {
    #         '_op_type': 'update',
    #         '_index': 'news-group',
    #         '_type': 'document',
    #         '_id': dataset.filenames[i].split('/')[-1],
    #         'doc': {'doc_topics': mesg, }
    #     }
    #     actions.append(structured_json_body)
    #
    # for (res, j) in streaming_bulk(client=es, raise_on_exception=True, raise_on_error=True,
    #                                actions=actions):
    #     print (res, j)


reindex()