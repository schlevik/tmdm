from typing import List, Iterable
from dynaconf import settings
from fastcache import clru_cache
from spacy.tokens import Doc, Token
from loguru import logger

from tmdm.model.extensions import Annotation, extend

force = settings['force']


# ATTRIBUTES
@extend(Token, type='property', create_attribute=True, default=[])
def corefs(self: Token):
    """

    Args:
        self:
        annotation_type:

    Returns:

    """
    logger.debug(f"Retrieving coref annotations for token '{self}'")
    logger.debug(f"Result is: '{self._._corefs}'")
    return [
        Coreference.make(i, self.doc) for i in self._._corefs
    ]


def set_corefs(self, corefs):
    # TODO if re-setting the NES, need to unload the previous token annotations
    # normalise and align, should be either in a pipeline element or a util function or something like that
    if self._._corefs:
        logger.error("Cannot re-set tokens (yet)!")
        raise NotImplementedError("Cannot re-set tokens (yet)!")
    for idx, (start, end, label) in enumerate(corefs):
        logger.trace(corefs)
        for token in self._.char_span_relaxed(start, end):
            annotations = token._._corefs
            if idx not in annotations:
                annotations.append(idx)

    self._._corefs = corefs


@extend(Doc, 'property', create_attribute=True, default=[], setter=set_corefs)
def corefs(self: Doc) -> List['Coreference']:
    """

    Args:
        self:
        tags:
        ner_generator:

    Returns:

    """
    tags = self._._corefs
    corefs = []
    if not tags:
        logger.warning("No Coreferences extracted for this document (yet?).")

    for i, _ in enumerate(tags):
        corefs.append(Coreference.make(self.doc, i))
    return corefs


def _l2c(label: str) -> int:
    return int(label.split("-")[-1])


@clru_cache(maxsize=100000)
def _cluster(doc: Doc, cluster_id: int) -> Iterable['Coreference']:
    return (Coreference.make(doc, i) for i, (_, _, label) in enumerate(doc._._corefs) if _l2c(label) == cluster_id)


class Coreference(Annotation):
    cluster_id: int
    cluster: List['Coreference']

    def coreferent(self, other: 'Coreference') -> bool:
        return isinstance(other, Coreference) and self.doc == other.doc and self.cluster_id == other.cluster_id

    @property
    def cluster(self) -> Iterable['Coreference']:
        return _cluster(self.doc, self.cluster_id)

    @classmethod
    def make(cls, doc: Doc, idx, *args, **kwargs) -> 'Coreference':
        start, end, label = doc._._corefs[idx]
        coref = super().make(doc, idx, start, end, label)
        coref.cluster_id = _l2c(label)
        return coref