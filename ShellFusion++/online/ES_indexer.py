import conf
import sys
sys.path.append(conf.offline)
from ES import indexDocs

if __name__ == "__main__":
    import time
    start = time.time()
    _lucene_docs_txt = conf.exp_models_dir + '/lucene_docs.txt'
    indexDocs(_lucene_docs_txt)

    print(f"ES index time:{time.time() - start}") #41s