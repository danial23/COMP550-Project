import pathlib
import json
import logging
# import json_stream


class Corpus:
    def __init__(self, list_of_filenames, dataset_path : pathlib.Path) -> None:
        self._dataset_path = dataset_path
        self._list_of_filenames = list_of_filenames
    
    def __iter__(self):
        return CorpusRevisionIterator(self)


class CorpusRevisionIterator:
    """
    Returns an iterator which iterates over all revisions in the corpus efficiently.
    """
    def __init__(self, corpus : Corpus):
        self._corpus = corpus
        self._generator = self.revisions()

    def __next__(self):
        return next(self._generator)
    
    def revisions(self):
        """
        Generator returning (doc_index, revision) tuples on the fly.
        """
        for doc_index, filename in enumerate(self._corpus._list_of_filenames):
            target_file_path = self._corpus._dataset_path.joinpath(filename)
            with open(target_file_path, "r") as fp:
                stats = target_file_path.stat()
                if stats.st_size < 1.0E9: # file size less than 1 GB
                    page = json.load(fp)
                else:
                    logging.warning(f"Skipped {filename} - too large to load into memory.")
                    continue
                    # page = json_stream.load(fp)
                for rev in page["revisions"]:
                    yield doc_index, rev


class CorpusPageIterator:
    def __init__(self, corpus : Corpus):
        self._corpus = corpus
        self._generator = self.pages()

    def __next__(self):
        return next(self._generator)
    
    def pages(self):
        """
        Generator to load pages on the fly.
        """
        for filename in self._corpus._list_of_filenames:
            with open(self._corpus._dataset_path.joinpath(filename), "r") as fp:
                page = json.load(fp)
                yield page
