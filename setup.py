from setuptools import setup

setup(name='topicx',
      version='0.1',
      description='Topic modeling library',
      url='https://github.com/Buckeyes2019/topicx',
      author='Topicx Paper Authors',
      author_email='flyingcircus@example.com',
      license='MIT',
      install_requires=['octis', 'umap-learn', 'hdbscan', 'simcse==0.4', 'plotly', 'flair', 'gensim'],
      zip_safe=False)
