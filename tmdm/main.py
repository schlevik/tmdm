import spacy
from typing import Tuple, Any, Union, Callable, Optional

from loguru import logger
from scispacy.custom_tokenizer import combined_rule_tokenizer

from tmdm.classes import Provider, Cached
from tmdm.pipe.ne import NEPipe
from tmdm.pipe.tokenizer import IDTokenizer
from tmdm.util import failsafe_combined_rule_sentence_segmenter


def change_getter(nlp, getter=Callable[[Any, ], Tuple[str, str]]):
    nlp.tokenizer.getter = getter


def default_getter(d):
    return d['id'], d['abstract']


def tmdm_pipeline(getter: Optional[Callable[[Any, ], Tuple[str, str]]] = None, model='en'):
    nlp = spacy.load(model)
    logger.info("Pipeline has no getter configured. Document IDs will be generated automatically. "
                "Pass data as plain strings.")
    nlp.tokenizer = IDTokenizer(nlp.Defaults.create_tokenizer(nlp), getter)
    return nlp


def tmdm_scientific_pipeline(getter: Callable[[Any, ], Tuple[str, str]] = default_getter, model="en_core_sci_lg"):
    nlp = spacy.load(model, disable=['ner', 'parser'])
    nlp.tokenizer = IDTokenizer(combined_rule_tokenizer(nlp), getter=getter)
    nlp.add_pipe(failsafe_combined_rule_sentence_segmenter)
    return nlp


def add_ner(nlp, provider: Union[Provider, str], schema="list_of_tuples_bio_stacked"):
    if isinstance(provider, str):
        provider = Cached(path=provider, getter=lambda d: d['abstract'], schema=schema)
    nlp.add_pipe(NEPipe(nlp.vocab, provider))